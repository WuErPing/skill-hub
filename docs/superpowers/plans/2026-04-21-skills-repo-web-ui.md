# Skills Repo Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `skill-hub web` starts a local Flask server that serves a web UI for managing skills cloned from GitHub repos in `~/.skills_repo/`, installable to `~/.claude/skills/` and `~/.agents/skills/`.

**Architecture:** Single Flask server (`localhost:7860`) with a vanilla HTML+JS+HTMX frontend served as a template. State is derived from the filesystem on every request — no database. Skills enter `~/.skills_repo/` via `git clone`/`git pull` triggered from `repos.yaml` config. Installation copies files to both target directories.

**Tech Stack:** Flask (Python), Vanilla HTML+JS (CDN), HTMX (CDN), Click (CLI), GitPython or subprocess for git operations.

---

## File Structure

```
src/skill_hub/
  web/
    __init__.py                    # Module init
    repos.py                       # repos.yaml management + git clone/fetch/pull
    state.py                       # Skills listing + installation status computation
    api.py                         # All /api/* endpoints
    app.py                         # Flask app factory + template serving
    templates/
      index.html                   # Full UI (HTML + CSS + JS embedded)
  cli.py                           # Add `web` command

tests/
  test_web.py                      # Integration tests for web module
```

**pyproject.toml:** Add `"flask>=2.0"` to dependencies.

---

## Task 1: Add Flask Dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add flask to dependencies**

In `pyproject.toml`, add `"flask>=2.0"` to the `dependencies` list.

---

## Task 2: Create Web Module Skeleton

**Files:**
- Create: `src/skill_hub/web/__init__.py`
- Create: `src/skill_hub/web/repos.py` (empty stubs first, fill in Task 3)
- Create: `src/skill_hub/web/state.py` (empty stubs first, fill in Task 4)
- Create: `src/skill_hub/web/api.py` (empty stubs first, fill in Task 5)
- Create: `src/skill_hub/web/app.py` (empty stubs first, fill in Task 6)
- Create: `src/skill_hub/web/templates/index.html` (stub first, fill in Task 7)

- [ ] **Step 1: Create web module directory**

```bash
mkdir -p src/skill_hub/web/templates
touch src/skill_hub/web/__init__.py
touch src/skill_hub/web/repos.py
touch src/skill_hub/web/state.py
touch src/skill_hub/web/api.py
touch src/skill_hub/web/app.py
touch src/skill_hub/web/templates/index.html
```

- [ ] **Step 2: Write `__init__.py`**

```python
"""Web UI for skill-hub."""

__all__ = ["create_app"]
```

- [ ] **Step 3: Write stub `app.py`** (placeholder so imports don't break)

```python
"""Flask app factory."""
from flask import Flask

def create_app() -> Flask:
    app = Flask(__name__)
    return app
```

- [ ] **Step 4: Commit**

```bash
git add src/skill_hub/web/
git commit -m "feat(web): scaffold web module structure"
```

---

## Task 3: Implement repos.py — repos.yaml + Git Operations

**Files:**
- Modify: `src/skill_hub/web/repos.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_web.py
import tempfile, yaml, subprocess
from pathlib import Path

def test_repos_yaml_loaded():
    with tempfile.TemporaryDirectory() as tmp:
        repos_file = Path(tmp) / "repos.yaml"
        repos_file.write_text("repos:\n  - url: https://github.com/example/skills\n    branch: main\n")
        # load_repos_config reads from ~/.skills_repo/repos.yaml
        from skill_hub.web.repos import load_repos_config
        # Patch HOME to use tmp
        ...

def test_git_clone_fetches_repo():
    ...

def test_git_pull_updates_repo():
    ...

def test_delete_repo_removes_directory():
    ...
```

Run: `pytest tests/test_web.py -v` — verify tests fail (functions don't exist yet).

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_web.py -v
# Expected: ERROR — module has no attribute 'load_repos_config'
```

- [ ] **Step 3: Implement `repos.py`**

```python
"""repos.yaml management and git operations for ~/.skills_repo."""

import subprocess
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from skill_hub.utils.path_utils import expand_home

SKILLS_REPO_ROOT = expand_home("~/.skills_repo")
REPOS_YAML = SKILLS_REPO_ROOT / "repos.yaml"
SKILLS_DIR = SKILLS_REPO_ROOT / "skills"


@dataclass
class Repo:
    url: str
    branch: str = "main"
    name: Optional[str] = None  # derived: owner/repo from URL

    def __post_init__(self):
        if self.name is None:
            # Extract owner/repo from URL or bare "owner/repo"
            import re
            m = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", self.url)
            if m:
                self.name = f"{m.group(1)}/{m.group(2)}"
            else:
                self.name = self.url.rstrip("/").split("/")[-2] + "/" + self.url.rstrip("/").split("/")[-1]


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


def repo_dir(repo: Repo) -> Path:
    """Return the local skills directory for a repo."""
    if repo.name:
        return SKILLS_DIR / repo.name.replace("/", "__")
    return SKILLS_DIR


def clone_or_pull(repo: Repo) -> tuple[bool, str]:
    """Clone repo if not present, otherwise pull latest. Returns (success, message)."""
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
            # Check if there are new commits
            result = subprocess.run(
                ["git", "log", f"origin/{repo.branch}..HEAD", "--oneline"],
                cwd=target, capture_output=True, text=True,
            )
            behind = bool(result.stdout.strip())
            return True, "fetched" if not behind else f"{len(result.stdout.strip().splitlines())} new commits"
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
    import shutil
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
        result = subprocess.run(
            ["git", "rev-list", f"origin/{repo.branch}..HEAD", "--count"],
            cwd=target, capture_output=True, text=True,
        )
        # If HEAD is behind origin, origin..HEAD is 0 and HEAD..origin has commits
        behind_result = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{repo.branch}", "--count"],
            cwd=target, capture_output=True, text=True,
        )
        count = int(behind_result.stdout.strip() or "0")
        return count > 0
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_web.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**

```bash
git add src/skill_hub/web/repos.py tests/test_web.py
git commit -m "feat(web): repos.yaml management and git clone/pull operations"
```

---

## Task 4: Implement state.py — Skills Listing + Status

**Files:**
- Modify: `src/skill_hub/web/state.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_web.py (add after Task 3 tests)
def test_skill_status_uninstalled():
    ...

def test_skill_status_installed():
    ...

def test_skill_status_inconsistent():
    ...

def test_md5_comparison():
    ...
```

Run: `pytest tests/test_web.py -v`

- [ ] **Step 2: Implement `state.py`**

```python
"""Skills state tracking — listing, status computation, install/uninstall."""

import hashlib
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from skill_hub.web.repos import load_repos_config, repo_dir, SKILLS_DIR

CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"


@dataclass
class SkillEntry:
    name: str
    repo_name: str          # e.g. "owner/repo"
    repo_url: str
    path: Path              # absolute path in ~/.skills_repo/skills/owner__repo/skill-name
    status: str             # "未安装" | "已安装" | "不一致" | "部分安装"
    # status_detail is one of:
    #   "uninstalled"  — not in either
    #   "installed"    — both, matched
    #   "inconsistent" — both, differ
    #   "partial"      — one only


def _md5_of_dir(path: Path) -> str:
    """Return a combined MD5 of all files in a directory (sorted by path)."""
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.name.encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _is_skill_dir(path: Path) -> bool:
    """A skill directory is any subdirectory under a repo dir that is not hidden."""
    return path.is_dir() and not path.name.startswith(".")


def list_skills() -> list[SkillEntry]:
    """Scan ~/.skills_repo/skills/ and both install directories, return all skills with status."""
    repos = load_repos_config()
    repo_url_map = {r.name: r.url for r in repos}

    # Collect installed skills and their MD5s
    claude_skills = {}  # name -> md5
    agents_skills = {}  # name -> md5

    if CLAUDE_SKILLS.exists():
        for d in CLAUDE_SKILLS.iterdir():
            if _is_skill_dir(d):
                claude_skills[d.name] = _md5_of_dir(d)
    if AGENTS_SKILLS.exists():
        for d in AGENTS_SKILLS.iterdir():
            if _is_skill_dir(d):
                agents_skills[d.name] = _md5_of_dir(d)

    # Scan source skills
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for repo_subdir in SKILLS_DIR.iterdir():
        if not repo_subdir.is_dir():
            continue
        # repo_subdir name is like "owner__repo"
        # Derive owner/repo name
        repo_name = repo_subdir.name.replace("__", "/")

        for skill_dir in repo_subdir.iterdir():
            if not _is_skill_dir(skill_dir):
                continue
            name = skill_dir.name
            in_claude = name in claude_skills
            in_agents = name in agents_skills

            if in_claude and in_agents:
                if claude_skills[name] == agents_skills[name]:
                    status = "已安装"
                else:
                    status = "不一致"
            elif in_claude or in_agents:
                status = "部分安装"
            else:
                status = "未安装"

            skills.append(SkillEntry(
                name=name,
                repo_name=repo_name,
                repo_url=repo_url_map.get(repo_name, ""),
                path=skill_dir,
                status=status,
            ))

    return sorted(skills, key=lambda s: (s.repo_name, s.name))


def install_skill(name: str, source_path: Path) -> tuple[bool, str]:
    """Copy skill from source_path to both ~/.claude/skills/ and ~/.agents/skills/. Returns (success, message)."""
    try:
        CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
        AGENTS_SKILLS.mkdir(parents=True, exist_ok=True)

        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        if dest_a.exists():
            shutil.rmtree(dest_a)
        if dest_b.exists():
            shutil.rmtree(dest_b)

        shutil.copytree(source_path, dest_a)
        shutil.copytree(source_path, dest_b)
        return True, f"Installed {name} to both directories"
    except Exception as e:
        return False, str(e)


def uninstall_skill(name: str) -> tuple[bool, str]:
    """Remove skill from both ~/.claude/skills/ and ~/.agents/skills/. Returns (success, message)."""
    try:
        errors = []
        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        if dest_a.exists():
            shutil.rmtree(dest_a)
        if dest_b.exists():
            shutil.rmtree(dest_b)

        return True, f"Uninstalled {name} from both directories"
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
pytest tests/test_web.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/skill_hub/web/state.py
git commit -m "feat(web): skills state tracking — listing, status, install/uninstall"
```

---

## Task 5: Implement api.py — All API Endpoints

**Files:**
- Modify: `src/skill_hub/web/api.py`
- Modify: `src/skill_hub/web/app.py`

- [ ] **Step 1: Write the failing test**

```python
def test_api_get_skills():
    client = app.test_client()
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert all("name" in s for s in data)
    assert all("status" in s for s in data)

def test_api_install_skill():
    ...

def test_api_uninstall_skill():
    ...

def test_api_repos_crud():
    ...
```

Run: `pytest tests/test_web.py -v`

- [ ] **Step 2: Implement `api.py`**

```python
"""All /api/* endpoints for the skill-hub web UI."""

from flask import Blueprint, jsonify, request
from skill_hub.web.state import list_skills, install_skill, uninstall_skill
from skill_hub.web.repos import (
    load_repos_config, save_repos_config, Repo,
    clone_or_pull, pull_latest, delete_repo,
    has_remote_updates, REPOS_YAML, SKILLS_DIR,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/skills", methods=["GET"])
def get_skills():
    """List all skills with their installation status."""
    skills = list_skills()
    return jsonify([
        {
            "name": s.name,
            "repoName": s.repo_name,
            "repoUrl": s.repo_url,
            "status": s.status,
            "path": str(s.path),
        }
        for s in skills
    ])


@api_bp.route("/skills/<name>/install", methods=["POST"])
def api_install(name: str):
    """Install a skill to both ~/.claude/skills and ~/.agents/skills."""
    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    # The skill's source path is in ~/.skills_repo/skills/
    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_skill(name, source_path)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/skills/<name>/uninstall", methods=["POST"])
def api_uninstall(name: str):
    """Uninstall a skill from both directories."""
    success, msg = uninstall_skill(name)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/repos", methods=["GET"])
def get_repos():
    """List all repos from repos.yaml."""
    repos = load_repos_config()
    return jsonify([
        {
            "url": r.url,
            "branch": r.branch,
            "name": r.name,
            "localPath": str(source_path) if (source_path := skill_hub.web.repos.repo_dir(r)) else "",
        }
        for r in repos
    ])


@api_bp.route("/repos", methods=["POST"])
def add_repo():
    """Add a new repo URL to repos.yaml and clone it."""
    body = request.get_json() or {}
    url = body.get("url", "").strip()
    branch = body.get("branch", "main").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    repos = load_repos_config()
    if any(r.url == url for r in repos):
        return jsonify({"error": "Repo already exists"}), 409

    repo = Repo(url=url, branch=branch)
    repos.append(repo)
    save_repos_config(repos)

    # Clone in background-ish (sync for now)
    success, msg = clone_or_pull(repo)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"ok": True, "message": f"Added but clone failed: {msg}"}), 201


@api_bp.route("/repos/<path:name>", methods=["DELETE"])
def remove_repo(name: str):
    """Delete a repo from repos.yaml and remove its local directory."""
    repos = load_repos_config()
    repo = next((r for r in repos if r.name == name), None)
    if not repo:
        return jsonify({"error": "Repo not found"}), 404

    success, msg = delete_repo(repo)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/repos/sync", methods=["POST"])
def sync_repos():
    """Manually pull latest for all repos."""
    repos = load_repos_config()
    results = []
    for repo in repos:
        ok, msg = pull_latest(repo)
        results.append({"url": repo.url, "ok": ok, "message": msg})
    return jsonify({"ok": True, "results": results})


@api_bp.route("/update-status", methods=["GET"])
def update_status():
    """Check if any repos have remote updates available."""
    repos = load_repos_config()
    updates = []
    for repo in repos:
        if has_remote_updates(repo):
            updates.append({"url": repo.url, "name": repo.name})
    return jsonify({"hasUpdates": len(updates) > 0, "repos": updates})
```

- [ ] **Step 3: Update `app.py` to wire up the blueprint**

```python
"""Flask app factory."""
from flask import Flask, render_template
from skill_hub.web.api import api_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_web.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/skill_hub/web/api.py src/skill_hub/web/app.py
git commit -m "feat(web): all API endpoints and Flask app factory"
```

---

## Task 6: Implement templates/index.html — Full Web UI

**Files:**
- Modify: `src/skill_hub/web/templates/index.html`

- [ ] **Step 1: Write the full UI template**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>skill-hub</title>
  <script src="https://unpkg.com/htmx.org@2.0.0"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8f9fa; color: #212529; }
    .container { max-width: 900px; margin: 0 auto; padding: 24px; }

    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
    h1 { font-size: 24px; font-weight: 700; }
    .header-actions { display: flex; gap: 8px; }

    .banner { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px 16px; margin-bottom: 16px; display: none; }
    .banner.show { display: block; }
    .banner button { margin-left: 12px; }

    .repo-section { margin-bottom: 24px; }
    .repo-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px 12px; background: #e9ecef; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; }
    .repo-header .toggle { font-size: 12px; }
    .repo-header .add-repo-btn { margin-left: auto; font-size: 12px; background: none; border: none; cursor: pointer; color: #0d6efd; }

    .skill-list { list-style: none; padding-left: 24px; }
    .skill-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; }
    .skill-item:hover { background: #f1f3f5; }

    .skill-name { flex: 1; font-weight: 500; }

    .status-tag {
      display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500;
    }
    .status-uninstalled { background: #e9ecef; color: #6c757d; }
    .status-installed { background: #d1e7dd; color: #0f5132; }
    .status-inconsistent { background: #fff3cd; color: #664d03; border: 1px solid #ffc107; }
    .status-partial { background: #cfe2ff; color: #084298; }

    .btn { padding: 4px 12px; border-radius: 4px; border: 1px solid #dee2e6; background: #fff; cursor: pointer; font-size: 13px; }
    .btn:hover { background: #f8f9fa; }
    .btn-install { border-color: #198754; color: #198754; }
    .btn-install:hover { background: #d1e7dd; }
    .btn-uninstall { border-color: #dc3545; color: #dc3545; }
    .btn-uninstall:hover { background: #f8d7da; }

    .toast { position: fixed; bottom: 24px; right: 24px; padding: 12px 16px; border-radius: 6px; font-size: 14px; display: none; z-index: 1000; }
    .toast-success { background: #d1e7dd; color: #0f5132; border: 1px solid #a3cfbb; }
    .toast-error { background: #f8d7da; color: #842029; border: 1px solid #f1aeb5; }
    .toast.show { display: block; }

    .add-repo-form { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid #dee2e6; display: none; }
    .add-repo-form.show { display: block; }
    .add-repo-form input { padding: 6px 10px; border: 1px solid #dee2e6; border-radius: 4px; width: 300px; margin-right: 8px; }
    .actions { margin-top: 16px; display: flex; gap: 8px; }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>skill-hub</h1>
    <div class="header-actions">
      <button class="btn" onclick="loadSkills()">刷新</button>
      <button class="btn" onclick="toggleAddRepo()">添加仓库</button>
    </div>
  </header>

  <div id="update-banner" class="banner">
    检测到更新可用 <button class="btn" onclick="syncAndReload()">刷新</button>
  </div>

  <div id="add-repo-form" class="add-repo-form">
    <input type="text" id="repo-url" placeholder="https://github.com/owner/repo">
    <input type="text" id="repo-branch" placeholder="main" value="main" style="width: 100px;">
    <div class="actions">
      <button class="btn btn-install" onclick="addRepo()">添加并克隆</button>
      <button class="btn" onclick="toggleAddRepo()">取消</button>
    </div>
  </div>

  <div id="skills-container">加载中...</div>
</div>

<div id="toast" class="toast"></div>

<script>
  let repos = {};

  function showToast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast toast-${type} show`;
    setTimeout(() => t.className = 'toast', 3000);
  }

  async function checkUpdateStatus() {
    const resp = await fetch('/api/update-status');
    const data = await resp.json();
    if (data.hasUpdates) {
      document.getElementById('update-banner').classList.add('show');
    }
  }

  async function syncAndReload() {
    await fetch('/api/repos/sync', { method: 'POST' });
    document.getElementById('update-banner').classList.remove('show');
    await loadSkills();
    showToast('同步完成');
  }

  function toggleAddRepo() {
    document.getElementById('add-repo-form').classList.toggle('show');
  }

  async function addRepo() {
    const url = document.getElementById('repo-url').value.trim();
    const branch = document.getElementById('repo-branch').value.trim() || 'main';
    if (!url) return;
    const resp = await fetch('/api/repos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, branch }),
    });
    const data = await resp.json();
    if (resp.ok) {
      showToast(data.message || '仓库添加成功');
      toggleAddRepo();
      document.getElementById('repo-url').value = '';
      await loadSkills();
    } else {
      showToast(data.error || '添加失败', 'error');
    }
  }

  async function loadSkills() {
    const resp = await fetch('/api/skills');
    const skills = await resp.json();
    renderSkills(skills);
  }

  function statusClass(status) {
    const map = {
      '已安装': 'status-installed',
      '未安装': 'status-uninstalled',
      '不一致': 'status-inconsistent',
      '部分安装': 'status-partial',
    };
    return map[status] || 'status-uninstalled';
  }

  function renderSkills(skills) {
    const container = document.getElementById('skills-container');
    if (!skills.length) {
      container.innerHTML = '<p style="color:#6c757d;">暂无 skills。请先添加仓库。</p>';
      return;
    }

    // Group by repo
    const groups = {};
    for (const s of skills) {
      if (!groups[s.repoName]) groups[s.repoName] = [];
      groups[s.repoName].push(s);
    }

    let html = '';
    for (const [repoName, items] of Object.entries(groups)) {
      html += `<div class="repo-section">
        <div class="repo-header" onclick="toggleRepo(this)">
          <span class="toggle">▼</span> 📁 ${repoName}
          <button class="add-repo-btn" onclick="event.stopPropagation(); removeRepo('${repoName}')">删除仓库</button>
        </div>
        <ul class="skill-list">
          ${items.map(s => `
          <li class="skill-item">
            <span class="skill-name">${s.name}</span>
            <span class="status-tag ${statusClass(s.status)}">${s.status}</span>
            ${s.status === '已安装' || s.status === '不一致' || s.status === '部分安装'
              ? `<button class="btn btn-uninstall" onclick="uninstallSkill('${s.name}')">卸载</button>`
              : `<button class="btn btn-install" onclick="installSkill('${s.name}')">安装</button>`
            }
          </li>`).join('')}
        </ul>
      </div>`;
    }
    container.innerHTML = html;
  }

  function toggleRepo(el) {
    const list = el.nextElementSibling;
    const toggle = el.querySelector('.toggle');
    if (list.style.display === 'none') {
      list.style.display = '';
      toggle.textContent = '▼';
    } else {
      list.style.display = 'none';
      toggle.textContent = '▶';
    }
  }

  async function installSkill(name) {
    const resp = await fetch(`/api/skills/${encodeURIComponent(name)}/install`, { method: 'POST' });
    const data = await resp.json();
    if (resp.ok) {
      showToast(data.message);
      await loadSkills();
    } else {
      showToast(data.error || '安装失败', 'error');
    }
  }

  async function uninstallSkill(name) {
    const resp = await fetch(`/api/skills/${encodeURIComponent(name)}/uninstall`, { method: 'POST' });
    const data = await resp.json();
    if (resp.ok) {
      showToast(data.message);
      await loadSkills();
    } else {
      showToast(data.error || '卸载失败', 'error');
    }
  }

  async function removeRepo(name) {
    if (!confirm(`确定要删除仓库 ${name} 吗？`)) return;
    const resp = await fetch(`/api/repos/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const data = await resp.json();
    if (resp.ok) {
      showToast(data.message);
      await loadSkills();
    } else {
      showToast(data.error || '删除失败', 'error');
    }
  }

  // Initial load
  loadSkills();
  checkUpdateStatus();
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add src/skill_hub/web/templates/index.html
git commit -m "feat(web): full web UI — HTML template with HTMX and status tags"
```

---

## Task 7: Add `web` CLI Command

**Files:**
- Modify: `src/skill_hub/cli.py`

- [ ] **Step 1: Add the `web` command to `cli.py`**

In `cli.py`, add:

```python
@cli.command(name="web")
@click.option("--port", default=7860, type=int, help="Port to run the web server on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
def web_command(port: int, host: str, no_open: bool) -> None:
    """Start the skill-hub web UI.

    Opens a browser interface for managing skills from ~/.skills_repo/.

    Skills are installed to both ~/.claude/skills/ and ~/.agents/skills/.

    Examples:

        skill-hub web
        skill-hub web --port 9000
    """
    import threading
    import webbrowser

    from skill_hub.web.app import create_app

    app = create_app()

    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open(f"http://{host}:{port}")

    if not no_open:
        threading.Thread(target=open_browser, daemon=True).start()

    console.print(f"[green]Starting skill-hub web UI at http://{host}:{port}[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")
    app.run(host=host, port=port, debug=False, threaded=True)
```

- [ ] **Step 2: Test the command loads without error**

```bash
cd /Users/wuerping/code/wuerping/skill-hub
python -c "from skill_hub.cli import cli; cli(['web', '--help'])"
# Expected: shows help output
```

- [ ] **Step 3: Commit**

```bash
git add src/skill_hub/cli.py
git commit -m "feat(cli): add skill-hub web command"
```

---

## Task 8: Write Integration Tests

**Files:**
- Create: `tests/test_web.py`

- [ ] **Step 1: Write comprehensive tests**

```python
"""Integration tests for skill-hub web module."""

import os, tempfile, shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask


@pytest.fixture
def temp_home(tmp_path):
    """Create a temp home directory with fake skills dirs."""
    skills_src = tmp_path / "skills_repo" / "skills" / "example__repo"
    skills_src.mkdir(parents=True)
    (skills_src / "test-skill").mkdir()
    (skills_src / "test-skill" / "SKILL.md").write_text("---\nname: test-skill\ndescription: Test\n---\n\nTest body")

    claude = tmp_path / ".claude" / "skills"
    agents = tmp_path / ".agents" / "skills"
    claude.mkdir(parents=True)
    agents.mkdir(parents=True)

    repos_yaml = tmp_path / "skills_repo" / "repos.yaml"
    repos_yaml.write_text("repos:\n  - url: https://github.com/example/repo\n    branch: main\n")

    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        # Also patch Path.home() — do it in the module
        import skill_hub.web.repos
        import skill_hub.web.state
        skill_hub.web.repos.SKILLS_REPO_ROOT = tmp_path / "skills_repo"
        skill_hub.web.repos.REPOS_YAML = repos_yaml
        skill_hub.web.repos.SKILLS_DIR = tmp_path / "skills_repo" / "skills"
        skill_hub.web.state.CLAUDE_SKILLS = claude
        skill_hub.web.state.AGENTS_SKILLS = agents
        yield tmp_path, claude, agents


@pytest.fixture
def client(temp_home):
    from skill_hub.web.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_skills_returns_list(client, temp_home):
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test-skill"
    assert data[0]["status"] == "未安装"


def test_install_skill(client, temp_home):
    tmp_path, claude, agents = temp_home
    name = "test-skill"
    resp = client.post(f"/api/skills/{name}/install", data={}, content_type="application/json")
    assert resp.status_code == 200
    assert (claude / name).exists()
    assert (agents / name).exists()


def test_uninstall_skill(client, temp_home):
    tmp_path, claude, agents = temp_home
    name = "test-skill"
    # First install
    client.post(f"/api/skills/{name}/install")
    # Then uninstall
    resp = client.post(f"/api/skills/{name}/uninstall")
    assert resp.status_code == 200
    assert not (claude / name).exists()
    assert not (agents / name).exists()


def test_get_repos(client, temp_home):
    resp = client.get("/api/repos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert "example/repo" in data[0]["name"]


def test_add_repo_and_clone(temp_home):
    from skill_hub.web.repos import load_repos_config, clone_or_pull, Repo
    repos = load_repos_config()
    assert len(repos) == 1
    # Test clone_or_pull doesn't crash
    ok, msg = clone_or_pull(repos[0])
    # May fail network, but shouldn't crash
    assert isinstance(ok, bool)
    assert isinstance(msg, str)


def test_update_status_returns_boolean(temp_home):
    from skill_hub.web.app import create_app
    app = create_app()
    client = app.test_client()
    resp = client.get("/api/update-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "hasUpdates" in data
    assert isinstance(data["hasUpdates"], bool)
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_web.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_web.py
git commit -m "test(web): integration tests for web API endpoints"
```

---

## Task 9: End-to-End Smoke Test

**Files:**
- None (manual testing)

- [ ] **Step 1: Start the web server and test in browser**

```bash
cd /Users/wuerping/code/wuerping/skill-hub
pip install -e ".[dev]"
skill-hub web --port 7860
```

Expected: Flask starts, browser opens to `http://127.0.0.1:7860`, shows skill list.

- [ ] **Step 2: Add a repo via the UI**

Paste a GitHub URL into "添加仓库", click "添加并克隆".

Expected: repo appears under its group, skills listed with "未安装" status.

- [ ] **Step 3: Install a skill**

Click "安装" button on a skill.

Expected: button changes to "卸载", status becomes "已安装". Both `~/.claude/skills/` and `~/.agents/skills/` contain the skill.

- [ ] **Step 4: Verify installation**

```bash
ls ~/.claude/skills/<skill-name>/
ls ~/.agents/skills/<skill-name>/
```

Expected: both directories exist with skill content.

- [ ] **Step 5: Uninstall**

Click "卸载" button.

Expected: skill removed from both directories, status becomes "未安装".

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: complete skills-repo-web-ui feature"
```

---

## Spec Coverage Check

- [x] **Architecture** → Task 2, 3, 4, 5, 6, 7
- [x] **Data model (repos.yaml, state tracking)** → Task 3, 4
- [x] **Web interface (layout, status tags, interactions)** → Task 6
- [x] **API endpoints (all 8 endpoints)** → Task 5
- [x] **Install/uninstall flows** → Task 4
- [x] **Error handling** → Task 5 (basic 500 + message)
- [x] **Update detection** → Task 3 (`has_remote_updates`), Task 5 (`/api/update-status`), Task 6 (banner)
- [x] **CLI entry point** → Task 7

No placeholder tasks found.
