# skill-hub

View, install, upgrade, and manage skills from `~/.agents/skills` directory.

## Installation

```bash
pip install -e .
```

## Usage

### List all skills

```bash
skill-hub list
```

### List skills with detailed information

```bash
skill-hub list --verbose
```

### View a specific skill

```bash
skill-hub view <skill-name>
```

### Show skills directory path

```bash
skill-hub path
```

### Compare local and global skills

Compare skills in your local project with global skills:

```bash
# Full comparison table
skill-hub compare

# Summary only (no detailed table)
skill-hub compare --summary

# Specify custom paths
skill-hub compare --local ./skills --global ~/.agents/skills
```

This command compares skills in your local project (e.g., `.opencode/skills`) with global skills (`~/.agents/skills`) and shows:

- **Local only**: Skills only in your local project
- **Global only**: Skills only in global directory
- **Update available**: Skills with version differences
- **Up to date**: Skills with matching versions

## Skill Lifecycle Management

### Install a skill

Install skills from GitHub repositories, local paths, or URLs:

```bash
# From GitHub repository
skill-hub install user/repo/skill-name

# With custom name
skill-hub install user/repo/skill-name --as my-skill

# From local path
skill-hub install /path/to/skill

# From URL
skill-hub install https://example.com/path/to/SKILL.md
```

### Upgrade a skill

Upgrade a local skill to global format with automatic config conversion:

```bash
skill-hub upgrade skill-name
```

This converts `.claude` configs to `.agent` format and creates a backup before upgrading.

### Check for updates

Check for skill updates:

```bash
# Check all skills
skill-hub update

# Check specific skill
skill-hub update skill-name
```

## Directory Structure

```
~/.agents/skills/
├── skill-name-1/
│   └── SKILL.md
├── skill-name-2/
│   └── SKILL.md
└── ...
```

## SKILL.md Format

```markdown
---
name: skill-name
description: A brief description of the skill
license: MIT (optional)
compatibility: cursor, claude, qoder (optional)
version: 1.0.0 (optional)
updateUrl: https://example.com/version.txt (optional)
---

## Skill Content

Your skill content here...
```

### Version Tracking

Skills can include version information:

- `version`: Semantic version (e.g., `1.0.0`)
- `updateUrl`: URL to fetch latest version info

Example:

```markdown
---
name: my-skill
description: A useful skill
version: 1.2.3
updateUrl: https://raw.githubusercontent.com/user/repo/main/VERSION
---
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `skill-hub list` | List all skills |
| `skill-hub list --verbose` | List skills with detailed info |
| `skill-hub view <name>` | View a specific skill |
| `skill-hub path` | Show skills directory path |
| `skill-hub compare` | Compare local and global skills (full table) |
| `skill-hub compare --summary` | Compare with summary only |
| `skill-hub install <source>` | Install a skill from GitHub, local path, or URL |
| `skill-hub install <source> --as <name>` | Install with custom name |
| `skill-hub upgrade <name>` | Upgrade a skill to global format |
| `skill-hub update` | Check all skills for updates |
| `skill-hub update <name>` | Check specific skill for updates |

## License

MIT
