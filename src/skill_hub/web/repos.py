"""repos.yaml management and git operations for ~/.skills_repo."""

import re
import shutil
import subprocess
import threading
import uuid
import yaml
from dataclasses import dataclass, field
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



def repo_dir(repo: Repo) -> Path:
    """Return the repo directory. For local repos, returns the local path directly."""
    if repo.is_local:
        return expand_home(repo.url).resolve()
    return REPOS_DIR / repo.dir_name


def mapping_path(repo: Repo) -> Path:
    """Return the YAML mapping file path for a repo."""
    return MAPPINGS_DIR / f"{repo.dir_name}.yaml"


def load_repos_config() -> list[Repo]:
    """Load repos from repos.yaml. Returns empty list if file doesn't exist."""
    if not REPOS_YAML.exists():
        return []
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


def _find_skills_in_repo(repo_dir: Path) -> tuple[dict[str, str], list[str]]:
    """Scan a cloned repo for skill directories (contain SKILL.md) and return {name: relative_path}, [conflicts].

    Conflicts occur when multiple SKILL.md files reside in directories with the
    same name (e.g. repo/a/skill-x/SKILL.md and repo/b/skill-x/SKILL.md).
    The first discovered path wins; duplicates are reported as conflicts.
    """
    mapping: dict[str, str] = {}
    conflicts: list[str] = []
    if not repo_dir.exists():
        return mapping, conflicts

    for skill_md in repo_dir.rglob("SKILL.md"):
        # skill dir is the parent of SKILL.md
        skill_dir = skill_md.parent
        # skill name = directory name
        name = skill_dir.name
        # relative path from repo root
        rel = skill_dir.relative_to(repo_dir)
        rel_str = str(rel)
        if name in mapping:
            if mapping[name] != rel_str:
                conflicts.append(
                    f"'{name}' at '{rel_str}' conflicts with existing '{mapping[name]}'"
                )
            # skip duplicate / conflicting names — first wins
            continue
        mapping[name] = rel_str

    return mapping, conflicts


def sync_mapping(repo: Repo) -> tuple[bool, str]:
    """Clone or update a repo and rebuild its skill mapping. Returns (success, message)."""
    target = repo_dir(repo)

    if repo.is_local:
        if not target.exists():
            return False, f"Local path not found: {target}"
        action = "Scanned"
    else:
        if not target.exists():
            # Check git first
            git_ok, git_msg = check_git_installed()
            if not git_ok:
                return False, f"Git not installed: {git_msg}"

            # Check network for remote repos
            net_ok, net_msg = check_network_connectivity()
            if not net_ok:
                return False, f"Network error: {net_msg}"

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

    mapping, conflicts = _find_skills_in_repo(target)
    save_skill_mapping(repo, mapping)
    count = len(mapping)
    msg = f"{action} {repo.url} — found {count} skill(s)"
    if conflicts:
        msg += f" (warning: {len(conflicts)} name conflict(s) skipped)"
    return True, msg


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
    mapping, conflicts = _find_skills_in_repo(target)
    save_skill_mapping(repo, mapping)
    count = len(mapping)
    msg = f"Pulled {repo.url} — {count} skill(s) in mapping"
    if conflicts:
        msg += f" (warning: {len(conflicts)} name conflict(s) skipped)"
    return True, msg


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
            cwd=target, capture_output=True, timeout=5,
        )
        behind_result = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{repo.branch}", "--count"],
            cwd=target, capture_output=True, text=True,
        )
        count = int(behind_result.stdout.strip() or "0")
        return count > 0
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return False


def check_git_installed() -> tuple[bool, str]:
    """Check if git is installed and accessible."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "git command returned non-zero exit code"
    except FileNotFoundError:
        return False, "git not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "git --version timed out"
    except Exception as e:
        return False, str(e)


def check_network_connectivity() -> tuple[bool, str]:
    """Check if we can reach GitHub."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "https://github.com/anthropics/skills.git"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return True, "Connected to GitHub"
        return False, f"git ls-remote failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Network connection timed out"
    except Exception as e:
        return False, str(e)


def diagnose_repo(repo: Repo) -> dict:
    """Run diagnostics on a repo and return a detailed report."""
    report = {
        "repo_url": repo.url,
        "repo_name": repo.name,
        "is_local": repo.is_local,
        "checks": [],
    }

    # Check 1: Git installed
    git_ok, git_msg = check_git_installed()
    report["checks"].append({
        "name": "git_installed",
        "ok": git_ok,
        "message": git_msg,
    })

    if not git_ok:
        report["overall_ok"] = False
        report["summary"] = "Git is not installed"
        return report

    # Check 2: Network connectivity (for remote repos)
    if not repo.is_local:
        net_ok, net_msg = check_network_connectivity()
        report["checks"].append({
            "name": "network_connectivity",
            "ok": net_ok,
            "message": net_msg,
        })
        if not net_ok:
            report["overall_ok"] = False
            report["summary"] = f"Cannot reach GitHub: {net_msg}"
            return report

    # Check 3: Repo directory exists
    target = repo_dir(repo)
    dir_exists = target.exists()
    report["checks"].append({
        "name": "repo_dir_exists",
        "ok": dir_exists,
        "message": f"Directory exists: {target}" if dir_exists else f"Directory not found: {target}",
    })

    if not dir_exists:
        report["overall_ok"] = False
        report["summary"] = "Repo not cloned"
        return report

    # Check 4: Is it a git repo?
    is_git = (target / ".git").exists()
    report["checks"].append({
        "name": "is_git_repo",
        "ok": is_git,
        "message": "Valid git repository" if is_git else "Not a git repository",
    })

    # Check 5: SKILL.md files exist
    skill_mds = list(target.rglob("SKILL.md"))
    skill_count = len(skill_mds)
    report["checks"].append({
        "name": "skill_md_files",
        "ok": skill_count > 0,
        "message": f"Found {skill_count} SKILL.md file(s)",
    })

    if skill_count > 0:
        # Show first few SKILL.md paths
        sample_paths = [str(p.relative_to(target)) for p in skill_mds[:5]]
        report["checks"][-1]["sample_paths"] = sample_paths

    # Check 6: Mapping file exists
    mp = mapping_path(repo)
    mapping_exists = mp.exists()
    report["checks"].append({
        "name": "mapping_file",
        "ok": mapping_exists,
        "message": f"Mapping file exists: {mp}" if mapping_exists else f"Mapping file not found: {mp}",
    })

    # Check 7: Mapping is not empty
    if mapping_exists:
        mapping = load_skill_mapping(repo)
        skill_count_in_mapping = len(mapping)
        report["checks"].append({
            "name": "mapping_content",
            "ok": skill_count_in_mapping > 0,
            "message": f"Mapping contains {skill_count_in_mapping} skill(s)",
        })
        if skill_count_in_mapping > 0:
            report["checks"][-1]["skills"] = list(mapping.keys())[:10]

    # Check 8: Scan for skills
    mapping_scanned, conflicts = _find_skills_in_repo(target)
    report["checks"].append({
        "name": "skill_scan",
        "ok": len(mapping_scanned) > 0,
        "message": f"Scan found {len(mapping_scanned)} skill(s)",
    })
    if conflicts:
        report["checks"][-1]["conflicts"] = conflicts

    # Overall status
    all_ok = all(c["ok"] for c in report["checks"])
    report["overall_ok"] = all_ok

    if all_ok:
        report["summary"] = f"All checks passed. Found {len(mapping_scanned)} skill(s)."
    else:
        failed_checks = [c["name"] for c in report["checks"] if not c["ok"]]
        report["summary"] = f"Failed checks: {', '.join(failed_checks)}"

    return report


def diagnose_all_repos() -> list[dict]:
    """Run diagnostics on all configured repos."""
    repos = load_repos_config()
    return [diagnose_repo(repo) for repo in repos]


# ---------------------------------------------------------------------------
# Async task tracking for repo clone/pull with progress
# ---------------------------------------------------------------------------

@dataclass
class RepoTask:
    task_id: str
    url: str
    branch: str
    status: str = "running"       # running | success | error
    progress: int = 0             # 0-100
    step: str = ""                # human-readable current step
    error: str = ""               # error message if failed
    repo_name: str = ""           # populated after clone

    def to_dict(self) -> dict:
        return {
            "taskId": self.task_id,
            "url": self.url,
            "branch": self.branch,
            "status": self.status,
            "progress": self.progress,
            "step": self.step,
            "error": self.error,
            "repoName": self.repo_name,
        }


_tasks: dict[str, RepoTask] = {}
_tasks_lock = threading.Lock()


def get_task(task_id: str) -> Optional[RepoTask]:
    with _tasks_lock:
        return _tasks.get(task_id)


def _parse_clone_progress(line: str) -> Optional[tuple[int, str]]:
    """Parse git clone --progress stderr line. Returns (percent, step) or None."""
    # "Receiving objects:  45% (123/270)" etc.
    m = re.search(r"(Receiving objects|Resolving deltas|remote: Counting objects|remote: Compressing objects):\s+(\d+)%", line)
    if m:
        stage = m.group(1)
        pct = int(m.group(2))
        # Weight: receiving 0-70%, resolving 70-95%
        if "Receiving" in stage or "Counting" in stage or "Compressing" in stage:
            return int(pct * 0.70), f"{stage}: {pct}%"
        elif "Resolving" in stage:
            return 70 + int(pct * 0.25), f"{stage}: {pct}%"
    # "Cloning into '...'"
    m2 = re.search(r"Cloning into '(.+)'", line)
    if m2:
        return 5, f"Cloning into '{m2.group(1)}'"
    return None


def _run_task(task: RepoTask):
    """Background thread: clone or pull a repo, update task progress."""
    try:
        target = repo_dir(Repo(url=task.url, branch=task.branch))
        is_new = not target.exists()

        if is_new:
            # --- Clone ---
            task.step = "Checking git..."
            task.progress = 1
            git_ok, git_msg = check_git_installed()
            if not git_ok:
                task.status = "error"
                task.error = f"Git not installed: {git_msg}"
                return

            task.step = "Checking network..."
            task.progress = 3
            net_ok, net_msg = check_network_connectivity()
            if not net_ok:
                task.status = "error"
                task.error = f"Network error: {net_msg}"
                return

            task.step = "Cloning..."
            task.progress = 5

            proc = subprocess.Popen(
                ["git", "clone", "--branch", task.branch, "--progress", task.url, str(target)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            # Read stderr line by line for progress
            assert proc.stderr is not None
            for line in proc.stderr:
                line = line.strip()
                if not line:
                    continue
                parsed = _parse_clone_progress(line)
                if parsed:
                    task.progress, task.step = parsed
                elif "fatal:" in line or "error:" in line:
                    task.status = "error"
                    task.error = line
                    proc.wait()
                    return

            ret = proc.wait()
            if ret != 0:
                task.status = "error"
                task.error = f"git clone exited with code {ret}"
                return

            task.progress = 95
            task.step = "Scanning skills..."
        else:
            # --- Pull ---
            task.step = "Pulling updates..."
            task.progress = 50
            try:
                subprocess.run(
                    ["git", "pull", "origin", task.branch],
                    cwd=target, check=True, capture_output=True, text=True, timeout=120,
                )
            except subprocess.CalledProcessError as e:
                task.status = "error"
                task.error = f"Pull failed: {e.stderr}"
                return
            except subprocess.TimeoutExpired:
                task.status = "error"
                task.error = "Pull timed out"
                return
            task.progress = 95
            task.step = "Scanning skills..."

        # Build mapping
        repo = Repo(url=task.url, branch=task.branch)
        mapping, conflicts = _find_skills_in_repo(target)
        save_skill_mapping(repo, mapping)
        count = len(mapping)
        task.repo_name = repo.name or ""
        task.progress = 100
        msg = f"{'Cloned' if is_new else 'Pulled'} {task.url} — {count} skill(s)"
        if conflicts:
            msg += f" ({len(conflicts)} conflict(s) skipped)"
        task.step = msg
        task.status = "success"

    except Exception as e:
        task.status = "error"
        task.error = str(e)


def start_repo_task(url: str, branch: str = "main") -> RepoTask:
    """Start an async clone/pull task. Returns the task immediately."""
    task_id = uuid.uuid4().hex[:12]
    task = RepoTask(task_id=task_id, url=url, branch=branch)
    with _tasks_lock:
        _tasks[task_id] = task
    thread = threading.Thread(target=_run_task, args=(task,), daemon=True)
    thread.start()
    return task
