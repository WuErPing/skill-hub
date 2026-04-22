"""Skills state tracking — listing, status computation, install/uninstall."""

import hashlib
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from skill_hub.web.repos import REPOS_DIR, load_repos_config, load_skill_mapping, repo_dir

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

CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"


@dataclass
class SkillEntry:
    name: str
    repo_name: str
    repo_url: str
    path: Path  # absolute path in the cloned repo
    in_claude: bool   # installed to ~/.claude/skills
    in_agents: bool   # installed to ~/.agents/skills
    md5_source: str   # MD5 of source skill in repo
    md5_claude: str   # MD5 of installed version in ~/.claude/skills (empty if not installed)
    md5_agents: str   # MD5 of installed version in ~/.agents/skills (empty if not installed)
    link_claude: bool = False  # True if installed via symlink
    link_agents: bool = False  # True if installed via symlink

    @property
    def claude_matches_source(self) -> bool:
        return self.in_claude and self.md5_claude == self.md5_source

    @property
    def agents_matches_source(self) -> bool:
        return self.in_agents and self.md5_agents == self.md5_source

    @property
    def status(self) -> str:
        c_ok = self.claude_matches_source
        a_ok = self.agents_matches_source
        if c_ok and a_ok:
            return "installed"
        elif self.in_claude or self.in_agents:
            return "outdated"
        return "not_installed"


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
    """Scan repos via skill mappings and both install directories, return all skills with status."""
    repos = load_repos_config()

    claude_skills = _scan_install_dir(CLAUDE_SKILLS)
    agents_skills = _scan_install_dir(AGENTS_SKILLS)

    # Gather all skill paths first
    entries: list[tuple[Repo, str, Path]] = []
    for repo in repos:
        mapping = load_skill_mapping(repo)
        if not mapping:
            continue
        repo_root = repo_dir(repo)
        for skill_name, rel_path in mapping.items():
            skill_path = repo_root / rel_path
            if skill_path.exists():
                entries.append((repo, skill_name, skill_path))

    # Parallel MD5 for source skills (the dominant cost)
    with ThreadPoolExecutor(max_workers=8) as pool:
        md5_futures = {
            (repo.name, skill_name): pool.submit(_md5_of_dir, skill_path)
            for repo, skill_name, skill_path in entries
        }

    skills: list[SkillEntry] = []
    for repo, skill_name, skill_path in entries:
        in_c = skill_name in claude_skills
        in_a = skill_name in agents_skills
        source_md5 = md5_futures[(repo.name, skill_name)].result()

        c_md5, c_link = claude_skills.get(skill_name, ("", False))
        a_md5, a_link = agents_skills.get(skill_name, ("", False))

        skills.append(SkillEntry(
            name=skill_name,
            repo_name=repo.name,
            repo_url=repo.url,
            path=skill_path,
            in_claude=in_c,
            in_agents=in_a,
            md5_source=source_md5,
            md5_claude=c_md5,
            md5_agents=a_md5,
            link_claude=c_link,
            link_agents=a_link,
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
    """Install skill from source_path to both ~/.claude/skills/ and ~/.agents/skills/."""
    try:
        CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
        AGENTS_SKILLS.mkdir(parents=True, exist_ok=True)

        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        _remove_destination(dest_a)
        _remove_destination(dest_b)

        if method == "symlink":
            ok_a = _try_symlink(source_path, dest_a)
            ok_b = _try_symlink(source_path, dest_b)
            if ok_a and ok_b:
                return True, f"Installed {name} to both directories (symlink)"
            # Fallback to copy if symlink failed on either side
            _remove_destination(dest_a)
            _remove_destination(dest_b)
            shutil.copytree(source_path, dest_a)
            shutil.copytree(source_path, dest_b)
            return True, f"Installed {name} to both directories (copy fallback — symlink not supported)"

        shutil.copytree(source_path, dest_a)
        shutil.copytree(source_path, dest_b)
        return True, f"Installed {name} to both directories"
    except Exception as e:
        return False, str(e)


def install_to_one(name: str, source_path: Path, target: str, method: str = "copy") -> tuple[bool, str]:
    """Install skill from source_path to a single directory ('claude' or 'agents')."""
    try:
        if target == "claude":
            dest_dir = CLAUDE_SKILLS
        elif target == "agents":
            dest_dir = AGENTS_SKILLS
        else:
            return False, f"Unknown target: {target}"

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        _remove_destination(dest)

        if method == "symlink":
            if _try_symlink(source_path, dest):
                return True, f"Installed {name} to {target} (symlink)"
            _remove_destination(dest)
            shutil.copytree(source_path, dest)
            return True, f"Installed {name} to {target} (copy fallback — symlink not supported)"

        shutil.copytree(source_path, dest)
        return True, f"Installed {name} to {target}"
    except Exception as e:
        return False, str(e)


# Load persisted cache on module import
_load_md5_cache()


def uninstall_skill(name: str) -> tuple[bool, str]:
    """Remove skill from both ~/.claude/skills/ and ~/.agents/skills/."""
    try:
        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        removed: list[str] = []
        if dest_a.exists() or dest_a.is_symlink():
            _remove_destination(dest_a)
            removed.append("~/.claude/skills")
        if dest_b.exists() or dest_b.is_symlink():
            _remove_destination(dest_b)
            removed.append("~/.agents/skills")

        if not removed:
            return True, f"{name} was not installed"
        return True, f"Uninstalled {name} from {', '.join(removed)}"
    except Exception as e:
        return False, str(e)
