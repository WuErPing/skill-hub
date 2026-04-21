"""repos.yaml management and git operations for ~/.skills_repo."""

import re
import shutil
import subprocess
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from skill_hub.utils.path_utils import expand_home

SKILLS_REPO_ROOT = expand_home("~/.skills_repo")
REPOS_YAML = SKILLS_REPO_ROOT / "repos.yaml"
REPOS_DIR = SKILLS_REPO_ROOT / "repos"
MAPPINGS_DIR = SKILLS_REPO_ROOT / "mappings"


@dataclass
class Repo:
    url: str
    branch: str = "main"
    name: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            m = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", self.url)
            if m:
                self.name = f"{m.group(1)}/{m.group(2)}"
            else:
                parts = self.url.rstrip("/").split("/")
                if len(parts) >= 2:
                    self.name = f"{parts[-2]}/{parts[-1]}"
                else:
                    self.name = parts[-1] if parts else self.url

    @property
    def dir_name(self) -> str:
        """Safe directory name for this repo (replacing / with __)."""
        return self.name.replace("/", "__") if self.name else ""

    @property
    def is_local(self) -> bool:
        """Return True if this repo points to a local filesystem path."""
        url = self.url.strip()
        if url.startswith(("~", "/", ".")):
            return True
        if url.startswith(("http://", "https://", "git@")):
            return False
        # Fallback: if it resolves to an existing path, treat as local
        return expand_home(url).exists()


DEFAULT_REPOS = [
    Repo(url="https://github.com/anthropics/skills", branch="main"),
]


def repo_dir(repo: Repo) -> Path:
    """Return the repo directory. For local repos, returns the local path directly."""
    if repo.is_local:
        return expand_home(repo.url).resolve()
    return REPOS_DIR / repo.dir_name


def mapping_path(repo: Repo) -> Path:
    """Return the YAML mapping file path for a repo."""
    return MAPPINGS_DIR / f"{repo.dir_name}.yaml"


def load_repos_config() -> list[Repo]:
    """Load repos from repos.yaml. Seeds with DEFAULT_REPOS if file doesn't exist."""
    if not REPOS_YAML.exists():
        save_repos_config(DEFAULT_REPOS)
        return DEFAULT_REPOS
    with open(REPOS_YAML) as f:
        data = yaml.safe_load(f) or {}
    return [Repo(**r) for r in data.get("repos", [])]


def save_repos_config(repos: list[Repo]) -> None:
    """Save repos list to repos.yaml."""
    SKILLS_REPO_ROOT.mkdir(parents=True, exist_ok=True)
    data = {"repos": [{"url": r.url, "branch": r.branch} for r in repos]}
    with open(REPOS_YAML, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_skill_mapping(repo: Repo) -> dict[str, str]:
    """Load skill-name -> relative-path mapping from YAML. Returns empty dict if not exists."""
    mp = mapping_path(repo)
    if not mp.exists():
        return {}
    with open(mp) as f:
        return yaml.safe_load(f) or {}


def save_skill_mapping(repo: Repo, mapping: dict[str, str]) -> None:
    """Save skill-name -> relative-path mapping to YAML."""
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    mp = mapping_path(repo)
    with open(mp, "w") as f:
        yaml.dump(mapping, f, default_flow_style=False, allow_unicode=True)


def _find_skills_in_repo(repo_dir: Path) -> dict[str, str]:
    """Scan a cloned repo for skill directories (contain SKILL.md) and return {name: relative_path}."""
    mapping = {}
    if not repo_dir.exists():
        return mapping

    for skill_md in repo_dir.rglob("SKILL.md"):
        # skill dir is the parent of SKILL.md
        skill_dir = skill_md.parent
        # skill name = directory name
        name = skill_dir.name
        # relative path from repo root
        rel = skill_dir.relative_to(repo_dir)
        mapping[name] = str(rel)

    return mapping


def sync_mapping(repo: Repo) -> tuple[bool, str]:
    """Clone or update a repo and rebuild its skill mapping. Returns (success, message)."""
    target = repo_dir(repo)

    if repo.is_local:
        if not target.exists():
            return False, f"Local path not found: {target}"
        action = "Scanned"
    else:
        if not target.exists():
            try:
                subprocess.run(
                    ["git", "clone", "--branch", repo.branch, repo.url, str(target)],
                    check=True, capture_output=True, text=True, timeout=120,
                )
            except subprocess.CalledProcessError as e:
                return False, f"Clone failed: {e.stderr}"
            except subprocess.TimeoutExpired:
                return False, "Clone timed out"
            action = "Cloned"
        else:
            action = "Synced"

    mapping = _find_skills_in_repo(target)
    save_skill_mapping(repo, mapping)
    count = len(mapping)
    return True, f"{action} {repo.url} — found {count} skill(s)"


def clone_or_pull(repo: Repo) -> tuple[bool, str]:
    """Clone repo if not present, otherwise fetch. Does NOT rebuild mapping."""
    target = repo_dir(repo)
    if repo.is_local:
        if not target.exists():
            return False, f"Local path not found: {target}"
        if (target / ".git").exists():
            try:
                subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=target, check=True, capture_output=True, text=True, timeout=30,
                )
                return True, "fetched"
            except subprocess.CalledProcessError as e:
                return False, f"Fetch failed: {e.stderr}"
        return True, "local directory"
    if not target.exists():
        try:
            subprocess.run(
                ["git", "clone", "--branch", repo.branch, repo.url, str(target)],
                check=True, capture_output=True, text=True, timeout=120,
            )
            return True, f"Cloned {repo.url}"
        except subprocess.CalledProcessError as e:
            return False, f"Clone failed: {e.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Clone timed out"
    else:
        try:
            subprocess.run(
                ["git", "fetch", "origin", repo.branch],
                cwd=target, check=True, capture_output=True, text=True, timeout=30,
            )
            return True, "fetched"
        except subprocess.CalledProcessError as e:
            return False, f"Fetch failed: {e.stderr}"


def pull_latest(repo: Repo) -> tuple[bool, str]:
    """Git pull the repo and rebuild skill mapping. Returns (success, message)."""
    target = repo_dir(repo)
    if not target.exists():
        if repo.is_local:
            return False, f"Local path not found: {target}"
        return sync_mapping(repo)
    if repo.is_local:
        if (target / ".git").exists():
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=target, check=True, capture_output=True, text=True, timeout=30,
                )
            except subprocess.CalledProcessError as e:
                return False, f"Pull failed: {e.stderr}"
    else:
        try:
            subprocess.run(
                ["git", "pull", "origin", repo.branch],
                cwd=target, check=True, capture_output=True, text=True, timeout=30,
            )
        except subprocess.CalledProcessError as e:
            return False, f"Pull failed: {e.stderr}"
    # Rebuild mapping after pull to catch added/removed skills
    mapping = _find_skills_in_repo(target)
    save_skill_mapping(repo, mapping)
    count = len(mapping)
    return True, f"Pulled {repo.url} — {count} skill(s) in mapping"


def delete_repo(repo: Repo) -> tuple[bool, str]:
    """Delete a repo's local directory, mapping, and remove from repos.yaml."""
    if not repo.is_local:
        target = repo_dir(repo)
        if target.exists():
            shutil.rmtree(target)
    mp = mapping_path(repo)
    if mp.exists():
        mp.unlink()
    repos = load_repos_config()
    repos = [r for r in repos if r.url != repo.url]
    save_repos_config(repos)
    return True, "Deleted"


def has_remote_updates(repo: Repo) -> bool:
    """Check if remote has commits ahead of local HEAD."""
    if repo.is_local:
        return False
    target = repo_dir(repo)
    if not target.exists():
        return False
    try:
        subprocess.run(
            ["git", "fetch", "origin", repo.branch],
            cwd=target, capture_output=True, timeout=15,
        )
        behind_result = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{repo.branch}", "--count"],
            cwd=target, capture_output=True, text=True,
        )
        count = int(behind_result.stdout.strip() or "0")
        return count > 0
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return False
