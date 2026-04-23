# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.1] - 2026-04-24

### Fixed

- **Python 3.9 compatibility**: Replace `X | None` type hints with `Optional[X]` in `repos.py` (union syntax requires Python 3.10+)

## [0.13.0] - 2026-04-24

### Added

- **Async repo clone/pull with progress**: Adding a remote repo now runs in a background thread with a real-time progress bar showing clone percentage and current stage
- **Task polling API**: `POST /api/repos/async` starts an async clone/pull task; `GET /api/repos/task/<id>` polls progress status
- **Retry on failure**: If clone/pull fails (network error, timeout, etc.), a Retry button allows resuming without re-entering the URL
- **Closable progress panel**: Progress panel shows green on success, red on error, and can be dismissed at any time

### Fixed

- **Add remote repo had no feedback**: `POST /api/repos` was synchronous, blocking the browser for up to 120s during `git clone` with no visual feedback; now fully async with progress tracking

## [0.12.0] - 2026-04-23

### Changed

- **No default repo auto-seeding**: `load_repos_config()` no longer auto-creates `repos.yaml` with `anthropics/skills` on first run; repos.yaml starts empty
- **Add repo form default value**: Repo URL input now pre-fills `https://github.com/anthropics/skills` as a suggested default instead of being auto-added as a configured repo

## [0.11.0] - 2026-04-23

### Added

- **Repo diagnostics API**: `GET /api/diagnose` and `GET /api/diagnose/<name>` endpoints provide detailed health checks for all configured repositories
- **Git installation check**: `check_git_installed()` verifies git is available before attempting clone operations
- **Network connectivity check**: `check_network_connectivity()` tests GitHub reachability before remote operations
- **Comprehensive repo diagnostics**: `diagnose_repo()` runs 8 checks including git, network, directory existence, SKILL.md files, mapping files, and skill scanning
- **Diagnosis button in Web UI**: 🔍 button in header triggers full diagnostics with detailed results panel
- **i18n support for diagnostics**: Chinese and English labels for all diagnostic messages

### Changed

- **Improved error handling in `sync_mapping()`**: Now checks git installation and network connectivity before attempting clone, providing clearer error messages

## [0.10.3] - 2026-04-23

### Fixed

- **New machine initialization**: `list_skills()` now auto-triggers `sync_mapping()` when a remote repo has no skill mapping, ensuring fresh installs discover skills immediately
- **Invalid git directory detection**: `scheduler.check_now()` now validates `.git` subdirectory before treating a directory as cloned; empty or corrupted directories are re-cloned
- **Accurate clone status**: `isCloned` flag now checks for `.git` presence rather than just directory existence, preventing false "cloned" states on failed/incomplete clones

## [0.10.2] - 2026-04-23

### Fixed

- **Web UI new machine initialization**: Moved auto-sync from blocking `list_skills()` to background scheduler; scheduler now clones uncloned repos automatically on first check
- **Repo display logic**: `selectedRepo` now considers all repos, not just those with skills; `syncOneRepo` handles uncloned repos (red dot clickable)

## [0.10.1] - 2026-04-23

### Fixed

- **Missing web template files in pip package**: `pyproject.toml` now includes `web/templates/*` and `web/static/*` in package data, fixing `TemplateNotFound: index.html` error when running `skill-hub web` after pip install

## [0.10.0] - 2026-04-23

### Added

- **Skill name conflict detection**: When multiple repos contain skills with the same name, the first discovered path wins and conflicts are reported
- **`conflict` field in API**: `/api/skills` now returns `conflict: true` for skills whose name appears in multiple repos
- **Cross-repo conflict flagging**: `list_skills()` detects when the same skill name exists across different repositories
- **`_find_skills_in_repo` conflict reporting**: Returns both the skill mapping and a list of name conflicts within a single repo

### Changed

- **`sync_mapping` and `pull_latest`**: Now report the number of name conflicts skipped during mapping rebuild

## [0.9.0] - 2026-04-23

### Added

- **Web UI version badge**: Header now displays current version number with async update checking
- **Update notification dot**: Red dot appears next to version when a new release is available on GitHub
- **Version dropdown menu**: Click version badge to see "Update now" or "Skip this version" options
- **Skip version API**: `POST /api/version/skip` persists skipped versions to avoid repeated prompts
- **Version info API**: `GET /api/version` returns current, latest, hasUpdate, and skipped status

### Changed

- **Async update checks**: Moved version update detection from CLI blocking prompt to web UI async fetch
- **Removed CLI update prompt**: `skill-hub web` no longer blocks on startup for version checks; `--no-check-update` flag removed
- **`get_latest_version` timeout**: Added configurable `timeout` parameter for GitHub API calls

## [0.8.0] - 2026-04-23

### Added

- **Request duration logging**: Werkzeug access logs now include response time `(X.Xms)` for every request
- **Server-side initial data injection**: Home page now pre-renders skills and repos data into HTML, eliminating frontend AJAX wait on first paint
- **MD5 cache persistence**: Skill directory MD5 checksums are cached to `~/.skills_repo/md5_cache.json` and survive process restarts
- **Parallel MD5 computation**: `list_skills()` now computes source skill MD5s across multiple threads

### Changed

- **Web UI CSS**: Replaced `cdn.tailwindcss.com` (~300KB+ external JS) with a precompiled 12KB local CSS file, eliminating network dependency on first paint
- **Parallel repo update checks**: `get_repos()` and `update_status()` now check `has_remote_updates` in parallel via thread pool instead of serial git fetch
- **Git fetch timeout**: Reduced from 15s to 5s to prevent slow networks from blocking API responses

### Fixed

- **First-screen loading speed (LCP)**: Reduced from ~1.01s to ~150ms by combining local CSS, MD5 caching, and server-injected initial data

## [0.7.0] - 2026-04-21

### Added
- **`version` CLI command**: Show current version and check for updates via GitHub API
- **`self-update` CLI command**: Upgrade skill-hub to the latest version from PyPI via `pip install --upgrade`
- **`version.py` module**: Semantic version parsing and comparison utilities (`compare_versions`, `get_latest_version`)

### Changed
- **Web UI styling**: Migrated from custom CSS to Tailwind CSS CDN
- **Sidebar navigation**: Skills are now grouped by remote repositories and local directories
- **Default repo seeding**: Fresh installs automatically seed `anthropics/skills` as the default repository

## [0.6.0] - 2026-03-16

### Added
- **Private skills support**: Added `.agents/skills/` directory for project-local skills with priority over public skills
- **`skill-hub-assistant` skill**: Natural language interface for managing skills via AI agents
- **`version-bump` skill**: Guide for updating project version numbers and CHANGELOG.md
- **AGENTS.md**: Documentation for AI agents on using skill-hub CLI

### Changed
- **Makefile targets**: Updated `version-bump` and added `git-commit` targets to use skill execution

## [0.5.0] - 2026-03-16

### Added
- **Version-aware `list` command**: default view now shows Version and Status columns when both public and private scopes are visible, surfacing `Up to date`, `⚠ Out of sync`, `Private only`, and `Public only` states inline
- **`list --diff`**: replaces the removed `compare` command, showing a full version comparison table between private and public skills

### Changed
- **CLI simplified**: removed `compare`, `upgrade`, and `list-local` commands (11 → 8 commands)
- **`list` default**: now shows all skills (public + private) in one table with a Source column; use `--public` or `--private` to filter
- **`sync` positional args**: `--from`/`--to` flags replaced by positional arguments — `skill-hub sync my-skill private public`; path-style skill argument still supported (e.g. `.agents/skills/my-skill`)
- **`install --to`**: accepts `public`/`private` keywords instead of raw paths (explicit paths still work)

### Fixed
- **Metadata serialization bug**: `metadata` dict in SKILL.md frontmatter was serialized as Python `str()` repr (`{'key': 'val'}`) instead of valid YAML; now uses `yaml.dump()`
- **`sync` skill resolution**: skill argument can now be a path like `.agents/skills/git-commit-helper`; the skill name and source directory are resolved correctly

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

[Unreleased]: https://github.com/wuerping/skill-hub/compare/v0.13.1...HEAD
[0.13.1]: https://github.com/wuerping/skill-hub/releases/tag/v0.13.1
[0.13.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.13.0
[0.12.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.12.0
[0.11.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.11.0
[0.10.3]: https://github.com/wuerping/skill-hub/releases/tag/v0.10.3
[0.10.2]: https://github.com/wuerping/skill-hub/releases/tag/v0.10.2
[0.10.1]: https://github.com/wuerping/skill-hub/releases/tag/v0.10.1
[0.10.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.10.0
[0.9.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.9.0
[0.8.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.8.0
[0.7.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.7.0
[0.6.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.6.0
[0.5.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.5.0
[0.4.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.4.0
[0.3.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.3.0
[0.2.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.2.0
[0.1.0]: https://github.com/wuerping/skill-hub/releases/tag/v0.1.0
