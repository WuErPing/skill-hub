"""Tests for repo intro module."""

import json
from pathlib import Path

from skill_hub.web.intro import (
    RepoIntro,
    generate_prompt,
    get_intro_cache_path,
    load_intro,
    read_repo_readme,
    save_intro,
)


def test_get_intro_cache_path():
    path = get_intro_cache_path("anthropics/skills")
    assert "anthropics__skills" in str(path)
    assert str(path).endswith(".json")


def test_repo_intro_defaults():
    intro = RepoIntro(repo_name="test/repo")
    assert intro.repo_name == "test/repo"
    assert intro.cached is False
    assert intro.summary == {}
    assert intro.authors == []


def test_read_repo_readme(tmp_path):
    # Test README.md exists
    readme = tmp_path / "README.md"
    readme.write_text("# Test Repo\n\nThis is a test.")
    content = read_repo_readme(tmp_path)
    assert content == "# Test Repo\n\nThis is a test."
    
    # Test Readme.md (different case)
    tmp_path2 = tmp_path / "subdir"
    tmp_path2.mkdir()
    readme2 = tmp_path2 / "Readme.md"
    readme2.write_text("# Another")
    content2 = read_repo_readme(tmp_path2)
    assert content2 == "# Another"
    
    # Test no README
    tmp_path3 = tmp_path / "empty"
    tmp_path3.mkdir()
    content3 = read_repo_readme(tmp_path3)
    assert content3 is None


def test_generate_prompt():
    prompt = generate_prompt("test/repo", "# Test\n\nThis is a test README.")
    data = json.loads(prompt)
    assert data["repo_name"] == "test/repo"
    assert "task" in data
    assert "output_format" in data
    assert "purpose" in data["output_format"]
    assert "features" in data["output_format"]


def test_load_save_intro(tmp_path):
    # Setup
    readme = tmp_path / "README.md"
    readme.write_text("# Test")
    
    # Compute actual md5
    import hashlib
    actual_md5 = hashlib.md5(readme.read_bytes()).hexdigest()
    
    intro = RepoIntro(
        repo_name="test/repo",
        summary={"purpose": "Test purpose", "features": ["feat1"]},
        cached=True,
        readme_md5=actual_md5,
    )
    
    # Save
    save_intro(intro)
    
    # Load (should match)
    loaded = load_intro("test/repo", readme)
    assert loaded.cached is True
    assert loaded.summary["purpose"] == "Test purpose"
    
    # Modify README - cache should be invalid
    readme.write_text("# Modified")
    loaded2 = load_intro("test/repo", readme)
    assert loaded2.cached is False


def test_load_intro_no_cache():
    # Test loading when no cache exists
    tmp_path = Path("/tmp/nonexistent_readme")
    intro = load_intro("no/cache", tmp_path)
    assert intro.cached is False
    assert intro.repo_name == "no/cache"
