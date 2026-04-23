"""Tests for scheduler module."""

import pytest
from skill_hub.web.scheduler import RepoScheduler, DEFAULT_SCAN_INTERVAL_MINUTES


@pytest.fixture
def fresh_scheduler(monkeypatch, tmp_path):
    """Provide a fresh scheduler instance for each test."""
    # Use temp settings file to avoid conflicts with other tests
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(
        'skill_hub.web.scheduler.SETTINGS_FILE',
        settings_file
    )
    # Reset singleton
    monkeypatch.setattr(RepoScheduler, '_instance', None)
    scheduler = RepoScheduler()
    scheduler.stop()
    yield scheduler
    scheduler.stop()


class TestRepoScheduler:
    def test_default_interval(self, fresh_scheduler):
        assert fresh_scheduler.scan_interval == DEFAULT_SCAN_INTERVAL_MINUTES

    def test_set_interval(self, fresh_scheduler):
        fresh_scheduler.scan_interval = 60
        assert fresh_scheduler.scan_interval == 60

    def test_set_interval_minimum(self, fresh_scheduler):
        fresh_scheduler.scan_interval = 0
        assert fresh_scheduler.scan_interval == 1

    def test_start_stop(self, fresh_scheduler):
        assert not fresh_scheduler.is_running()
        fresh_scheduler.start()
        assert fresh_scheduler.is_running()
        fresh_scheduler.stop()
        assert not fresh_scheduler.is_running()

    def test_check_now_updates_cache(self, fresh_scheduler, tmp_path, monkeypatch):
        # Mock load_repos_config to return a test repo
        from skill_hub.web.repos import Repo
        test_repo = Repo(url="https://github.com/test/repo", branch="main")
        monkeypatch.setattr(
            'skill_hub.web.scheduler.load_repos_config',
            lambda: [test_repo]
        )
        # Mock has_remote_updates to return True
        monkeypatch.setattr(
            'skill_hub.web.scheduler.has_remote_updates',
            lambda repo: True
        )
        
        fresh_scheduler.check_now()
        
        status = fresh_scheduler.get_status("test/repo")
        assert status is not None
        assert status.has_updates is True
        assert status.error is None

    def test_get_all_statuses(self, fresh_scheduler, monkeypatch):
        from skill_hub.web.repos import Repo
        test_repo = Repo(url="https://github.com/test/repo", branch="main")
        monkeypatch.setattr(
            'skill_hub.web.scheduler.load_repos_config',
            lambda: [test_repo]
        )
        monkeypatch.setattr(
            'skill_hub.web.scheduler.has_remote_updates',
            lambda repo: False
        )
        
        fresh_scheduler.check_now()
        
        statuses = fresh_scheduler.get_all_statuses()
        assert "test/repo" in statuses
        assert statuses["test/repo"].has_updates is False

    def test_settings_persistence(self, fresh_scheduler, tmp_path, monkeypatch):
        # Use temp settings file
        settings_file = tmp_path / "settings.json"
        monkeypatch.setattr(
            'skill_hub.web.scheduler.SETTINGS_FILE',
            settings_file
        )
        
        fresh_scheduler.scan_interval = 45
        
        # Create new scheduler instance to test loading
        monkeypatch.setattr(RepoScheduler, '_instance', None)
        new_scheduler = RepoScheduler()
        assert new_scheduler.scan_interval == 45
        new_scheduler.stop()
