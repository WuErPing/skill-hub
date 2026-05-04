# 可扩展安装目录支持实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 skill-hub 从固定两个安装目录（~/.claude/skills, ~/.agents/skills）改造为支持用户自定义任意数量的安装目录，同时保持界面紧凑。

**Architecture:** 引入 `InstallDir` 配置模型和 `config.json` 持久化存储；将 `SkillEntry` 的固定字段改为动态 `dir_status` 字典；前端用首字母缩写圆点网格替代固定列。

**Tech Stack:** Python, Flask, Jinja2, Vanilla JS, Tailwind CSS, pytest

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/skill_hub/web/config.py` | 安装目录配置管理（读取/保存/初始化 config.json） | **新建** |
| `src/skill_hub/web/state.py` | SkillEntry 数据模型、安装/卸载逻辑、状态扫描 | **大幅修改** |
| `src/skill_hub/web/api.py` | REST API 接口（/skills, /install, /uninstall, /install-to, /settings） | **大幅修改** |
| `src/skill_hub/web/templates/index.html` | 前端界面：设置面板、圆点组件、tooltip、列表渲染 | **大幅修改** |
| `tests/test_web.py` | 集成测试更新 | **大幅修改** |
| `tests/test_config.py` | 配置模块单元测试 | **新建** |

---

## Task 1: 创建安装目录配置模块

**Files:**
- Create: `src/skill_hub/web/config.py`
- Test: `tests/test_config.py`

### Step 1: 编写配置模块测试

```python
"""Tests for install directory configuration management."""

import json
from pathlib import Path

import pytest

from skill_hub.web.config import InstallDir, get_install_dirs, add_install_dir, remove_install_dir


@pytest.fixture
def temp_config(tmp_path):
    """Override config file location for tests."""
    import skill_hub.web.config as config_module
    original = config_module.CONFIG_FILE
    config_module.CONFIG_FILE = tmp_path / "config.json"
    yield tmp_path
    config_module.CONFIG_FILE = original


def test_default_dirs_on_first_load(temp_config):
    """When config.json doesn't exist, default dirs are auto-created."""
    dirs = get_install_dirs()
    assert len(dirs) == 2
    assert dirs[0].label == "claude"
    assert dirs[0].is_default is True
    assert dirs[1].label == "agents"
    assert dirs[1].is_default is True


def test_add_custom_dir(temp_config):
    """Adding a custom dir persists to config."""
    add_install_dir("~/.cursor/skills")
    dirs = get_install_dirs()
    labels = [d.label for d in dirs]
    assert "cursor" in labels
    # Verify persisted
    with open(get_install_dirs.__module__.CONFIG_FILE) as f:
        data = json.load(f)
    assert any(d["label"] == "cursor" for d in data["installDirs"])


def test_add_duplicate_dir_ignored(temp_config):
    """Adding an existing dir is ignored."""
    add_install_dir("~/.claude/skills")  # already default
    dirs = get_install_dirs()
    assert len(dirs) == 2


def test_remove_custom_dir(temp_config):
    """Removing a custom dir works."""
    add_install_dir("~/.cursor/skills")
    remove_install_dir("cursor")
    dirs = get_install_dirs()
    labels = [d.label for d in dirs]
    assert "cursor" not in labels


def test_cannot_remove_default_dir(temp_config):
    """Removing a default dir raises error."""
    with pytest.raises(ValueError, match="Cannot remove default"):
        remove_install_dir("claude")


def test_abbreviation_generation(temp_config):
    """Abbreviations avoid conflicts."""
    add_install_dir("~/.cursor/skills")   # "cursor" -> "Cr"
    add_install_dir("~/.custom/skills")   # "custom" -> "Cu"
    dirs = get_install_dirs()
    cursor_dir = next(d for d in dirs if d.label == "cursor")
    custom_dir = next(d for d in dirs if d.label == "custom")
    assert cursor_dir.abbreviation == "Cr"
    assert custom_dir.abbreviation == "Cu"
```

Run: `pytest tests/test_config.py -v`
Expected: FAIL (module doesn't exist yet)

### Step 2: 实现配置模块

```python
"""Install directory configuration management."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from skill_hub.utils.path_utils import expand_home

SKILLS_REPO_ROOT = expand_home("~/.skills_repo")
CONFIG_FILE = SKILLS_REPO_ROOT / "config.json"

_DEFAULT_DIRS = [
    {"path": "~/.claude/skills", "label": "claude", "isDefault": True},
    {"path": "~/.agents/skills", "label": "agents", "isDefault": True},
]


@dataclass
class InstallDir:
    path: str
    label: str
    is_default: bool = False
    abbreviation: str = ""

    def __post_init__(self):
        if not self.abbreviation:
            self.abbreviation = _generate_abbreviation(self.label)

    @property
    def resolved_path(self) -> Path:
        return expand_home(self.path)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "label": self.label,
            "isDefault": self.is_default,
            "abbreviation": self.abbreviation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "InstallDir":
        return cls(
            path=d["path"],
            label=d["label"],
            is_default=d.get("isDefault", False),
            abbreviation=d.get("abbreviation", ""),
        )


def _generate_abbreviation(label: str) -> str:
    """Generate a unique abbreviation for a label.
    
    Algorithm:
    1. Take first letter
    2. If conflicts with existing dirs, take first two letters
    3. If still conflicts, take first three, etc.
    4. If label is exhausted, add numeric suffix
    """
    dirs = get_install_dirs()
    existing = {d.abbreviation for d in dirs}
    
    for length in range(1, len(label) + 1):
        abbr = label[:length].capitalize()
        if abbr not in existing:
            return abbr
    
    # Fallback: add numeric suffix
    suffix = 1
    base = label.capitalize()
    while f"{base}{suffix}" in existing:
        suffix += 1
    return f"{base}{suffix}"


def get_install_dirs() -> list[InstallDir]:
    """Load install directories from config.json.
    
    If config doesn't exist, create it with defaults.
    """
    if not CONFIG_FILE.exists():
        dirs = [InstallDir.from_dict(d) for d in _DEFAULT_DIRS]
        _save_config(dirs)
        return dirs
    
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return [InstallDir.from_dict(d) for d in data.get("installDirs", [])]
    except (json.JSONDecodeError, KeyError):
        dirs = [InstallDir.from_dict(d) for d in _DEFAULT_DIRS]
        _save_config(dirs)
        return dirs


def _save_config(dirs: list[InstallDir]) -> None:
    """Persist install directories to config.json."""
    SKILLS_REPO_ROOT.mkdir(parents=True, exist_ok=True)
    data = {"installDirs": [d.to_dict() for d in dirs]}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_install_dir(path: str) -> InstallDir:
    """Add a new install directory. 
    
    Args:
        path: Directory path (supports ~ expansion)
        
    Returns:
        The created InstallDir
        
    Raises:
        ValueError: If path already exists in config
    """
    dirs = get_install_dirs()
    resolved = expand_home(path)
    
    for d in dirs:
        if d.resolved_path == resolved:
            raise ValueError(f"Directory already configured: {path}")
    
    # Derive label from directory name
    label = resolved.name if resolved.name != "skills" else resolved.parent.name
    if not label:
        label = "dir"
    
    # Ensure unique label
    existing_labels = {d.label for d in dirs}
    base_label = label
    suffix = 1
    while label in existing_labels:
        label = f"{base_label}{suffix}"
        suffix += 1
    
    new_dir = InstallDir(path=path, label=label, is_default=False)
    dirs.append(new_dir)
    _save_config(dirs)
    return new_dir


def remove_install_dir(label: str) -> None:
    """Remove an install directory by label.
    
    Args:
        label: Directory label to remove
        
    Raises:
        ValueError: If directory is default or not found
    """
    dirs = get_install_dirs()
    target = next((d for d in dirs if d.label == label), None)
    
    if target is None:
        raise ValueError(f"Directory not found: {label}")
    if target.is_default:
        raise ValueError(f"Cannot remove default directory: {label}")
    
    dirs = [d for d in dirs if d.label != label]
    _save_config(dirs)
```

Run: `pytest tests/test_config.py -v`
Expected: PASS

### Step 3: Commit

```bash
git add src/skill_hub/web/config.py tests/test_config.py
git commit -m "feat: add install directory configuration module"
```

---

## Task 2: 重构 SkillEntry 和状态扫描逻辑

**Files:**
- Modify: `src/skill_hub/web/state.py`
- Test: `tests/test_web.py` (更新 fixture)

### Step 4: 更新测试 fixture 以支持动态目录

修改 `tests/test_web.py` 中的 `temp_home` fixture：

```python
@pytest.fixture
def temp_home(tmp_path):
    """Create a temp home directory with fake skills dirs."""
    # Setup repos
    repo_clone = tmp_path / "skills_repo" / "repos" / "example__repo"
    repo_clone.mkdir(parents=True)
    (repo_clone / "test-skill").mkdir()
    (repo_clone / "test-skill" / "SKILL.md").write_text("---\nname: test-skill\ndescription: Test\n---\n\nTest body")

    mapping_file = tmp_path / "skills_repo" / "mappings" / "example__repo.yaml"
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    mapping_file.write_text("test-skill: test-skill\n")

    # Setup install dirs
    claude = tmp_path / ".claude" / "skills"
    agents = tmp_path / ".agents" / "skills"
    cursor = tmp_path / ".cursor" / "skills"
    claude.mkdir(parents=True)
    agents.mkdir(parents=True)
    cursor.mkdir(parents=True)

    repos_yaml = tmp_path / "skills_repo" / "repos.yaml"
    repos_yaml.write_text("repos:\n  - url: https://github.com/example/repo\n    branch: main\n")

    # Create config.json with test dirs
    config_file = tmp_path / "skills_repo" / "config.json"
    config_file.write_text(json.dumps({
        "installDirs": [
            {"path": str(claude), "label": "claude", "isDefault": True, "abbreviation": "C"},
            {"path": str(agents), "label": "agents", "isDefault": True, "abbreviation": "A"},
            {"path": str(cursor), "label": "cursor", "isDefault": False, "abbreviation": "Cr"},
        ]
    }))

    import skill_hub.web.repos
    import skill_hub.web.state
    import skill_hub.web.config as config_module
    
    skill_hub.web.repos.SKILLS_REPO_ROOT = tmp_path / "skills_repo"
    skill_hub.web.repos.REPOS_YAML = repos_yaml
    skill_hub.web.repos.REPOS_DIR = tmp_path / "skills_repo" / "repos"
    skill_hub.web.repos.MAPPINGS_DIR = tmp_path / "skills_repo" / "mappings"
    config_module.CONFIG_FILE = config_file
    
    import skill_hub.web.state as state_module
    state_module.REPOS_DIR = skill_hub.web.repos.REPOS_DIR

    yield tmp_path, claude, agents, cursor

    # Reset module state
    skill_hub.web.repos.SKILLS_REPO_ROOT = skill_hub.web.repos.SKILLS_REPO_ROOT
    skill_hub.web.repos.REPOS_YAML = skill_hub.web.repos.REPOS_YAML
    skill_hub.web.repos.REPOS_DIR = skill_hub.web.repos.REPOS_DIR
    skill_hub.web.repos.MAPPINGS_DIR = skill_hub.web.repos.MAPPINGS_DIR
    config_module.CONFIG_FILE = config_module.CONFIG_FILE
    state_module.REPOS_DIR = skill_hub.web.repos.REPOS_DIR
```

同时更新所有引用 `temp_home` 的测试函数以接收 4 个返回值：

```python
def test_get_skills_returns_list(client, temp_home):
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test-skill"
    # New format: dirStatus instead of status
    assert data[0]["dirStatus"]["claude"]["installed"] is False
    assert data[0]["dirStatus"]["agents"]["installed"] is False


def test_install_skill(client, temp_home):
    tmp_path, claude, agents, cursor = temp_home
    name = "test-skill"
    resp = client.post(f"/api/skills/{name}/install", data={}, content_type="application/json")
    assert resp.status_code == 200
    assert (claude / name).exists()
    assert (agents / name).exists()
    assert (cursor / name).exists()


def test_uninstall_skill(client, temp_home):
    tmp_path, claude, agents, cursor = temp_home
    name = "test-skill"
    client.post(f"/api/skills/{name}/install")
    resp = client.post(f"/api/skills/{name}/uninstall")
    assert resp.status_code == 200
    assert not (claude / name).exists()
    assert not (agents / name).exists()
    assert not (cursor / name).exists()
```

注意：需要更新 `tests/test_web.py` 中所有使用 `temp_home` 的函数签名。

### Step 5: 重构 state.py 数据模型

将 `src/skill_hub/web/state.py` 的核心部分替换：

```python
"""Skills state tracking — listing, status computation, install/uninstall."""

import hashlib
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

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
    
    @property
    def matches_source(self) -> bool:
        """Whether installed version matches source (requires external source_md5 comparison)."""
        return False  # Computed at SkillEntry level


@dataclass
class SkillEntry:
    name: str
    repo_name: str
    repo_url: str
    path: Path  # absolute path in the cloned repo
    dir_status: dict[str, DirStatus] = field(default_factory=dict)
    conflict: bool = False  # True if another repo provides the same skill name
    source_md5: str = ""  # MD5 of source skill in repo

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
```

### Step 6: 重构扫描和安装逻辑

替换 `state.py` 中的扫描函数：

```python
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
    for repo, skill_name, skill_path in entries:
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
        
        method_str = f" ({method})" if method == "symlink" else ""
        return True, f"Installed {name} to {', '.join(installed_to)}{method_str}"
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
```

Run: `pytest tests/test_web.py -v -k "test_get_skills_returns_list or test_install_skill or test_uninstall_skill"`
Expected: PASS

### Step 7: Commit

```bash
git add src/skill_hub/web/state.py tests/test_web.py
git commit -m "refactor: support dynamic install directories in state module"
```

---

## Task 3: 更新 API 接口

**Files:**
- Modify: `src/skill_hub/web/api.py`
- Test: `tests/test_web.py` (更新 API 测试)

### Step 8: 更新 /api/skills 返回格式

修改 `api.py` 中的 `get_skills()` 函数：

```python
@api_bp.route("/skills", methods=["GET"])
def get_skills():
    """List all skills with their installation status across all directories."""
    from skill_hub.web.config import get_install_dirs
    
    skills = list_skills()
    install_dirs = get_install_dirs()
    
    return jsonify([
        {
            "name": s.name,
            "repoName": s.repo_name,
            "repoUrl": s.repo_url,
            "status": s.status,
            "dirStatus": {
                label: {
                    "installed": ds.installed,
                    "matchesSource": ds.installed and ds.md5 == s.source_md5,
                    "isSymlink": ds.is_symlink,
                    "md5": ds.md5,
                }
                for label, ds in s.dir_status.items()
            },
            # Legacy fields for backward compatibility during transition
            "inClaude": s.in_claude,
            "inAgents": s.in_agents,
            "claudeMatchesSource": s.claude_matches_source,
            "agentsMatchesSource": s.agents_matches_source,
            "linkClaude": s.link_claude,
            "linkAgents": s.link_agents,
            "md5Source": s.source_md5,
            "path": str(s.path),
            "conflict": s.conflict,
        }
        for s in skills
    ])
```

### Step 9: 更新 /api/skills/<name>/install-to 支持任意目录

```python
@api_bp.route("/skills/<name>/install-to", methods=["POST"])
def api_install_to(name: str):
    """Install a skill to a single directory by label."""
    from skill_hub.web.config import get_install_dirs
    
    body = request.get_json(silent=True) or {}
    target_label = body.get("target", "").strip()
    method = body.get("method", "copy")
    
    if method not in ("copy", "symlink"):
        return jsonify({"error": "method must be 'copy' or 'symlink'"}), 400
    
    # Validate target label exists
    install_dirs = get_install_dirs()
    valid_labels = {d.label for d in install_dirs}
    if target_label not in valid_labels:
        return jsonify({"error": f"target must be one of: {', '.join(valid_labels)}"}), 400

    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_to_one(name, source_path, target_label, method=method)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500
```

### Step 10: 新增安装目录管理 API

在 `api.py` 末尾添加：

```python
@api_bp.route("/install-dirs", methods=["GET"])
def get_install_dirs_api():
    """List all configured install directories."""
    from skill_hub.web.config import get_install_dirs
    
    dirs = get_install_dirs()
    return jsonify([
        {
            "path": d.path,
            "label": d.label,
            "isDefault": d.is_default,
            "abbreviation": d.abbreviation,
            "resolvedPath": str(d.resolved_path),
        }
        for d in dirs
    ])


@api_bp.route("/install-dirs", methods=["POST"])
def add_install_dir_api():
    """Add a new install directory."""
    from skill_hub.web.config import add_install_dir
    
    body = request.get_json(silent=True) or {}
    path = body.get("path", "").strip()
    
    if not path:
        return jsonify({"error": "path is required"}), 400
    
    try:
        new_dir = add_install_dir(path)
        return jsonify({
            "ok": True,
            "dir": {
                "path": new_dir.path,
                "label": new_dir.label,
                "abbreviation": new_dir.abbreviation,
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/install-dirs/<label>", methods=["DELETE"])
def remove_install_dir_api(label: str):
    """Remove an install directory by label."""
    from skill_hub.web.config import remove_install_dir
    
    try:
        remove_install_dir(label)
        return jsonify({"ok": True, "message": f"Removed directory '{label}'"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
```

### Step 11: 更新测试并验证

修改 `tests/test_web.py` 中的 API 测试以匹配新格式：

```python
def test_install_to_single_dir(client, temp_home):
    tmp_path, claude, agents, cursor = temp_home
    name = "test-skill"
    
    # Install to cursor only
    resp = client.post(
        f"/api/skills/{name}/install-to",
        data=json.dumps({"target": "cursor", "method": "copy"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert not (claude / name).exists()
    assert not (agents / name).exists()
    assert (cursor / name).exists()


def test_get_install_dirs(client, temp_home):
    resp = client.get("/api/install-dirs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 3
    labels = [d["label"] for d in data]
    assert "claude" in labels
    assert "agents" in labels
    assert "cursor" in labels


def test_add_and_remove_install_dir(client, temp_home):
    tmp_path, claude, agents, cursor = temp_home
    
    # Add custom dir
    custom = tmp_path / "custom" / "skills"
    custom.mkdir(parents=True)
    
    resp = client.post(
        "/api/install-dirs",
        data=json.dumps({"path": str(custom)}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["dir"]["label"] == "custom"
    
    # Verify it's in the list
    resp = client.get("/api/install-dirs")
    labels = [d["label"] for d in resp.get_json()]
    assert "custom" in labels
    
    # Remove it
    resp = client.delete("/api/install-dirs/custom")
    assert resp.status_code == 200
    
    # Verify removed
    resp = client.get("/api/install-dirs")
    labels = [d["label"] for d in resp.get_json()]
    assert "custom" not in labels


def test_cannot_remove_default_dir(client, temp_home):
    resp = client.delete("/api/install-dirs/claude")
    assert resp.status_code == 400
    assert "Cannot remove default" in resp.get_json()["error"]
```

Run: `pytest tests/test_web.py -v`
Expected: PASS

### Step 12: Commit

```bash
git add src/skill_hub/web/api.py tests/test_web.py
git commit -m "feat: update API for dynamic install directories"
```

---

## Task 4: 前端界面改造

**Files:**
- Modify: `src/skill_hub/web/templates/index.html`
- Modify: `src/skill_hub/web/app.py` (如有需要传递 installDirs)

### Step 13: 更新 HTML 结构

修改 `index.html` 的设置面板部分，在现有设置菜单中增加"安装目录"区块：

找到：
```html
<div id="settings-menu" class="hidden absolute right-0 mt-1 w-64 bg-white border border-gray-300 rounded-lg shadow-lg z-50 text-sm p-3">
  <div class="mb-3">
    <label class="block text-xs text-gray-500 mb-1" id="scan-interval-label"></label>
    <div class="flex items-center gap-2">
      <input type="number" id="scan-interval" min="1" max="1440" class="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
      <span class="text-xs text-gray-500" id="scan-interval-unit"></span>
    </div>
  </div>
  <button onclick="saveSettings()" class="w-full px-3 py-1.5 rounded border border-green-600 text-green-700 text-xs hover:bg-green-50 cursor-pointer" id="btn-save-settings"></button>
</div>
```

替换为：
```html
<div id="settings-menu" class="hidden absolute right-0 mt-1 w-80 bg-white border border-gray-300 rounded-lg shadow-lg z-50 text-sm p-3">
  <!-- Install Directories -->
  <div class="mb-4">
    <div class="flex items-center justify-between mb-2">
      <label class="text-xs font-semibold text-gray-700" id="install-dirs-label">安装目录</label>
    </div>
    <div id="install-dirs-list" class="space-y-1 mb-2 max-h-40 overflow-y-auto"></div>
    <div class="flex gap-2">
      <input type="text" id="new-install-dir" placeholder="~/.custom/skills" 
        class="flex-1 px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-400">
      <button onclick="addInstallDir()" class="px-2 py-1 rounded border border-green-600 text-green-700 text-xs hover:bg-green-50 cursor-pointer">+</button>
    </div>
    <div id="install-dir-error" class="hidden mt-1 text-xs text-red-600"></div>
  </div>
  
  <hr class="border-gray-200 my-3">
  
  <!-- Scan Interval -->
  <div class="mb-3">
    <label class="block text-xs text-gray-500 mb-1" id="scan-interval-label"></label>
    <div class="flex items-center gap-2">
      <input type="number" id="scan-interval" min="1" max="1440" class="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
      <span class="text-xs text-gray-500" id="scan-interval-unit"></span>
    </div>
  </div>
  <button onclick="saveSettings()" class="w-full px-3 py-1.5 rounded border border-green-600 text-green-700 text-xs hover:bg-green-50 cursor-pointer" id="btn-save-settings"></button>
</div>
```

### Step 14: 添加 i18n 文本

在 `i18n.zh` 和 `i18n.en` 中添加：

```javascript
// 在 zh 对象中添加
installDirs: '安装目录',
addDir: '添加',
dirExists: '目录已存在',
dirAdded: '目录添加成功',
dirRemoved: '目录已删除',
cannotRemoveDefault: '不能删除默认目录',
dirNotFound: '目录未找到',

// 在 en 对象中添加
installDirs: 'Install Directories',
addDir: 'Add',
dirExists: 'Directory already exists',
dirAdded: 'Directory added',
dirRemoved: 'Directory removed',
cannotRemoveDefault: 'Cannot remove default directory',
dirNotFound: 'Directory not found',
```

### Step 15: 添加安装目录管理函数

在 `<script>` 标签内添加：

```javascript
// Install directory management
let installDirs = [];

async function loadInstallDirs() {
  try {
    const resp = await fetch('/api/install-dirs');
    if (!resp.ok) return;
    installDirs = await resp.json();
    renderInstallDirs();
  } catch (e) {}
}

function renderInstallDirs() {
  const container = document.getElementById('install-dirs-list');
  if (!container) return;
  
  let html = '';
  for (const dir of installDirs) {
    const isDefault = dir.isDefault;
    const deleteBtn = isDefault 
      ? `<span class="text-gray-300 text-xs">默认</span>`
      : `<button onclick="removeInstallDir('${escAttr(dir.label)}')" class="text-red-500 hover:text-red-700 text-xs cursor-pointer bg-transparent border-0">✕</button>`;
    
    html += `<div class="flex items-center justify-between px-2 py-1.5 bg-gray-50 rounded text-xs">
      <div class="flex items-center gap-2 min-w-0">
        <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">${escHtml(dir.abbreviation)}</span>
        <span class="truncate text-gray-700" title="${escAttr(dir.path)}">${escHtml(dir.path)}</span>
      </div>
      ${deleteBtn}
    </div>`;
  }
  container.innerHTML = html;
}

async function addInstallDir() {
  const input = document.getElementById('new-install-dir');
  const path = input.value.trim();
  const errorEl = document.getElementById('install-dir-error');
  
  if (!path) return;
  
  try {
    const resp = await fetch('/api/install-dirs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await resp.json();
    if (resp.ok) {
      input.value = '';
      errorEl.classList.add('hidden');
      showToast(t('dirAdded'));
      await loadInstallDirs();
      await loadSkills(); // Refresh skills to show new dir status
    } else {
      errorEl.textContent = data.error || t('addFailed');
      errorEl.classList.remove('hidden');
    }
  } catch (e) {
    errorEl.textContent = t('addFailed');
    errorEl.classList.remove('hidden');
  }
}

async function removeInstallDir(label) {
  try {
    const resp = await fetch(`/api/install-dirs/${encodeURIComponent(label)}`, {
      method: 'DELETE',
    });
    const data = await resp.json();
    if (resp.ok) {
      showToast(t('dirRemoved'));
      await loadInstallDirs();
      await loadSkills();
    } else {
      showToast(data.error || t('deleteFailed'), 'error');
    }
  } catch (e) {
    showToast(t('deleteFailed'), 'error');
  }
}
```

### Step 16: 重构 Skill 列表渲染

修改 `renderSkills()` 函数，用圆点网格替代固定列：

```javascript
function renderSkills() {
  const container = document.getElementById('skills-container');

  if (!selectedRepo) {
    container.innerHTML = `<div class="text-gray-500 text-center py-10 text-sm">${t('noSkills')}</div>`;
    return;
  }

  const items = allSkills.filter(s => s.repoName === selectedRepo);
  const repoInfo = repoMeta[selectedRepo] || {};
  const isLocal = repoInfo.isLocal;
  const hasUpdate = repoInfo.hasRemoteUpdates;

  const dotCls = hasUpdate ? 'bg-yellow-400' : 'bg-green-600';
  const dotTitle = hasUpdate ? t('remoteUpdateAvailable') : (isLocal ? t('localPath') : t('syncedWithRemote'));
  const escapedRepo = selectedRepo.replace(/'/g, "\\'");
  const dotClick = hasUpdate ? `onclick="event.stopPropagation(); syncOneRepo('${escapedRepo}')" class="cursor-pointer"` : '';

  let html = `<div>
    <div class="flex items-center gap-2 px-3 py-2 bg-gray-200 rounded-md text-sm font-semibold mb-2">
      <span class="w-2.5 h-2.5 rounded-full ${dotCls}" title="${dotTitle}" ${dotClick}></span>
      <span class="truncate">${escHtml(selectedRepo)}</span>
      <span class="ml-auto flex gap-2">
        <button onclick="installAllSkills('${escapedRepo}')" class="text-xs text-green-700 hover:underline cursor-pointer bg-transparent border border-green-600 rounded px-2 py-0.5">${t('installAll')}</button>
        <button onclick="uninstallAllSkills('${escapedRepo}')" class="text-xs text-red-600 hover:underline cursor-pointer bg-transparent border border-red-500 rounded px-2 py-0.5">${t('uninstallAll')}</button>
        <button onclick="removeRepo('${escapedRepo}')" class="text-xs text-red-600 hover:underline cursor-pointer bg-transparent border-0 p-0.5">${t('deleteRepo')}</button>
      </span>
    </div>`;

  if (items.length === 0) {
    html += `<p class="text-gray-500 text-sm px-3 py-2">${t('noSkillsInRepo')}</p>`;
  } else {
    html += '<ul class="list-none pl-0">';
    for (const s of items) {
      const isInstalled = s.status === 'installed' || s.status === 'outdated';
      const escapedName = s.name.replace(/'/g, "\\'");
      
      // Build directory status dots
      let dirDots = '';
      const dirStatus = s.dirStatus || {};
      for (const dir of installDirs) {
        const ds = dirStatus[dir.label] || { installed: false, matchesSource: false, isSymlink: false };
        let dotColor, dotTitle, dotAction;
        
        if (ds.installed) {
          if (ds.matchesSource) {
            dotColor = 'bg-green-600';
            dotTitle = `${dir.path}: ${t('installedLatest')}${ds.isSymlink ? ' (symlink)' : ''}`;
          } else {
            dotColor = 'bg-yellow-400 cursor-pointer';
            dotTitle = `${dir.path}: ${t('clickToUpdate')}`;
            dotAction = `onclick="installToDir('${escapedName}', '${escAttr(dir.label)}')"`;
          }
        } else {
          dotColor = 'bg-gray-300';
          dotTitle = `${dir.path}: ${t('notInstalledTitle')}`;
        }
        
        const symlinkIcon = ds.isSymlink ? '<span class="absolute -bottom-0.5 -right-0.5 text-[8px] text-blue-500">🔗</span>' : '';
        
        dirDots += `<span class="relative inline-flex items-center justify-center w-5 h-5 rounded-full ${dotColor} text-white text-[10px] font-bold shrink-0 mr-1" title="${escAttr(dotTitle)}" ${dotAction || ''}>${escHtml(dir.abbreviation)}${symlinkIcon}</span>`;
      }

      const statusLabel = s.status === 'outdated' ? t('partial') : t(s.status);

      html += `<li class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 mb-1">
        <span class="flex-1 font-medium cursor-pointer hover:underline hover:text-blue-600" onclick="toggleMeta('${escapedName}', this)">${escHtml(s.name)}</span>
        <span class="flex items-center">${dirDots}</span>
        <span class="inline-block px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge(s.status)}">${statusLabel}</span>
        ${isInstalled
          ? `<button onclick="uninstallSkill('${escapedName}')" class="px-3 py-1 rounded border border-red-500 text-red-600 text-xs hover:bg-red-50 cursor-pointer">${t('uninstall')}</button>`
          : `<button onclick="installSkill('${escapedName}')" class="px-3 py-1 rounded border border-green-600 text-green-700 text-xs hover:bg-green-50 cursor-pointer">${t('install')}</button>`
        }
      </li>
      <div id="meta-${escapedName}" class="hidden bg-white border border-gray-300 rounded-lg p-4 mx-3 mb-2 text-sm leading-relaxed"></div>`;
    }
    html += '</ul>';
  }

  html += '</div>';
  container.innerHTML = html;
}

// New function for installing to a specific directory
async function installToDir(name, targetLabel) {
  if (!confirm(t('confirmUpdateTo', name, targetLabel))) return;
  const useSymlink = document.getElementById('use-symlink').checked;
  const resp = await fetch(`/api/skills/${encodeURIComponent(name)}/install-to`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target: targetLabel, method: useSymlink ? 'symlink' : 'copy' }),
  });
  const data = await resp.json();
  if (resp.ok) { showToast(data.message); await loadSkills(); }
  else { showToast(data.error || t('installFailed'), 'error'); }
}
```

### Step 17: 初始化时加载安装目录

在脚本初始化部分，添加 `loadInstallDirs()` 调用：

```javascript
// Background refresh to get latest state
loadSkills();
loadInstallDirs();  // <-- 新增
checkUpdateStatus();
checkAppVersion();
loadSettings();
```

### Step 18: 更新绑定静态按钮标签

添加：
```javascript
document.getElementById('install-dirs-label').textContent = t('installDirs');
```

### Step 19: 运行前端测试

由于前端是 Vanilla JS，通过运行 Web UI 测试验证：

```bash
# 启动测试服务器并运行现有测试
pytest tests/test_web.py -v
```

Expected: PASS

### Step 20: Commit

```bash
git add src/skill_hub/web/templates/index.html
git commit -m "feat: add dynamic install directory UI with abbreviation dots"
```

---

## Task 5: 更新初始数据传递和 App Factory

**Files:**
- Modify: `src/skill_hub/web/app.py`

### Step 21: 更新初始数据

修改 `app.py` 中的 `index()` 路由，传递安装目录信息：

```python
@web_bp.route("/")
def index():
    from skill_hub.web.config import get_install_dirs
    
    skills = list_skills()
    repos = load_repos_config()
    
    # Include install dirs in initial data
    install_dirs = get_install_dirs()
    
    initial_data = {
        "skills": [
            {
                "name": s.name,
                "repoName": s.repo_name,
                "repoUrl": s.repo_url,
                "status": s.status,
                "dirStatus": {
                    label: {
                        "installed": ds.installed,
                        "matchesSource": ds.installed and ds.md5 == s.source_md5,
                        "isSymlink": ds.is_symlink,
                    }
                    for label, ds in s.dir_status.items()
                },
            }
            for s in skills
        ],
        "repos": [
            {
                "name": r.name,
                "hasRemoteUpdates": has_remote_updates(r) if not r.is_local else False,
                "isLocal": r.is_local,
                "isCloned": repo_dir(r).exists() and (repo_dir(r) / ".git").exists(),
            }
            for r in repos
        ],
        "installDirs": [
            {
                "path": d.path,
                "label": d.label,
                "abbreviation": d.abbreviation,
                "isDefault": d.is_default,
            }
            for d in install_dirs
        ],
    }
    return render_template(
        "index.html",
        initial_data=initial_data,
        current_version=__version__,
    )
```

### Step 22: 前端使用初始数据

在 `<script>` 中更新初始数据处理：

```javascript
// Instant first paint from server-injected data
if (__INITIAL_DATA__) {
    allSkills = __INITIAL_DATA__.skills || [];
    installDirs = __INITIAL_DATA__.installDirs || [];  // <-- 新增
    for (const r of __INITIAL_DATA__.repos || []) {
        repoMeta[r.name] = { hasRemoteUpdates: r.hasRemoteUpdates, isLocal: r.isLocal, isCloned: r.isCloned };
    }
    const repoNames = [...new Set(allSkills.map(s => s.repoName))];
    const allRepoNames = [...new Set([...repoNames, ...Object.keys(repoMeta)])];
    if (selectedRepo && !allRepoNames.includes(selectedRepo)) selectedRepo = null;
    if (!selectedRepo && allRepoNames.length > 0) selectedRepo = allRepoNames[0];
    renderSidebar();
    renderSkills();
    renderInstallDirs();  // <-- 新增
}
```

### Step 23: 运行完整测试

```bash
pytest tests/ -v
```

Expected: 全部 PASS

### Step 24: Commit

```bash
git add src/skill_hub/web/app.py src/skill_hub/web/templates/index.html
git commit -m "feat: pass install dirs via initial data and render on load"
```

---

## 自检清单

### Spec 覆盖检查

| Spec 需求 | 实现任务 |
|-----------|----------|
| 用户可添加自定义安装目录 | Task 1 (config.py), Task 3 (API), Task 4 (UI) |
| 用户可删除自定义目录 | Task 1 (config.py), Task 3 (API), Task 4 (UI) |
| 默认目录不可删除 | Task 1 (remove_install_dir), Task 3 (测试) |
| 配置持久化到 config.json | Task 1 (config.py) |
| SkillEntry 改为动态 dir_status | Task 2 (state.py) |
| 首字母缩写自动生成 | Task 1 (_generate_abbreviation) |
| 圆点显示首字母 | Task 4 (renderSkills) |
| 圆点颜色状态（绿/黄/灰） | Task 4 (renderSkills) |
| Symlink 标识 | Task 4 (symlinkIcon) |
| Hover tooltip | Task 4 (title 属性) |
| 一键安装/卸载所有目录 | Task 2 (install_skill, uninstall_skill) |
| 单独目录安装 | Task 2 (install_to_one), Task 3 (API), Task 4 (installToDir) |
| 后端 API 更新 | Task 3 (api.py) |
| 前端界面更新 | Task 4 (index.html) |
| 测试覆盖 | 所有 Tasks |

### Placeholder 扫描

- [x] 无 "TBD", "TODO", "implement later"
- [x] 无 "Add appropriate error handling" 等模糊描述
- [x] 所有步骤包含实际代码
- [x] 所有文件路径准确

### 类型一致性

- [x] `InstallDir` 在 Task 1 和 Task 3 中定义一致
- [x] `DirStatus` 在 Task 2 中定义，在 Task 4 中使用一致
- [x] API 响应字段名前后一致 (`dirStatus`, `matchesSource`, `isSymlink`)
- [x] 函数签名一致 (`install_to_one` 参数为 `target_label`)

---

## 实现后验证

启动 Web UI 进行手动验证：

```bash
skill-hub web
```

验证清单：
1. [ ] 设置菜单显示"安装目录"列表
2. [ ] 添加新目录后，skill 列表出现新圆点
3. [ ] 圆点显示正确的首字母缩写
4. [ ] 绿色圆点 = 已安装且匹配源
5. [ ] 黄色圆点 = 已安装但不同步，点击可更新
6. [ ] 灰色圆点 = 未安装
7. [ ] 悬停圆点显示 tooltip
8. [ ] "安装"按钮安装到所有目录
9. [ ] "卸载"按钮从所有目录卸载
10. [ ] 不能删除默认目录
11. [ ] 删除自定义目录后圆点消失
