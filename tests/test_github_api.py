"""Tests for GitHub API wrapper."""

from skill_hub.web.github_api import Author, fetch_repo_authors


def test_author_dataclass():
    author = Author(
        username="testuser",
        name="Test User",
        bio="A test bio",
        avatar_url="https://example.com/avatar.png",
        profile_url="https://github.com/testuser",
        role="owner",
        contributions=0,
    )
    assert author.username == "testuser"
    assert author.name == "Test User"
    assert author.role == "owner"
    assert author.contributions == 0


def test_fetch_repo_authors_non_github():
    """Should return empty list for non-GitHub URLs."""
    result = fetch_repo_authors("https://gitlab.com/user/repo")
    assert result == []


def test_fetch_repo_authors_local_path():
    """Should return empty list for local paths."""
    result = fetch_repo_authors("~/local/repo")
    assert result == []
