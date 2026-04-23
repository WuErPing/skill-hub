"""Background scheduler for periodic repository sync checks."""

import json
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from skill_hub.web.repos import load_repos_config, has_remote_updates, sync_mapping, repo_dir, Repo

SETTINGS_FILE = Path.home() / ".skills_repo" / "settings.json"
DEFAULT_SCAN_INTERVAL_MINUTES = 30


@dataclass
class RepoStatus:
    has_updates: bool
    last_checked: float
    error: Optional[str] = None


class RepoScheduler:
    """Singleton scheduler that periodically checks remote repos for updates."""

    _instance: Optional["RepoScheduler"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RepoScheduler":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._scan_interval = self._load_settings().get("scan_interval_minutes", DEFAULT_SCAN_INTERVAL_MINUTES)
        self._status_cache: dict[str, RepoStatus] = {}
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._cache_lock = threading.Lock()

    def _load_settings(self) -> dict:
        if SETTINGS_FILE.exists():
            try:
                return json.loads(SETTINGS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_settings(self) -> None:
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            settings = {"scan_interval_minutes": self._scan_interval}
            SETTINGS_FILE.write_text(json.dumps(settings))
        except OSError:
            pass

    @property
    def scan_interval(self) -> int:
        return self._scan_interval

    @scan_interval.setter
    def scan_interval(self, minutes: int) -> None:
        if minutes < 1:
            minutes = 1
        self._scan_interval = minutes
        self._save_settings()
        # Restart scheduler with new interval if running
        if self._running:
            self.stop()
            self.start()

    def get_status(self, repo_name: str) -> Optional[RepoStatus]:
        with self._cache_lock:
            return self._status_cache.get(repo_name)

    def get_all_statuses(self) -> dict[str, RepoStatus]:
        with self._cache_lock:
            return dict(self._status_cache)

    def check_now(self) -> None:
        """Run a single check cycle immediately. Clone uncloned repos first."""
        repos = load_repos_config()
        new_status: dict[str, RepoStatus] = {}
        for repo in repos:
            if repo.is_local:
                new_status[repo.name] = RepoStatus(
                    has_updates=False,
                    last_checked=time.time(),
                )
                continue
            target = repo_dir(repo)
            if not target.exists():
                # Repo not cloned yet — clone it now
                try:
                    ok, msg = sync_mapping(repo)
                    if ok:
                        new_status[repo.name] = RepoStatus(
                            has_updates=False,
                            last_checked=time.time(),
                        )
                    else:
                        new_status[repo.name] = RepoStatus(
                            has_updates=False,
                            last_checked=time.time(),
                            error=msg,
                        )
                except Exception as e:
                    new_status[repo.name] = RepoStatus(
                        has_updates=False,
                        last_checked=time.time(),
                        error=str(e),
                    )
                continue
            # Repo exists — check for remote updates
            try:
                has_updates = has_remote_updates(repo)
                new_status[repo.name] = RepoStatus(
                    has_updates=has_updates,
                    last_checked=time.time(),
                )
            except Exception as e:
                new_status[repo.name] = RepoStatus(
                    has_updates=False,
                    last_checked=time.time(),
                    error=str(e),
                )
        with self._cache_lock:
            self._status_cache = new_status

    def _run_check(self) -> None:
        """Execute check and schedule next run."""
        if not self._running:
            return
        try:
            self.check_now()
        finally:
            # Schedule next run
            if self._running:
                self._schedule_next()

    def _schedule_next(self) -> None:
        """Schedule the next check."""
        interval_seconds = self._scan_interval * 60
        self._timer = threading.Timer(interval_seconds, self._run_check)
        self._timer.daemon = True
        self._timer.start()

    def start(self) -> None:
        """Start the scheduler. Runs first check immediately."""
        if self._running:
            return
        self._running = True
        # Run first check immediately in a separate thread
        threading.Thread(target=self._run_check, daemon=True).start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def is_running(self) -> bool:
        return self._running


# Global scheduler instance
scheduler = RepoScheduler()
