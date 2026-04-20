# Skills Repo Web UI Design

## Overview

A web interface for managing skills sourced from GitHub repositories. Skills are cloned into `~/.skills_repo/`, then installed to `~/.claude/skills/` and `~/.agents/skills/` via drag-and-drop or button interactions. The tool is launched via `skill-hub web`.

## Architecture

### Directory Structure

```
~/.skills_repo/
  repos.yaml              # Source repository list
  skills/                 # Cloned skills source
    owner-repo1/
      skill-a/
      skill-b/
    owner-repo2/
      skill-c/

~/.claude/skills/         # Install target A
~/.agents/skills/         # Install target B
```

### How Skills Enter ~/.skills_repo

Users edit `repos.yaml` to list GitHub repository URLs, then run `skill-hub web` which clones/fetches them. The web UI manages repos.yaml via API.

### CLI Entry Point

`skill-hub web` starts a local Flask server (default `localhost:7860`) and opens the browser. The user navigates to the URL to manage skills.

### Tech Stack

- **Backend**: Flask (Python), API-driven
- **Frontend**: Vanilla HTML + Vanilla JS + HTMX via CDN, no build step
- **State**: File-system driven, no external database

## Data Model

### repos.yaml

```yaml
repos:
  - url: https://github.com/example/skills
    branch: main
  - url: https://github.com/another/repo
    branch: main
```

### Skill Metadata

Each skill directory may contain a `.meta` file:

```yaml
name: brainstorming
repo: example/skills
description: Help turn ideas into fully formed designs
```

Metadata is read from the skill directory or parsed from the README.

### Installation State Tracking

State is derived from filesystem presence:

- Skill in `~/.claude/skills/<name>/` → installed to A
- Skill in `~/.agents/skills/<name>/` → installed to B
- MD5 snapshots stored in `.meta` files for inconsistency detection

## Web Interface

### Layout (Single Column + Status Tags)

```
┌─────────────────────────────────────────────────┐
│ skill-hub                          [刷新] [设置] │
├─────────────────────────────────────────────────┤
│ 📁 github.com/example/skills                     │
│   ├─ brainstorming    [已安装] [不一致] [卸载]   │
│   └─ tdd               [未安装]  [安装]          │
│ 📁 github.com/another/repo                       │
│   └─ lark-sheets       [已安装]  [卸载]          │
└─────────────────────────────────────────────────┘
```

### Status Tags

| Status | Meaning |
|--------|---------|
| 未安装 | Present in repos, not in either install directory |
| 已安装 | Present in both `~/.claude/skills` and `~/.agents/skills` with matching MD5 |
| 不一致 | Present in both install directories but MD5 differs (highlighted) |
| 部分安装 | Present in only one install directory |

### Interactions

- **Install**: Click "安装" button → copies files to both `~/.claude/skills/` and `~/.agents/skills/`, computes MD5 snapshot
- **Uninstall**: Click "卸载" button → removes from both install directories, preserves source in `~/.skills_repo`
- **Refresh**: Button reloads the full skill list and re-checks status

### Update Detection

- Each repo's local git state is checked on page load
- If `git fetch` indicates remote has new commits, a banner appears: "检测到更新，点击刷新"
- Manual refresh button pulls latest and reloads the UI

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/skills` | List all skills with status |
| POST | `/api/skills/<name>/install` | Install skill to both directories |
| POST | `/api/skills/<name>/uninstall` | Uninstall from both directories |
| GET | `/api/repos` | List repos from repos.yaml |
| POST | `/api/repos` | Add a new repository URL |
| DELETE | `/api/repos/<name>` | Delete a repository |
| POST | `/api/repos/sync` | Manually sync all repos (git fetch) |
| GET | `/api/update-status` | Check if any repos have remote updates |

### Install Flow

1. Read all files from `~/.skills_repo/skills/<repo>/<skill>/`
2. Copy to `~/.claude/skills/<skill>/` and `~/.agents/skills/<skill>/`
3. Compute MD5 snapshot of all files, write to `.meta`
4. Return updated status

### Uninstall Flow

1. Delete `~/.claude/skills/<skill>/` recursively
2. Delete `~/.agents/skills/<skill>/` recursively
3. Preserve source in `~/.skills_repo`
4. Return updated status

## Error Handling

- `git clone/fetch` failure → displayed in UI error toast, does not block other operations
- File copy failure (permission, disk full) → returns 500, shown in frontend
- Skill modified manually in install directory → install overwrites with confirmation prompt

## Persistence

- `repos.yaml` is the single source of truth for repository list
- `~/.skills_repo/skills/` is the single source of truth for skill source code
- Deleting a repo via UI removes its directory from `~/.skills_repo/skills/`
- No external database; state is derived from filesystem

## Refresh Triggers

- Page load: full scan of all directories
- Install/uninstall: incremental update
- Manual refresh button: full rescan
