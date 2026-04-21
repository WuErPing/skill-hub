"""Integration tests for skill-hub web module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.web.app import create_app


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

    import skill_hub.web.repos
    import skill_hub.web.state
    skill_hub.web.repos.SKILLS_REPO_ROOT = tmp_path / "skills_repo"
    skill_hub.web.repos.REPOS_YAML = repos_yaml
    skill_hub.web.repos.SKILLS_DIR = tmp_path / "skills_repo" / "skills"
    # state.py imports SKILLS_DIR directly, so patch its local binding too
    import skill_hub.web.state as state_module
    state_module.SKILLS_DIR = tmp_path / "skills_repo" / "skills"
    skill_hub.web.state.CLAUDE_SKILLS = claude
    skill_hub.web.state.AGENTS_SKILLS = agents

    yield tmp_path, claude, agents

    # Reset module state
    skill_hub.web.repos.SKILLS_REPO_ROOT = skill_hub.web.repos.SKILLS_REPO_ROOT
    skill_hub.web.repos.REPOS_YAML = skill_hub.web.repos.REPOS_YAML
    skill_hub.web.repos.SKILLS_DIR = skill_hub.web.repos.SKILLS_DIR
    state_module.SKILLS_DIR = skill_hub.web.repos.SKILLS_DIR


@pytest.fixture
def client(temp_home):
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
    client.post(f"/api/skills/{name}/install")
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


def test_add_repo_returns_409_if_exists(client, temp_home):
    resp = client.post("/api/repos",
        json={"url": "https://github.com/example/repo", "branch": "main"},
        content_type="application/json",
    )
    assert resp.status_code == 409
    data = resp.get_json()
    assert "already exists" in data["error"]


def test_update_status_returns_boolean(client, temp_home):
    resp = client.get("/api/update-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "hasUpdates" in data
    assert isinstance(data["hasUpdates"], bool)


def test_install_then_status_shows_installed(client, temp_home):
    name = "test-skill"
    client.post(f"/api/skills/{name}/install")
    resp = client.get("/api/skills")
    data = resp.get_json()
    skill = next(s for s in data if s["name"] == name)
    assert skill["status"] == "已安装"


def test_delete_nonexistent_repo_returns_404(client, temp_home):
    resp = client.delete("/api/repos/nonexistent/repo")
    assert resp.status_code == 404


def test_install_nonexistent_skill_returns_404(client, temp_home):
    resp = client.post("/api/skills/nonexistent/install")
    assert resp.status_code == 404


def test_sync_repos_returns_results(client, temp_home):
    resp = client.post("/api/repos/sync")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "results" in data
