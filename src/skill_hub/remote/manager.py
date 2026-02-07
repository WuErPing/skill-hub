"""Repository manager for cloning and updating remote Git repositories."""

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from skill_hub.models import RepositoryConfig, RepositoryMetadata
from skill_hub.utils import ensure_directory, expand_home

logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manages remote Git repositories."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize repository manager.

        Args:
            cache_dir: Directory to store cloned repositories (default: ~/.agents/skills/.skill-hub/repos)
        """
        if cache_dir is None:
            cache_dir = expand_home("~/.agents/skills/.skill-hub/repos")
        self.cache_dir = cache_dir
        ensure_directory(cache_dir)

    def _get_repo_hash(self, url: str) -> str:
        """
        Compute hash for repository URL.

        Args:
            url: Repository URL

        Returns:
            SHA-256 hash of URL (first 16 chars)
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _get_repo_dir(self, url: str) -> Path:
        """
        Get local directory for repository.

        Args:
            url: Repository URL

        Returns:
            Path to repository directory
        """
        repo_hash = self._get_repo_hash(url)
        return self.cache_dir / repo_hash

    def _get_metadata_file(self, url: str) -> Path:
        """
        Get metadata file path for repository.

        Args:
            url: Repository URL

        Returns:
            Path to meta.json file
        """
        return self._get_repo_dir(url) / "meta.json"

    def clone_or_update(self, config: RepositoryConfig) -> bool:
        """
        Clone repository if not exists, otherwise update it.

        Args:
            config: Repository configuration

        Returns:
            True if successful, False otherwise
        """
        repo_dir = self._get_repo_dir(config.url)

        try:
            if repo_dir.exists() and (repo_dir / ".git").exists():
                return self._update_repository(config, repo_dir)
            else:
                return self._clone_repository(config, repo_dir)
        except Exception as e:
            logger.error(f"Error syncing repository {config.url}: {e}")
            self._save_metadata_error(config.url, str(e))
            return False

    def _clone_repository(self, config: RepositoryConfig, repo_dir: Path) -> bool:
        """
        Clone repository with shallow clone.

        Args:
            config: Repository configuration
            repo_dir: Target directory

        Returns:
            True if successful
        """
        logger.info(f"Cloning repository {config.url}...")

        # Ensure parent directory exists
        ensure_directory(repo_dir.parent)

        # Build clone command
        cmd = ["git", "clone", "--depth", "1", "--branch", config.branch, config.url, str(repo_dir)]

        # Add authentication if token is available
        env = self._get_git_env()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env,
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return False

            logger.info(f"Successfully cloned {config.url}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Clone timeout for {config.url}")
            return False
        except FileNotFoundError:
            logger.error("Git executable not found. Please install Git.")
            return False

    def _update_repository(self, config: RepositoryConfig, repo_dir: Path) -> bool:
        """
        Update existing repository.

        Args:
            config: Repository configuration
            repo_dir: Repository directory

        Returns:
            True if successful
        """
        logger.info(f"Updating repository {config.url}...")

        env = self._get_git_env()

        try:
            # Fetch latest changes
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "fetch", "origin", config.branch],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

            if result.returncode != 0:
                logger.warning(f"Git fetch failed, attempting re-clone: {result.stderr}")
                # Try to re-clone
                import shutil
                shutil.rmtree(repo_dir)
                return self._clone_repository(config, repo_dir)

            # Reset to latest
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "reset", "--hard", f"origin/{config.branch}"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if result.returncode != 0:
                logger.error(f"Git reset failed: {result.stderr}")
                return False

            logger.info(f"Successfully updated {config.url}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Update timeout for {config.url}")
            return False

    def _get_git_env(self) -> dict:
        """
        Get environment variables for Git commands with authentication.

        Returns:
            Environment dict
        """
        env = os.environ.copy()

        # Check for GitHub token
        token = os.environ.get("SKILL_HUB_GITHUB_TOKEN")
        if token:
            # For HTTPS URLs, Git will use the token from the URL
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = token
            env["GIT_PASSWORD"] = token

        return env

    def get_commit_hash(self, url: str) -> Optional[str]:
        """
        Get current commit hash of repository.

        Args:
            url: Repository URL

        Returns:
            Commit hash or None if not available
        """
        repo_dir = self._get_repo_dir(url)

        if not (repo_dir / ".git").exists():
            return None

        try:
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def load_metadata(self, url: str) -> Optional[RepositoryMetadata]:
        """
        Load repository metadata.

        Args:
            url: Repository URL

        Returns:
            RepositoryMetadata or None
        """
        meta_file = self._get_metadata_file(url)

        if not meta_file.exists():
            return None

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RepositoryMetadata(**data)
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to load metadata for {url}: {e}")
            return None

    def save_metadata(self, metadata: RepositoryMetadata) -> None:
        """
        Save repository metadata.

        Args:
            metadata: Repository metadata to save
        """
        meta_file = self._get_metadata_file(metadata.url)
        ensure_directory(meta_file.parent)

        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                # Convert dataclass to dict
                data = {
                    "url": metadata.url,
                    "branch": metadata.branch,
                    "commit_hash": metadata.commit_hash,
                    "last_sync_at": metadata.last_sync_at,
                    "skills_imported": metadata.skills_imported,
                    "sync_count": metadata.sync_count,
                    "last_error": metadata.last_error,
                }
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save metadata for {metadata.url}: {e}")

    def _save_metadata_error(self, url: str, error: str) -> None:
        """Save error to metadata."""
        metadata = self.load_metadata(url) or RepositoryMetadata(
            url=url,
            branch="main",
        )
        metadata.last_error = error
        metadata.last_sync_at = datetime.now().isoformat()
        self.save_metadata(metadata)

    def get_repository_path(self, url: str) -> Path:
        """
        Get local path to repository.

        Args:
            url: Repository URL

        Returns:
            Path to repository directory
        """
        return self._get_repo_dir(url)

    def validate_url(self, url: str) -> bool:
        """
        Validate repository URL format.

        Args:
            url: Repository URL

        Returns:
            True if valid format
        """
        # Basic validation for common Git URL formats
        valid_prefixes = ("https://", "http://", "git@", "ssh://")
        return any(url.startswith(prefix) for prefix in valid_prefixes)
