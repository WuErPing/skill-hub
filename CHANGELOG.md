# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-03-16

### Added
- **Comprehensive Test Suite**: Added complete test coverage for all modules
  - 10 test files with 1700+ lines of test code
  - CLI command tests (`test_cli.py`)
  - Comparison module tests (`test_comparison.py`)
  - Discovery engine tests (`test_discovery.py`)
  - Installer tests (`test_installer.py`)
  - Data models tests (`test_models.py`)
  - Upgrader tests (`test_upgrader.py`)
  - Utility function tests (`test_utils.py`)
  - Version management tests (`test_version.py`)
- **Pytest Configuration**: Added pytest setup with coverage support
  - Dev dependencies: `pytest>=7.0`, `pytest-cov>=4.0`
  - Test discovery configuration in `pyproject.toml`

### Fixed
- **Installer Bug**: Fixed missing parent directory creation during skill installation
  - `install_path.mkdir(parents=True, exist_ok=True)` now called before copying files

## [0.3.0] - 2026-03-13

### Changed
- **Simplified to view-only**: Removed all features except viewing skills in `~/.agents/skills`
- Removed remote repository management (pull, repo commands)
- Removed synchronization features (sync command)
- Removed agent adapters (Cursor, Claude, Qoder, etc.)
- Removed bilingual translation support
- Removed AI-powered skill finder
- Removed web interface (FastAPI, Streamlit, Flask)
- Removed configuration management system
- Simplified CLI to three commands: `list`, `view`, `path`

### Removed
- All modules: adapters, remote, sync, bilingual, ai, web, locales, config
- Complex configuration options
- Multi-agent support
- Health checks

## [0.2.0] - 2026-02-07

### Added
- **Expanded Ecosystem Support**: Added 5 new AI coding agents
  - Antigravity (Google)
  - Codex (OpenAI)
  - GitHub Copilot
  - Gemini CLI
  - Windsurf (Codeium)
  - Now supporting 9+ AI coding agents total
- **Shared Skills Directory (`.agents/skills/`) Standard**: Support for agent-agnostic shared skills directory
  - New `get_shared_skills_path()` method in `AgentAdapter` base class to discover `.agents/skills/` in project root
  - Shared path included in skill discovery with highest priority
  - Skills from `.agents/skills/` are tagged with `agent="shared"` for source tracking
  - Health checks now report shared skills status (`shared_skills_path` and `shared_skills_exists`)
  - Comprehensive documentation in README.md with usage examples
  - Full backward compatibility with existing agent-specific directories
- **Official Repository Integration**: Quick setup commands for official skill repositories
  - `--with-all` flag to add all official repositories
  - Individual flags: `--with-anthropic`, `--with-vercel`, `--with-cloudflare`, `--with-supabase`, `--with-qoder`
  - Support for Qoder Community repository (54+ skills, 9 categories)
- **Internationalization (i18n)**: Support for English and Chinese languages
- Test suite for shared skills functionality
  - Unit tests for shared path discovery
  - Integration tests for conflict resolution between shared and agent-specific paths
  - Tests for priority ordering and source tagging

### Changed
- **Unified Hub Location**: Changed central hub from `~/.skills/` to `~/.agents/skills/`
- Updated `get_all_search_paths()` to include `.agents/skills/` as highest priority
- Updated `SyncEngine.pull_from_agents()` to properly tag shared skills
- Enhanced skill discovery priority order: shared > project-local > global
- Improved web interface with better repository management and sync controls

### Documentation
- Added comprehensive "Shared Skills Directory" section to README.md
- Updated Quick Start guide to mention `.agents/skills/` discovery and new agents
- Updated openspec/project.md with priority order and shared directory information
- Added usage examples and migration guidance
- Added official repository list with descriptions

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

[Unreleased]: https://github.com/yourusername/skill-hub/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/yourusername/skill-hub/releases/tag/v0.4.0
[0.3.0]: https://github.com/yourusername/skill-hub/releases/tag/v0.3.0
[0.2.0]: https://github.com/yourusername/skill-hub/releases/tag/v0.2.0
[0.1.0]: https://github.com/yourusername/skill-hub/releases/tag/v0.1.0
