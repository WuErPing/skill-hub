# skill-hub

View, install, upgrade, and manage skills from `~/.agents/skills` directory.

## Installation

```bash
# Install in editable mode (for development)
pip install -e .

# Or install globally
pip install skill-hub

# Or install from GitHub
pip install git+https://github.com/wuerping/skill-hub.git
```

## Multi-Layer Skill Directory Architecture

skill-hub supports a hierarchical skill directory structure with both **public** (global) and **project-level** (project-specific) skill directories:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              REMOTE                                            │
│                           GitHub                                               │
│  skill-hub install user/repo/skill-name --to public|private                    │
└───────────────────────────┬──────────────────────────────────┬───────────────┘
                            │                                  │
                            ▼                                  ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│          PUBLIC               │        │          PUBLIC               │
│   ~/.agents/skills/           │        │   ~/.claude/skills/           │
│   (Global - shared)           │◄──────►│   (Global - tool-specific)    │
│                               │        │                               │
│   skill-hub list --public     │        │   skill-hub list --public     │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to public                 │        │   --to public                 │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │     Bidirectional Config Sync          │
            │     (automatic tool detection)         │
            │                                        │
            ▼                                        ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     PROJECT-LEVEL             │        │     PROJECT-LEVEL             │
│   .agents/skills/             │        │   .claude/skills/             │
│   (Project-specific skills)   │        │   (Project-specific skills)   │
│                               │        │                               │
│   skill-hub list --private    │        │   skill-hub list --private    │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to private                │        │   --to private                │
│                               │        │                               │
│   skill-hub sync <skill>      │        │   skill-hub sync <skill>      │
│   --from public --to private  │        │   --from public --to private  │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │   Priority: Project-level > Global     │
            │   (project skills override global)     │
            │                                        │
            ▼                                        ▼
         Project A                               Project B
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              REMOTE                                            │
│                           GitHub                                               │
│  skill-hub install user/repo/skill-name --to public|private                    │
└───────────────────────────┬──────────────────────────────────┬───────────────┘
                            │                                  │
                            ▼                                  ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│          PUBLIC               │        │          PUBLIC               │
│   ~/.agents/skills/           │        │   ~/.claude/skills/           │
│   (Global - shared)           │◄──────►│   (Global - tool-specific)    │
│                               │        │                               │
│   skill-hub list --public     │        │   skill-hub list --public     │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to public                 │        │   --to public                 │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │     Bidirectional Config Sync          │
            │     (automatic tool detection)         │
            │                                        │
            ▼                                        ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     PROJECT-LEVEL             │        │     PROJECT-LEVEL             │
│   .agents/skills/             │        │   .claude/skills/             │
│   (Project-specific skills)   │        │   (Project-specific skills)   │
│                               │        │                               │
│   skill-hub list --private    │        │   skill-hub list --private    │
│   skill-hub install ...       │        │   skill-hub install ...       │
│   --to private                │        │   --to private                │
│                               │        │                               │
│   skill-hub sync <skill>      │        │   skill-hub sync <skill>      │
│   --from public --to private  │        │   --from public --to private  │
└───────────┬───────────────────┘        └───────────┬───────────────────┘
            │                                        │
            │   Priority: Project-level > Global     │
            │   (project skills override global)     │
            │                                        │
            ▼                                        ▼
         Project A                               Project B

# List all skills with source indication
$ skill-hub list --all

# Sync with dry-run to preview changes
$ skill-hub sync my-skill --from public --to private --dry-run
```

### Directory Types

**Public Directories** (Global):
- `~/.agents/skills/` - Agent-level public skills
- `~/.claude/skills/` - Tool-specific public skills
- `~/.opencode/skills/` - Opencode tool-specific public skills

**Project-Level Directories** (Project-specific):
- `./.agents/skills/` - Agent-level project-specific skills
- `./.claude/skills/` - Tool-specific project-specific skills
- `./.*/skills/` - Other tool-specific project-level directories

### Priority System

When the same skill exists in multiple directories:

1. **Project-level > Global** - Project-specific skills override global skills
2. **First discovered** - When multiple project-level directories exist, the first one found takes precedence

This allows you to:
- Share public skills across all projects
- Override public skills with project-specific customizations
- Keep project-specific skills isolated to a project

## Usage

### List all skills

```bash
# List public skills (default)
skill-hub list

# List all skills from all directories
skill-hub list --all

# List only project-level skills
skill-hub list --private

# List only public skills
skill-hub list --public

# List with detailed information
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

# Compare all local directories
skill-hub compare --all-locals
```

This command compares skills in your local project (e.g., `.opencode/skills`, `.agents/skills`) with global skills (`~/.agents/skills`) and shows:

- **Local only**: Skills only in your local project
- **Global only**: Skills only in global directory
- **Update available**: Skills with version differences
- **Up to date**: Skills with matching versions

## Skill Lifecycle Management

### Install a skill

Install skills from GitHub repositories, local paths, or URLs:

```bash
# Install to project-level directory (default)
skill-hub install user/repo/skill-name

# Install to project-level directory (explicit)
skill-hub install user/repo/skill-name --to private

# Install to public directory
skill-hub install user/repo/skill-name --to public

# With custom name
skill-hub install user/repo/skill-name --as my-skill

# From local path
skill-hub install /path/to/skill

# From URL
skill-hub install https://example.com/path/to/SKILL.md
```

### Sync skills between directories

Explicitly sync skills between public and project-level directories (no automatic bidirectional sync):

```bash
# Sync from public to project-level
skill-hub sync my-skill --from public --to private

# Sync from project-level to public
skill-hub sync my-skill --from private --to public

# Dry run - show what would happen without making changes
skill-hub sync my-skill --from public --to private --dry-run

# Force overwrite existing skill
skill-hub sync my-skill --from public --to private --force
```

**Important**: The sync command requires explicit user action. There is no automatic bidirectional synchronization.

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

### Version management

Check skill-hub version and updates:

```bash
# Show current version
skill-hub version

# Check for available updates
skill-hub version --check
```

### Self-update

Update skill-hub to the latest version:

```bash
skill-hub self-update
```

## Directory Structure

### Public (Global) Structure

```
~/.agents/skills/
├── skill-name-1/
│   └── SKILL.md
├── skill-name-2/
│   └── SKILL.md
└── ...

~/.claude/skills/
├── skill-name-1/
│   └── SKILL.md
└── ...
```

### Project-Level (Project-specific) Structure

```
./.agents/skills/
├── custom-skill-1/
│   └── SKILL.md
└── ...

./.claude/skills/
├── custom-skill-2/
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
| `skill-hub list` | List public skills (default) |
| `skill-hub list --all` | List skills from all directories |
| `skill-hub list --private` | List only project-level skills |
| `skill-hub list --public` | List only public skills |
| `skill-hub list --verbose` | List skills with detailed info |
| `skill-hub view <name>` | View a specific skill |
| `skill-hub path` | Show skills directory path |
| `skill-hub compare` | Compare local and global skills |
| `skill-hub compare --summary` | Compare with summary only |
| `skill-hub compare --all-locals` | Compare all local directories |
| `skill-hub install <source>` | Install a skill |
| `skill-hub install <source> --to public` | Install to public directory |
| `skill-hub install <source> --to private` | Install to project-level directory |
| `skill-hub install <source> --as <name>` | Install with custom name |
| `skill-hub sync <name> --from public --to private` | Sync skill from public to project-level |
| `skill-hub sync <name> --from private --to public` | Sync skill from project-level to public |
| `skill-hub sync <name> --from public --to private --dry-run` | Dry run sync |
| `skill-hub sync <name> --from public --to private --force` | Force sync (overwrite) |
| `skill-hub upgrade <name>` | Upgrade a skill to global format |
| `skill-hub update` | Check all skills for updates |
| `skill-hub update <name>` | Check specific skill for updates |
| `skill-hub version` | Show current version |
| `skill-hub version --check` | Check for available updates |
| `skill-hub self-update` | Update skill-hub to latest version |

## Migration Guide

### For Existing Users

If you're already using skill-hub, your existing skills in `~/.agents/skills/` will continue to work exactly as before. The new multi-layer features are additive and backward compatible.

**To start using project-level directories:**

1. Create a project-level skills directory in your project:
   ```bash
   mkdir -p .agents/skills
   ```

2. Install skills to the project-level directory:
   ```bash
   skill-hub install user/repo/skill-name --to private
   ```

3. Or sync existing public skills to project-level for customization:
   ```bash
   skill-hub sync existing-skill --from public --to private
   ```

### Best Practices

1. **Public skills**: Use for general-purpose skills that can be shared across projects
2. **Project-level skills**: Use for project-specific customizations
3. **Sync workflow**: Make changes in project-level, then sync to public when ready to share
4. **Version control**: Commit `.agents/skills/` to your project repository for team collaboration

## Examples

### Example 1: Override a public skill with project-specific version

```bash
# Install public skill
skill-hub install user/public-skill

# Sync to project-level for customization
skill-hub sync public-skill --from public --to private

# Edit .agents/skills/public-skill/SKILL.md

# List shows project-level version takes priority
skill-hub list --all
```

### Example 2: Share skills with team

```bash
# Create project-level skills directory
mkdir -p .agents/skills

# Install team-specific skill to project-level
skill-hub install company/team-skill --to private

# Commit to repository
git add .agents/skills/
git commit -m "Add team-specific skill"
```

### Example 3: Workflow with dry-run

```bash
# Check what would be synced
skill-hub sync my-skill --from public --to private --dry-run

# Actually sync if it looks correct
skill-hub sync my-skill --from public --to private
```

## License

MIT
