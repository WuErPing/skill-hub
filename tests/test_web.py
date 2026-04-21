"""Integration tests for skill-hub web module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.web.app import create_app
from skill_hub.web.repos import Repo


@pytest.fixture
def temp_home(tmp_path):
    """Create a temp home directory with fake skills dirs."""
    # New structure: repos/ is the full git clone, mappings/ tracks skill locations
    repo_clone = tmp_path / "skills_repo" / "repos" / "example__repo"
    repo_clone.mkdir(parents=True)
    (repo_clone / "test-skill").mkdir()
    (repo_clone / "test-skill" / "SKILL.md").write_text("---\nname: test-skill\ndescription: Test\n---\n\nTest body")

    mapping_file = tmp_path / "skills_repo" / "mappings" / "example__repo.yaml"
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    mapping_file.write_text("test-skill: test-skill\n")

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
    skill_hub.web.repos.REPOS_DIR = tmp_path / "skills_repo" / "repos"
    skill_hub.web.repos.MAPPINGS_DIR = tmp_path / "skills_repo" / "mappings"
    import skill_hub.web.state as state_module
    state_module.REPOS_DIR = tmp_path / "skills_repo" / "repos"
    skill_hub.web.state.CLAUDE_SKILLS = claude
    skill_hub.web.state.AGENTS_SKILLS = agents

    yield tmp_path, claude, agents

    # Reset module state
    skill_hub.web.repos.SKILLS_REPO_ROOT = skill_hub.web.repos.SKILLS_REPO_ROOT
    skill_hub.web.repos.REPOS_YAML = skill_hub.web.repos.REPOS_YAML
    skill_hub.web.repos.REPOS_DIR = skill_hub.web.repos.REPOS_DIR
    skill_hub.web.repos.MAPPINGS_DIR = skill_hub.web.repos.MAPPINGS_DIR
    state_module.REPOS_DIR = skill_hub.web.repos.REPOS_DIR


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
    assert data[0]["status"] == "not_installed"


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


def test_add_existing_repo_does_not_error(client, temp_home):
    """Adding a repo URL that already exists should re-sync, not reject."""
    resp = client.post("/api/repos",
        json={"url": "https://github.com/example/repo", "branch": "main"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["ok"] is True
    # Repos should still list only one entry
    repos_resp = client.get("/api/repos")
    repos = repos_resp.get_json()
    assert len(repos) == 1


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
    assert skill["status"] == "installed"


def test_delete_nonexistent_repo_returns_404(client, temp_home):
    resp = client.delete("/api/repos/nonexistent/repo")
    assert resp.status_code == 404


def test_install_nonexistent_skill_returns_404(client, temp_home):
    resp = client.post("/api/skills/nonexistent/install")
    assert resp.status_code == 404


class TestRepoLocalDetection:
    """Unit tests for Repo.is_local property."""

    def test_https_url_is_not_local(self):
        repo = Repo(url="https://github.com/user/repo")
        assert repo.is_local is False

    def test_git_at_url_is_not_local(self):
        repo = Repo(url="git@github.com:user/repo.git")
        assert repo.is_local is False

    def test_absolute_path_is_local(self):
        repo = Repo(url="/home/user/my-skills")
        assert repo.is_local is True

    def test_tilde_path_is_local(self):
        repo = Repo(url="~/code/skills")
        assert repo.is_local is True

    def test_relative_path_is_local(self):
        repo = Repo(url="./my-skills")
        assert repo.is_local is True

    def test_name_derivation_for_short_path(self):
        repo = Repo(url="my-skill")
        assert repo.name == "my-skill"


def test_sync_repos_returns_results(client, temp_home):
    resp = client.post("/api/repos/sync")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "results" in data


def test_add_local_repo_path(client, temp_home):
    """Adding a local directory as repo source should scan skills without cloning."""
    tmp_path, claude, agents = temp_home
    local_repo = tmp_path / "local_skills"
    local_repo.mkdir()
    (local_repo / "my-skill").mkdir()
    (local_repo / "my-skill" / "SKILL.md").write_text("---\nname: my-skill\ndescription: Local\n---\n")

    resp = client.post("/api/repos",
        json={"url": str(local_repo)},
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["ok"] is True
    assert "Scanned" in data["message"]

    # Should appear in repos list with isLocal=true
    repos_resp = client.get("/api/repos")
    repos = repos_resp.get_json()
    local_repos = [r for r in repos if r.get("isLocal")]
    assert len(local_repos) >= 1
    assert str(local_repo) in local_repos[0]["localPath"]

    # Skill should be listed
    skills_resp = client.get("/api/skills")
    skills = skills_resp.get_json()
    skill_names = [s["name"] for s in skills]
    assert "my-skill" in skill_names


def test_delete_local_repo_does_not_remove_source(client, temp_home):
    """Deleting a local repo should only remove the mapping, not the source directory."""
    tmp_path, claude, agents = temp_home
    local_repo = tmp_path / "local_skills"
    local_repo.mkdir()
    (local_repo / "my-skill").mkdir()
    (local_repo / "my-skill" / "SKILL.md").write_text("---\nname: my-skill\ndescription: Local\n---\n")

    client.post("/api/repos", json={"url": str(local_repo)}, content_type="application/json")

    # Find the repo name
    repos = client.get("/api/repos").get_json()
    local_repo_entry = next(r for r in repos if r.get("isLocal"))
    repo_name = local_repo_entry["name"]

    resp = client.delete(f"/api/repos/{repo_name}")
    assert resp.status_code == 200

    # Source directory must still exist
    assert local_repo.exists()
    # Mapping file should be gone
    import skill_hub.web.repos as repos_module
    from skill_hub.web.repos import Repo
    repo = Repo(url=str(local_repo))
    assert not repos_module.mapping_path(repo).exists()
