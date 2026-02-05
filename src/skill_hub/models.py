"""Data models for skill-hub."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SkillMetadata:
    """Metadata for a skill from YAML frontmatter."""

    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class SkillSource:
    """Source location information for a discovered skill."""

    path: Path
    agent: str  # cursor, claude, qoder, opencode
    discovered_at: datetime


@dataclass
class Skill:
    """Complete skill with metadata and content."""

    metadata: SkillMetadata
    content: str
    sources: List[SkillSource] = field(default_factory=list)
    checksum: Optional[str] = None
    last_sync_at: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Get skill name from metadata."""
        return self.metadata.name


@dataclass
class SyncHistory:
    """History entry for a sync operation."""

    timestamp: datetime
    operation: str  # pull, push, bi-directional
    source: Optional[str] = None


@dataclass
class SkillHubMetadata:
    """Metadata stored for a skill in the hub."""

    name: str
    description: str
    sources: List[Dict[str, str]]
    checksum: str
    last_sync_at: str
    sync_history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration for an agent adapter."""

    enabled: bool = True
    global_path: Optional[str] = None


@dataclass
class RepositoryConfig:
    """Configuration for a remote skill repository."""

    url: str
    enabled: bool = True
    branch: str = "main"
    path: str = ""
    sync_schedule: Optional[str] = None


@dataclass
class RepositoryMetadata:
    """Metadata for a remote repository."""

    url: str
    branch: str
    commit_hash: Optional[str] = None
    last_sync_at: Optional[str] = None
    skills_imported: List[str] = field(default_factory=list)
    sync_count: int = 0
    last_error: Optional[str] = None


@dataclass
class Config:
    """skill-hub configuration."""

    version: str = "1.0.0"
    conflict_resolution: str = "newest"  # newest, manual, hub-priority, remote-priority, local-priority
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    repositories: List[RepositoryConfig] = field(default_factory=list)
    sync: Dict[str, bool] = field(
        default_factory=lambda: {
            "incremental": True,
            "check_permissions": True,
            "create_directories": True,
            "remote_priority": False,
        }
    )
