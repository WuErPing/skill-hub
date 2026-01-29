# skill-hub

Unified skill management system for AI coding agents (Cursor, Claude, Qoder, OpenCode).

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
│   ├── utils/             # Utilities (YAML parser, validators)
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

### Phase 2 (Future)
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
