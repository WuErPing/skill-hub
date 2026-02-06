# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Shared Skills Directory (`.agents/skills/`) Standard**: Support for agent-agnostic shared skills directory
  - New `get_shared_skills_path()` method in `AgentAdapter` base class to discover `.agents/skills/` in project root
  - Shared path included in skill discovery with highest priority
  - Skills from `.agents/skills/` are tagged with `agent="shared"` for source tracking
  - Health checks now report shared skills status (`shared_skills_path` and `shared_skills_exists`)
  - Comprehensive documentation in README.md with usage examples
  - Full backward compatibility with existing agent-specific directories
- Test suite for shared skills functionality
  - Unit tests for shared path discovery
  - Integration tests for conflict resolution between shared and agent-specific paths
  - Tests for priority ordering and source tagging

### Changed
- Updated `get_all_search_paths()` to include `.agents/skills/` as highest priority
- Updated `SyncEngine.pull_from_agents()` to properly tag shared skills
- Enhanced skill discovery priority order: shared > project-local > global

### Documentation
- Added comprehensive "Shared Skills Directory" section to README.md
- Updated Quick Start guide to mention `.agents/skills/` discovery
- Updated openspec/project.md with priority order and shared directory information
- Added usage examples and migration guidance

## [0.1.0] - 2026-01-30

### Added
- Initial release with core functionality
- Multi-agent skill discovery (Cursor, Claude, Qoder, OpenCode)
- Bi-directional synchronization between hub and agents
- Remote repository support (pull from GitHub)
- Web interface with three backends (FastAPI + HTMX, Streamlit, Flask)
- CLI commands: `discover`, `sync`, `list`, `agents`, `repo`, `pull`, `init`, `web`
- Configuration management system
- Conflict detection and resolution
- Health checks for adapters
- Auto-open browser on `skill-hub web` command

[Unreleased]: https://github.com/yourusername/skill-hub/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/skill-hub/releases/tag/v0.1.0
