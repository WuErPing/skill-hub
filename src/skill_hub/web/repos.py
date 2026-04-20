"""repos.yaml management and git operations for ~/.skills_repo."""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from skill_hub.utils.path_utils import expand_home

SKILLS_REPO_ROOT = expand_home("~/.skills_repo")
REPOS_YAML = SKILLS_REPO_ROOT / "repos.yaml"
SKILLS_DIR = SKILLS_REPO_ROOT / "skills"


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
                self.name = self.url.rstrip("/").split("/")[-2] + "/" + self.url.rstrip("/").split("/")[-1]


def load_repos_config() -> list[Repo]:
    """Load repos from repos.yaml. Returns empty list if file doesn't exist."""
    import yaml
    if not REPOS_YAML.exists():
        return []
    with open(REPOS_YAML) as f:
        data = yaml.safe_load(f) or {}
    return [Repo(**r) for r in data.get("repos", [])]


def save_repos_config(repos: list[Repo]) -> None:
    """Save repos list to repos.yaml."""
    import yaml
    SKILLS_REPO_ROOT.mkdir(parents=True, exist_ok=True)
    data = {"repos": [{"url": r.url, "branch": r.branch} for r in repos]}
    with open(REPOS_YAML, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def repo_dir(repo: Repo) -> Path:
    """Return the local skills directory for a repo."""
    if repo.name:
        return SKILLS_DIR / repo.name.replace("/", "__")
    return SKILLS_DIR


def clone_or_pull(repo: Repo) -> tuple[bool, str]:
    """Clone repo if not present, otherwise fetch latest. Returns (success, message)."""
    target = repo_dir(repo)
    if not target.exists():
        try:
            subprocess.run(
                ["git", "clone", "--branch", repo.branch, "--single-branch", repo.url, str(target)],
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
    """Git pull the repo. Returns (success, message)."""
    target = repo_dir(repo)
    if not target.exists():
        return clone_or_pull(repo)
    try:
        subprocess.run(
            ["git", "pull", "origin", repo.branch],
            cwd=target, check=True, capture_output=True, text=True, timeout=30,
        )
        return True, "Pulled latest"
    except subprocess.CalledProcessError as e:
        return False, f"Pull failed: {e.stderr}"


def delete_repo(repo: Repo) -> tuple[bool, str]:
    """Delete a repo's local directory and remove from repos.yaml. Returns (success, message)."""
    target = repo_dir(repo)
    if target.exists():
        shutil.rmtree(target)
    repos = load_repos_config()
    repos = [r for r in repos if r.url != repo.url]
    save_repos_config(repos)
    return True, "Deleted"


def has_remote_updates(repo: Repo) -> bool:
    """Check if remote has commits ahead of local HEAD. Returns True if update available."""
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
