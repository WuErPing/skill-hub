# skill-hub

View, install, and manage skills from `~/.agents/skills`.

## Installation

```bash
pip install skill-hub

# Or from GitHub
pip install git+https://github.com/wuerping/skill-hub.git

# Development
pip install -e .
```

## Multi-Layer Skill Directory Architecture

skill-hub supports **public** (global) and **private** (project-level) skill directories:

```
                     Remote Sources
                  GitHub / URL / Local Path
                  skill-hub install <source>
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌───────────────────────┐   ┌───────────────────────┐
│    PUBLIC (Global)    │   │   PRIVATE (Project)   │
│                       │   │                       │
│  ~/.agents/skills/    │   │  .agents/skills/      │
│  ~/.claude/skills/    │   │  .claude/skills/      │
│                       │   │  .<tool>/skills/      │
└──────────┬────────────┘   └──────────┬────────────┘
           │                           │
           │   Priority: private > public
           └──────────┬────────────────┘
                      ▼
              Skill Discovery

  # Sync between directories
  $ skill-hub sync my-skill private public
  $ skill-hub sync my-skill public private
```

**Priority**: When the same skill exists in both directories, the private (project-level) version takes precedence.

## Commands

### `list` — List skills

```bash
# List all skills (public + private), default
skill-hub list

# Filter by scope
skill-hub list --public
skill-hub list --private

# Detailed output
skill-hub list --verbose

# Show diff between private and public
skill-hub list --diff
```

### `view` — View a skill

```bash
skill-hub view <skill-name>
```

### `install` — Install a skill

Install from a local path, GitHub repository, or URL.
Installs to private (`./.agents/skills`) by default.

```bash
# From local path (to private, default)
skill-hub install /path/to/my-skill

# To public (~/.agents/skills)
skill-hub install /path/to/my-skill --to public

# From GitHub
skill-hub install user/repo/skill-name

# From URL
skill-hub install https://example.com/SKILL.md

# With custom name
skill-hub install /path/to/my-skill --as custom-name
```

### `sync` — Sync a skill between directories

FROM and TO are positional arguments: `public` or `private`.

```bash
# Private → public
skill-hub sync my-skill private public

# Public → private
skill-hub sync my-skill public private

# Also accepts a path as the skill argument
skill-hub sync .agents/skills/my-skill private public

# Dry run
skill-hub sync my-skill private public --dry-run

# Force overwrite
skill-hub sync my-skill private public --force
```

### `update` — Check for skill updates

```bash
# Check all skills in ~/.agents/skills
skill-hub update

# Check a specific skill
skill-hub update my-skill
```

### `path` — Show public skills directory

```bash
skill-hub path
```

### `version` / `self-update`

```bash
skill-hub version
skill-hub version --check
skill-hub self-update
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `skill-hub list` | List all skills (public + private) |
| `skill-hub list --public` | List only public skills |
| `skill-hub list --private` | List only private skills |
| `skill-hub list --verbose` | List with detailed info |
| `skill-hub list --diff` | Show diff between private and public |
| `skill-hub view <name>` | View a specific skill |
| `skill-hub path` | Show public skills directory path |
| `skill-hub install <source>` | Install to private (default) |
| `skill-hub install <source> --to public` | Install to public |
| `skill-hub install <source> --to private` | Install to private |
| `skill-hub install <source> --as <name>` | Install with custom name |
| `skill-hub sync <name> private public` | Sync from private to public |
| `skill-hub sync <name> public private` | Sync from public to private |
| `skill-hub sync <name> <from> <to> --dry-run` | Preview sync |
| `skill-hub sync <name> <from> <to> --force` | Force overwrite |
| `skill-hub update` | Check all skills for updates |
| `skill-hub update <name>` | Check specific skill for updates |
| `skill-hub version` | Show current version |
| `skill-hub version --check` | Check for available updates |
| `skill-hub self-update` | Update skill-hub to latest version |

## SKILL.md Format

```markdown
---
name: skill-name
description: A brief description of the skill
license: MIT
compatibility: cursor, claude, opencode
metadata:
  version: 1.0.0
  author: you@example.com
---

## Skill Content

Your skill instructions here...
```

## Directory Structure

```
~/.agents/skills/          # public
├── skill-name-1/
│   └── SKILL.md
└── skill-name-2/
    └── SKILL.md

.agents/skills/            # private (project)
├── custom-skill/
│   └── SKILL.md
└── ...
```

## Examples

### Override a public skill with a project-specific version

```bash
# Sync public skill to project for customization
skill-hub sync public-skill public private

# Edit .agents/skills/public-skill/SKILL.md
# Private version now takes priority automatically
skill-hub list
```

### Share a skill across projects

```bash
# Develop and test in project first
skill-hub install /path/to/new-skill

# Promote to public when ready
skill-hub sync new-skill private public
```

### Team collaboration

```bash
# Install team skill to project directory
skill-hub install company/team-skill --to private

# Commit to repository
git add .agents/skills/
git commit -m "Add team skill"
```

## License

MIT
