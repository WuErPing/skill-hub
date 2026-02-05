# skill-hub

Unified skill management system for AI coding agents (Cursor, Claude, Qoder, OpenCode).

English | [简体中文](README.zh-CN.md)

## Overview

skill-hub discovers, synchronizes, and distributes AI coding agent skills across multiple platforms. It provides a centralized repository at `~/.skills/` and ensures all agents have access to the same skill definitions.

### Problem

AI coding agents each maintain their own skill definitions in separate configuration directories, leading to:
- **Duplication**: Same skills stored multiple times across different agent configs
- **Inconsistency**: Skills drift out of sync when updated in one location
- **Discovery friction**: No centralized view of available skills across all agents
- **Manual overhead**: Developers must manually copy skills between agents

### Solution

skill-hub solves these problems by:
1. **Discovering** skills from all agent configuration directories
2. **Synchronizing** them to a central hub at `~/.skills/`
3. **Distributing** updated skills back to all agent configurations

## Features

- 🔍 **Multi-Agent Discovery**: Automatically find skills from Cursor, Claude, Qoder, and OpenCode
- 🔄 **Bi-Directional Sync**: Pull skills from agents to hub, push from hub to agents
- ⚡ **Incremental Updates**: Only sync changed skills for better performance
- 🔧 **Extensible**: Plugin architecture for easy addition of new agents
- 🏥 **Health Checks**: Verify adapter configurations and permissions
- 📊 **Rich CLI**: Beautiful terminal output with tables and progress indicators

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/skill-hub.git
cd skill-hub

# Install in development mode
pip install -e ".[dev]"
```

### From PyPI (coming soon)

```bash
pip install skill-hub
```

## Quick Start

### 1. Discover Skills

Find all skills across your AI agent configurations:

```bash
skill-hub discover
```

This will scan:
- `~/.cursor/skills/`, `.cursor/skills/`
- `~/.claude/skills/`, `.claude/skills/`
- `~/.qoder/skills/`, `.qoder/skills/`
- `~/.config/opencode/skills/`, `.opencode/skills/`

### 2. Sync Skills

Synchronize skills between hub and agents:

```bash
# Bi-directional sync (pull then push)
skill-hub sync

# Only pull from agents to hub
skill-hub sync --pull

# Only push from hub to agents
skill-hub sync --push
```

### 3. List Skills in Hub

```bash
skill-hub list
```

### 4. Check Agent Health

```bash
skill-hub agents --check
```

### 5. Add Remote Repositories

Pull skills from community repositories like https://github.com/anthropics/skills:

```bash
# Add a remote repository
skill-hub repo add https://github.com/anthropics/skills

# Pull skills from all configured repositories
skill-hub pull

# List configured repositories
skill-hub repo list
```

### 6. Web Interface

Launch a browser-based UI to manage skills (opens automatically in your default browser):

```bash
# Start FastAPI Web UI (default) - auto-opens browser
skill-hub web

# Choose a different backend
skill-hub web --backend streamlit
skill-hub web --backend flask

# Start without opening browser
skill-hub web --no-browser
```

The web interface provides:
- 📊 Dashboard with quick actions and metrics
- 🔄 Sync controls (pull/push/both)
- 📦 Repository management (add/list/pull)
- 🤖 Agent health checks
- ⚙️ Configuration viewer
- 🔍 Skill discovery

## Setup for New Users

When someone clones this project repository, they need to set up their **local user configuration**:

### Initial Setup

1. **Install the project:**
   ```bash
   git clone https://github.com/yourusername/skill-hub.git
   cd skill-hub
   pip install -e .
   ```

2. **Initialize configuration:**
   
   **Option A: Quick setup with Anthropic skills (recommended)**
   ```bash
   skill-hub init --with-anthropic
   ```
   
   **Option B: Interactive setup**
   ```bash
   skill-hub init
   # Follow the prompts to add repositories
   ```
   
   **Option C: Custom repositories**
   ```bash
   skill-hub init --repo https://github.com/yourorg/team-skills
   ```

3. **Pull skills:**
   ```bash
   skill-hub pull
   ```

4. **Distribute to your agents:**
   ```bash
   skill-hub sync
   ```

### Configuration Storage

**Important:** Configuration is stored **per-user** at `~/.skills/.skill-hub/config.json`, NOT in the project repository. This means:

- ✅ Each user configures their own repositories
- ✅ Each user manages their own hub at `~/.skills/`
- ✅ Configuration is **not** checked into Git
- ✅ Team members can share skill repository URLs via documentation

### Sharing Repository Configuration

To help team members, you can document recommended repositories in your project:

**Option 1: Simple one-liner in your project README**
```markdown
## Setup Skills

After installation, run:
```bash
skill-hub init --with-anthropic --repo https://github.com/yourorg/team-skills
skill-hub pull
```
```

**Option 2: Shell script** (`setup-skills.sh`):
```bash
#!/bin/bash
set -e

echo "Setting up skill-hub..."
skill-hub init --with-anthropic --repo https://github.com/yourorg/team-skills

echo "Fetching skills..."
skill-hub pull

echo "Distributing to agents..."
skill-hub sync

echo "✓ Skills setup complete!"
```
```

### Private Repositories

For private GitHub repositories, set an environment variable:

```bash
export SKILL_HUB_GITHUB_TOKEN="ghp_your_token_here"
skill-hub pull
```

Add to your shell profile (`~/.zshrc`, `~/.bashrc`) to persist across sessions.

## Supported Agents

| Agent | Project-Local | Global |
|-------|--------------|--------|
| **Cursor** | `.cursor/skills/` | `~/.cursor/skills/` |
| **Claude** | `.claude/skills/` | `~/.claude/skills/` |
| **Qoder** | `.qoder/skills/` | `~/.qoder/skills/` |
| **OpenCode** | `.opencode/skills/` | `~/.config/opencode/skills/` |

## Skill Format

Skills must be defined in `SKILL.md` files with YAML frontmatter:

```markdown
---
name: git-release
description: Create consistent releases and changelogs
license: MIT
compatibility: cursor, claude, qoder, opencode
---

## What I do
- Draft release notes from merged PRs
- Propose a version bump
- Provide a copy-pasteable `gh release create` command

## When to use me
Use this when you are preparing a tagged release.
```

### Requirements

- **name**: Lowercase alphanumeric with single hyphens (1-64 chars)
- **description**: 1-1024 characters
- **license**: Optional license identifier
- **compatibility**: Optional compatibility note
- **metadata**: Optional key-value pairs

## CLI Commands

### `skill-hub web`

Start the web interface for managing skills through a browser. The browser will open automatically.

```bash
skill-hub web                           # Start FastAPI UI (default, port 8501, auto-open browser)
skill-hub web --backend fastapi         # Explicit FastAPI backend with HTMX + Tailwind
skill-hub web --backend streamlit       # Use Streamlit backend
skill-hub web --backend flask           # Use Flask backend (Vue.js + Element Plus)
skill-hub web --host 0.0.0.0 --port 8080  # Custom host/port
skill-hub web --no-browser              # Start without opening browser
```

**Features:**
- **Dashboard**: Quick init, pull, and metrics
- **Sync**: Bi-directional, pull-only, or push-only sync
- **Hub Skills**: View all skills in central hub with descriptions
- **Repositories**: Add/list/remove remote repos, pull skills
- **Agents**: List adapters and run health checks
- **Config**: View current configuration JSON
- **Discovery**: Discover skills from all agents

**Backends:**
- **FastAPI** (default): Modern, fast async backend with HTMX + Tailwind CSS, SPA-like experience
- **Streamlit**: Interactive Python-native UI with automatic reload
- **Flask**: Lightweight REST API with Vue.js + Element Plus frontend

### `skill-hub init`

Initialize skill-hub configuration with repository setup.

```bash
skill-hub init                      # Interactive mode with prompts
skill-hub init --with-anthropic     # Add Anthropic skills automatically
skill-hub init --repo <url>         # Add custom repository
skill-hub init --with-anthropic --repo https://github.com/org/repo  # Combine options
```

**Interactive Mode Example:**
```
$ skill-hub init
Initializing skill-hub configuration...

Quick Setup:

Add Anthropic's community skills repository? [Y/n]: y
  ✓ Added: https://github.com/anthropics/skills

Add custom repository? [y/N]: y
  Repository URL: https://github.com/myorg/skills
    ✓ Added
  Add another? [y/N]: n

✓ Configuration saved to ~/.skills/.skill-hub/config.json
  2 repository(ies) configured

Next steps:
  1. Run: skill-hub pull to fetch skills
  2. Run: skill-hub sync to distribute to agents
```

### `skill-hub sync`

Synchronize skills between hub and agents.

```bash
skill-hub sync              # Bi-directional (pull then push)
skill-hub sync --pull       # Pull from agents to hub
skill-hub sync --push       # Push from hub to agents
skill-hub sync --verbose    # Show detailed logging
```

### `skill-hub discover`

Discover skills from all agent configurations.

```bash
skill-hub discover          # Show skills in table format
skill-hub discover --json   # Export as JSON
```

### `skill-hub list`

List all skills in the central hub.

```bash
skill-hub list
```

### `skill-hub agents`

Manage agent adapters.

```bash
skill-hub agents            # List all adapters
skill-hub agents --check    # Run health checks
```

### `skill-hub repo`

Manage remote skill repositories.

```bash
skill-hub repo add <url>           # Add a repository
skill-hub repo add <url> --branch dev --path /skills  # With options
skill-hub repo list                # List configured repositories
skill-hub repo remove <url>        # Remove a repository
```

**Examples:**
```bash
# Add Anthropic's community skills
skill-hub repo add https://github.com/anthropics/skills

# Add with specific branch
skill-hub repo add https://github.com/yourorg/skills --branch develop

# Add with subdirectory path
skill-hub repo add https://github.com/example/repo --path /contrib/skills
```

### `skill-hub pull`

Pull skills from remote repositories.

```bash
skill-hub pull                      # Pull from all enabled repositories
skill-hub pull <url>                # Pull from specific repository
```

**What it does:**
1. Clones or updates repositories (shallow clone with `--depth 1`)
2. Scans for `SKILL.md` files
3. Imports skills to `~/.skills/`
4. Tracks commit hashes for incremental updates
5. Saves metadata (sync count, last sync time, imported skills)

## Architecture

```
skill-hub/
├── src/skill_hub/
│   ├── adapters/          # Agent-specific adapters
│   │   ├── cursor.py
│   │   ├── claude.py
│   │   ├── qoder.py
│   │   └── opencode.py
│   ├── discovery/         # Skill discovery engine
│   ├── sync/              # Synchronization engine
│   ├── remote/            # Remote repository management
│   ├── utils/             # Utilities (YAML parser, validators)
│   ├── web/               # Web interfaces
│   │   ├── app.py         # Flask app (REST API + Vue UI)
│   │   └── streamlit_app.py  # Streamlit app
│   ├── models.py          # Data models
│   └── cli.py             # Command-line interface
├── tests/                 # Unit and integration tests
└── openspec/              # OpenSpec specifications
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=skill_hub --cov-report=term-missing

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_utils.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=skill_hub
```

## Configuration

skill-hub uses a configuration file at `~/.skills/.skill-hub/config.json`:

```json
{
  "version": "1.0.0",
  "conflict_resolution": "newest",
  "agents": {
    "cursor": {
      "enabled": true,
      "global_path": null
    },
    "claude": {
      "enabled": true,
      "global_path": null
    },
    "qoder": {
      "enabled": false,
      "global_path": null
    },
    "opencode": {
      "enabled": true,
      "global_path": null
    }
  },
  "sync": {
    "incremental": true,
    "check_permissions": true,
    "create_directories": true
  }
}
```

## Roadmap

### Phase 1 (Current)
- ✅ Multi-agent skill discovery
- ✅ Bi-directional synchronization
- ✅ Support for Cursor, Claude, Qoder, OpenCode
- ✅ Basic conflict detection

### Phase 2 (Completed)
- ✅ Remote repository support (pull from GitHub, etc.)
- ✅ Configuration management system
- ✅ Repository metadata tracking
- ✅ Web interface (FastAPI + HTMX + Tailwind CSS, Streamlit, Flask)
- ✅ Auto-open browser on web command

### Phase 3 (Future)
- 🔲 File watching for automatic sync
- 🔲 Cloud sync between machines
- 🔲 Skill validation and testing
- 🔲 Advanced conflict resolution strategies
- 🔲 Skill marketplace/registry

## Contributing

Contributions are welcome! Please read the [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### Adding a New Agent

To add support for a new AI coding agent:

1. Create a new adapter in `src/skill_hub/adapters/`:

```python
from skill_hub.adapters.base import AgentAdapter

class NewAgentAdapter(AgentAdapter):
    @property
    def name(self) -> str:
        return "newagent"

    @property
    def default_global_path(self) -> str:
        return "~/.newagent"

    @property
    def project_local_dirname(self) -> str:
        return ".newagent"
```

2. Register it in `AdapterRegistry`
3. Add tests
4. Update documentation

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [OpenSpec](https://github.com/Fission-AI/OpenSpec) for specification-driven development
- Skill format inspired by [OpenCode Skills](https://opencode.ai/docs/skills/)
- CLI built with [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/skill-hub/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/skill-hub/discussions)
- **Documentation**: [Full Documentation](https://skill-hub.readthedocs.io/)
