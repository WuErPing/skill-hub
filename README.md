# skill-hub

Web UI for managing skills from GitHub repositories and local directories.

## Installation

```bash
pip install skill-hub

# Or from GitHub
pip install git+https://github.com/wuerping/skill-hub.git

# Development
pip install -e .
```

## Quick Start

```bash
skill-hub web
```

Opens a browser UI at `http://127.0.0.1:7860` where you can add GitHub repos or local directories, browse skills, and install them to `~/.claude/skills/` and `~/.agents/skills/`.

```bash
# Custom port
skill-hub web --port 8080

# Don't auto-open browser
skill-hub web --no-open
```

## How It Works

1. **Add a GitHub repo or local directory** via the UI — remote repos get cloned into `~/.skills_repo/repos/`, local paths are scanned in place
2. **Skills are discovered** automatically via `SKILL.md` files in the repo
3. **Install skills** to `~/.claude/skills/` and `~/.agents/skills/` with one click
4. **Sync status** — green dots mean installed version matches source, yellow means outdated
5. **Repo sync** — detect and pull remote updates, with a sync status indicator per repo (local paths skip cloning)

## Features

- Skills grouped by repository (remote and local)
- Per-directory install status (green = up-to-date, yellow = outdated vs source)
- Install to both `~/.claude/skills` and `~/.agents/skills` simultaneously
- Click yellow dots to reinstall a single directory from source
- Click skill names to view metadata from `SKILL.md` frontmatter
- Add/remove repos, with remote update detection
- **Local directory support** — add any local path (e.g. `~/code/my-skills`) as a skill source

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

## Architecture

### Module Structure

```
src/skill_hub/
├── cli.py              # Click CLI entrypoint (web command only)
├── models.py           # SkillMetadata dataclass
├── utils/
│   ├── __init__.py     # Path helpers (expand_path, derive_name)
│   └── yaml_parser.py  # SKILL.md YAML frontmatter parser
└── web/
    ├── app.py          # Flask app factory
    ├── api.py          # REST API routes
    ├── repos.py        # Repo management (clone, scan, install)
    ├── state.py        # Installed skills state tracking
    └── templates/
        └── index.html  # Single-page web UI
```

### Data Flow

```
  GitHub / Local Path                ~/.skills_repo/               Targets
                                     (Local Cache)                 (Installed)

       │                                  │                            │
       │  git clone (remote)              │                            │
       │  scan in place (local)           │                            │
       ▼                                  ▼                            ▼
 ┌───────────┐                  ┌─────────────────┐         ┌─────────────────┐
 │  Source   │─────────────────►│   repos/        │         │ ~/.claude/      │
 │  (URL or  │                  │   (source code) │         │   skills/       │
 │   path)   │                  └─────────────────┘         └─────────────────┘
 └───────────┘                          │                            ▲
                                        │  scan SKILL.md             │
                                        ▼                            │
                               ┌─────────────────┐                   │
                               │   mappings/     │───────────────────┘
                               │   (skill index) │
                               └─────────────────┘
                                          │
                                          │  copy / install
                                          ▼
                               ┌─────────────────┐
                               │ ~/.agents/      │
                               │   skills/       │
                               └─────────────────┘
```

## Directory Structure

```
~/.skills_repo/
├── repos.yaml             # repo list config
├── repos/                 # cloned git repos
│   └── owner__repo/
│       └── ...
└── mappings/              # skill location mappings (YAML)
    └── owner__repo.yaml

~/.claude/skills/          # installed skills (target A)
~/.agents/skills/          # installed skills (target B)
```

## License

MIT
