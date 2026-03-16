# skill-hub — Agent Guide

skill-hub is a CLI tool for viewing, installing, and managing agent skills stored in `~/.agents/skills` (public) and `.agents/skills` (private/project-level).

## Key Concepts

- **Public skills** — `~/.agents/skills/` — shared globally across all projects
- **Private skills** — `.agents/skills/` — project-local, takes priority over public when names collide
- **SKILL.md** — every skill is a directory with a `SKILL.md` file containing YAML frontmatter (`name`, `description`) and markdown instructions

## CLI Commands

| Command | What it does |
|---------|-------------|
| `skill-hub list` | List all skills (public + private) |
| `skill-hub list --public` | Public skills only |
| `skill-hub list --private` | Private skills only |
| `skill-hub list --verbose` | Full details (path, version, compatibility) |
| `skill-hub list --diff` | Side-by-side comparison of private vs public |
| `skill-hub view <name>` | Print a skill's full SKILL.md content |
| `skill-hub path` | Show the public skills directory path |
| `skill-hub install <source>` | Install skill to private (default) |
| `skill-hub install <source> --to public` | Install to public |
| `skill-hub install <source> --as <name>` | Install with a custom name |
| `skill-hub sync <name> private public` | Promote private skill to public |
| `skill-hub sync <name> public private` | Pull public skill into project |
| `skill-hub sync ... --dry-run` | Preview without making changes |
| `skill-hub sync ... --force` | Overwrite without confirmation |
| `skill-hub update` | Check all public skills for updates |
| `skill-hub update <name>` | Check a specific skill for updates |
| `skill-hub version` | Show installed version |
| `skill-hub version --check` | Check if newer version exists |
| `skill-hub self-update` | Upgrade skill-hub via pip |

## Install Sources

- **Local path**: `skill-hub install /path/to/my-skill` or `./relative/path`
- **GitHub**: `skill-hub install user/repo/skill-folder`
- **URL**: `skill-hub install https://example.com/SKILL.md`
- **Bare name** (already discovered): `skill-hub install my-skill`

## SKILL.md Format

```markdown
---
name: skill-name
description: What the skill does and when to use it
license: MIT
compatibility: cursor, claude, opencode
metadata:
  version: 1.0.0
  author: you@example.com
  updateUrl: https://github.com/user/repo/path/to/skill
---

## Skill instructions here
```

## Skills in This Project

Private skills live in `.agents/skills/`. Use `skill-hub list --private` to see what's available, or `skill-hub view <name>` to read one.

## Available Skill: `skill-hub-assistant`

Use the `skill-hub-assistant` skill (in `.agents/skills/`) when a user asks to manage skills in natural language — listing, installing, syncing, or viewing skills.
