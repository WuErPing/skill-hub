"""Skills state tracking — listing, status computation, install/uninstall."""

import hashlib
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from skill_hub.web.repos import (
    REPOS_DIR,
    _find_skills_in_repo,
    load_repos_config,
    load_skill_mapping,
    mapping_path,
    repo_dir,
    save_skill_mapping,
    sync_mapping,
)
from skill_hub.web.config import get_install_dirs, InstallDir

MD5_CACHE_FILE = Path.home() / ".skills_repo" / "md5_cache.json"
_md5_cache: dict[str, tuple[float, str]] = {}


def _load_md5_cache() -> None:
    """Load persisted MD5 cache from disk."""
    global _md5_cache
    if MD5_CACHE_FILE.exists():
        try:
            with open(MD5_CACHE_FILE, encoding="utf-8") as f:
                raw = json.load(f)
                _md5_cache = {k: (v[0], v[1]) for k, v in raw.items()}
        except Exception:
            _md5_cache = {}


def _save_md5_cache() -> None:
    """Persist current MD5 cache to disk."""
    try:
        MD5_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MD5_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_md5_cache, f)
    except Exception:
        pass


def _dir_mtime(path: Path) -> float:
    """Return the latest mtime of any file under path (recursive)."""
    latest = 0.0
    try:
        latest = path.stat().st_mtime
        for root, _dirs, files in os.walk(path):
            for f in files:
                try:
                    mtime = os.stat(os.path.join(root, f)).st_mtime
                    if mtime > latest:
                        latest = mtime
                except OSError:
                    pass
    except OSError:
        pass
    return latest


@dataclass
class DirStatus:
    """Status of a skill in a single install directory."""
    installed: bool = False
    md5: str = ""
    is_symlink: bool = False


@dataclass
class SkillEntry:
    name: str
    repo_name: str
    repo_url: str
    path: Path  # absolute path in the cloned repo
    dir_status: dict[str, DirStatus] = field(default_factory=dict)
    conflict: bool = False
    source_md5: str = ""

    @property
    def status(self) -> str:
        """Overall status across all directories."""
        if not self.dir_status:
            return "not_installed"
        
        all_match = all(
            ds.installed and ds.md5 == self.source_md5
            for ds in self.dir_status.values()
        )
        any_installed = any(ds.installed for ds in self.dir_status.values())
        
        if all_match:
            return "installed"
        elif any_installed:
            return "outdated"
        return "not_installed"

    # Backward-compatible properties
    @property
    def in_claude(self) -> bool:
        return self.dir_status.get("claude", DirStatus()).installed

    @property
    def in_agents(self) -> bool:
        return self.dir_status.get("agents", DirStatus()).installed

    @property
    def claude_matches_source(self) -> bool:
        ds = self.dir_status.get("claude")
        return ds.installed and ds.md5 == self.source_md5 if ds else False

    @property
    def agents_matches_source(self) -> bool:
        ds = self.dir_status.get("agents")
        return ds.installed and ds.md5 == self.source_md5 if ds else False

    @property
    def link_claude(self) -> bool:
        return self.dir_status.get("claude", DirStatus()).is_symlink

    @property
    def link_agents(self) -> bool:
        return self.dir_status.get("agents", DirStatus()).is_symlink

    # Legacy md5 fields for API backward compatibility
    @property
    def md5_source(self) -> str:
        return self.source_md5

    @property
    def md5_claude(self) -> str:
        return self.dir_status.get("claude", DirStatus()).md5

    @property
    def md5_agents(self) -> str:
        return self.dir_status.get("agents", DirStatus()).md5


# Legacy constants for backward compatibility (used by tests)
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"


def _md5_of_dir(path: Path) -> str:
    """Return a combined MD5 of all files in a directory (sorted by path).
    Results are cached keyed by the directory's latest mtime.
    """
    global _md5_cache
    if not path.exists():
        return ""
    cache_key = str(path.resolve())
    mtime = _dir_mtime(path)
    cached = _md5_cache.get(cache_key)
    if cached and cached[0] >= mtime:
        return cached[1]
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.name.encode())
            h.update(f.read_bytes())
    result = h.hexdigest()
    _md5_cache[cache_key] = (mtime, result)
    _save_md5_cache()
    return result


def _is_skill_dir(path: Path) -> bool:
    """A skill directory is any subdirectory that is not hidden."""
    return path.is_dir() and not path.name.startswith(".")


def _scan_install_dir(install_dir: Path) -> dict[str, tuple[str, bool]]:
    """Scan an install directory and return {name: (md5, is_symlink)}."""
    result: dict[str, tuple[str, bool]] = {}
    if install_dir.exists():
        for entry in install_dir.iterdir():
            if _is_skill_dir(entry):
                result[entry.name] = (_md5_of_dir(entry), entry.is_symlink())
    return result


def list_skills() -> list[SkillEntry]:
    """Scan repos via skill mappings and all install directories, return all skills with status."""
    repos = load_repos_config()
    install_dirs = get_install_dirs()
    
    # Scan all install directories
    dir_scans: dict[str, dict[str, tuple[str, bool]]] = {}
    for install_dir in install_dirs:
        dir_scans[install_dir.label] = _scan_install_dir(install_dir.resolved_path)

    # Gather all skill paths first
    entries: list[tuple[Repo, str, Path]] = []
    for repo in repos:
        mapping = load_skill_mapping(repo)
        target = repo_dir(repo)

        if repo.is_local and target.exists():
            # Local repo: rebuild mapping if the directory has changed
            mp = mapping_path(repo)
            repo_mtime = _dir_mtime(target)
            if not mapping or not mp.exists() or repo_mtime > mp.stat().st_mtime:
                mapping, _conflicts = _find_skills_in_repo(target)
                if mapping:
                    save_skill_mapping(repo, mapping)

        if not mapping:
            if not repo.is_local:
                try:
                    ok, _msg = sync_mapping(repo)
                    if ok:
                        mapping = load_skill_mapping(repo)
                except Exception:
                    pass
            if not mapping:
                continue
        
        repo_root = repo_dir(repo)
        for skill_name, rel_path in mapping.items():
            skill_path = repo_root / rel_path
            if skill_path.exists():
                entries.append((repo, skill_name, skill_path))

    # Detect cross-repo name conflicts
    name_counts: dict[str, int] = {}
    for _repo, skill_name, _skill_path in entries:
        name_counts[skill_name] = name_counts.get(skill_name, 0) + 1

    # Parallel MD5 for source skills
    with ThreadPoolExecutor(max_workers=8) as pool:
        md5_futures = {
            (repo.name, skill_name): pool.submit(_md5_of_dir, skill_path)
            for repo, skill_name, skill_path in entries
        }

    skills: list[SkillEntry] = []
    known_names: set[str] = set()
    for repo, skill_name, skill_path in entries:
        known_names.add(skill_name)
        source_md5 = md5_futures[(repo.name, skill_name)].result()

        # Build dir_status for all install directories
        dir_status: dict[str, DirStatus] = {}
        for install_dir in install_dirs:
            scan = dir_scans.get(install_dir.label, {})
            md5, is_symlink = scan.get(skill_name, ("", False))
            dir_status[install_dir.label] = DirStatus(
                installed=skill_name in scan,
                md5=md5,
                is_symlink=is_symlink,
            )

        skills.append(SkillEntry(
            name=skill_name,
            repo_name=repo.name,
            repo_url=repo.url,
            path=skill_path,
            dir_status=dir_status,
            conflict=name_counts[skill_name] > 1,
            source_md5=source_md5,
        ))

    # Detect orphaned skills: installed but not in any repo mapping
    orphan_names: set[str] = set()
    for scan in dir_scans.values():
        for skill_name in scan:
            if skill_name not in known_names:
                orphan_names.add(skill_name)

    for skill_name in sorted(orphan_names):
        dir_status: dict[str, DirStatus] = {}
        first_path: Path | None = None
        for install_dir in install_dirs:
            scan = dir_scans.get(install_dir.label, {})
            md5, is_symlink = scan.get(skill_name, ("", False))
            installed = skill_name in scan
            dir_status[install_dir.label] = DirStatus(
                installed=installed,
                md5=md5,
                is_symlink=is_symlink,
            )
            if installed and first_path is None:
                first_path = install_dir.resolved_path / skill_name

        source_md5 = ""
        if first_path:
            source_md5 = _md5_of_dir(first_path)

        skills.append(SkillEntry(
            name=skill_name,
            repo_name="(local)",
            repo_url="",
            path=first_path or Path(skill_name),
            dir_status=dir_status,
            conflict=False,
            source_md5=source_md5,
        ))

    return sorted(skills, key=lambda s: (s.repo_name, s.name))


def _remove_destination(dest: Path) -> None:
    """Safely remove an existing installation destination."""
    if not dest.exists() and not dest.is_symlink():
        return
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)


def _try_symlink(source: Path, dest: Path) -> bool:
    """Try to create a directory symlink. Returns True on success."""
    try:
        os.symlink(source, dest, target_is_directory=True)
        return True
    except OSError:
        return False


def install_skill(name: str, source_path: Path, method: str = "copy") -> tuple[bool, str]:
    """Install skill from source_path to all configured install directories."""
    try:
        install_dirs = get_install_dirs()
        installed_to: list[str] = []
        
        for install_dir in install_dirs:
            dest_dir = install_dir.resolved_path
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / name
            
            _remove_destination(dest)
            
            if method == "symlink":
                if _try_symlink(source_path, dest):
                    installed_to.append(install_dir.label)
                    continue
                # Fallback to copy
                _remove_destination(dest)
            
            shutil.copytree(source_path, dest)
            installed_to.append(install_dir.label)
        
        if not installed_to:
            return False, "No install directories configured"
        
        if method == "symlink":
            # Check if any fallback occurred
            all_symlink = True
            for install_dir in install_dirs:
                dest_dir = install_dir.resolved_path
                dest = dest_dir / name
                if dest.exists() and not dest.is_symlink():
                    all_symlink = False
                    break
            if all_symlink:
                return True, f"Installed {name} to {', '.join(installed_to)} (symlink)"
            else:
                return True, f"Installed {name} to {', '.join(installed_to)} (copy fallback — symlink not supported)"
        return True, f"Installed {name} to {', '.join(installed_to)}"
    except Exception as e:
        return False, str(e)


def install_to_one(name: str, source_path: Path, target_label: str, method: str = "copy") -> tuple[bool, str]:
    """Install skill from source_path to a single directory by label."""
    try:
        install_dirs = get_install_dirs()
        target_dir = next((d for d in install_dirs if d.label == target_label), None)
        
        if target_dir is None:
            return False, f"Unknown target directory: {target_label}"
        
        dest_dir = target_dir.resolved_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        _remove_destination(dest)
        
        if method == "symlink":
            if _try_symlink(source_path, dest):
                return True, f"Installed {name} to {target_label} (symlink)"
            _remove_destination(dest)
            shutil.copytree(source_path, dest)
            return True, f"Installed {name} to {target_label} (copy fallback — symlink not supported)"
        
        shutil.copytree(source_path, dest)
        return True, f"Installed {name} to {target_label}"
    except Exception as e:
        return False, str(e)


def uninstall_skill(name: str) -> tuple[bool, str]:
    """Remove skill from all configured install directories."""
    try:
        install_dirs = get_install_dirs()
        removed: list[str] = []
        
        for install_dir in install_dirs:
            dest = install_dir.resolved_path / name
            if dest.exists() or dest.is_symlink():
                _remove_destination(dest)
                removed.append(install_dir.label)
        
        if not removed:
            return True, f"{name} was not installed"
        return True, f"Uninstalled {name} from {', '.join(removed)}"
    except Exception as e:
        return False, str(e)


def uninstall_from_one(name: str, target_label: str) -> tuple[bool, str]:
    """Remove skill from a single directory by label."""
    try:
        install_dirs = get_install_dirs()
        target_dir = next((d for d in install_dirs if d.label == target_label), None)
        
        if target_dir is None:
            return False, f"Unknown target directory: {target_label}"
        
        dest = target_dir.resolved_path / name
        if dest.exists() or dest.is_symlink():
            _remove_destination(dest)
            return True, f"Uninstalled {name} from {target_label}"
        return True, f"{name} was not installed in {target_label}"
    except Exception as e:
        return False, str(e)


def install_repo_skills(repo_name: str, method: str = "copy") -> tuple[bool, str]:
    """Install all skills from a repo to all configured directories."""
    skills = list_skills()
    repo_skills = [s for s in skills if s.repo_name == repo_name]
    if not repo_skills:
        return False, f"No skills found in repo '{repo_name}'"

    installed = 0
    errors: list[str] = []
    for s in repo_skills:
        if not s.path.exists():
            errors.append(f"{s.name}: source not found")
            continue
        ok, msg = install_skill(s.name, s.path, method=method)
        if ok:
            installed += 1
        else:
            errors.append(f"{s.name}: {msg}")

    total = len(repo_skills)
    if errors:
        return installed > 0, f"Installed {installed}/{total} skill(s); errors: {'; '.join(errors)}"
    return True, f"Installed {installed}/{total} skill(s) from {repo_name}"


def uninstall_repo_skills(repo_name: str) -> tuple[bool, str]:
    """Uninstall all skills from a repo from all configured directories."""
    skills = list_skills()
    repo_skills = [s for s in skills if s.repo_name == repo_name]
    if not repo_skills:
        return False, f"No skills found in repo '{repo_name}'"

    uninstalled = 0
    errors: list[str] = []
    for s in repo_skills:
        ok, msg = uninstall_skill(s.name)
        if ok:
            uninstalled += 1
        else:
            errors.append(f"{s.name}: {msg}")

    total = len(repo_skills)
    if errors:
        return uninstalled > 0, f"Uninstalled {uninstalled}/{total} skill(s); errors: {'; '.join(errors)}"
    return True, f"Uninstalled {uninstalled}/{total} skill(s) from {repo_name}"


# Load persisted cache on module import
_load_md5_cache()
