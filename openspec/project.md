# Project Context

## Purpose
Skill-hub is a unified skill management system that discovers, synchronizes, and distributes AI coding agent skills across multiple platforms (Antigravity, Claude, Codex, Copilot, Cursor, Gemini CLI, OpenCode, Qoder, Windsurf). It provides a centralized repository at `~/.agents/skills/` and ensures all agents have access to the same skill definitions.

## Tech Stack
- **Language**: Python 3.9+
- **CLI Framework**: Click or Typer
- **YAML Parsing**: PyYAML
- **File System**: pathlib (standard library)
- **Configuration**: JSON for metadata, YAML for skill frontmatter
- **Testing**: pytest

## Project Conventions

### Code Style
- Follow standard TypeScript/JavaScript conventions (if Node.js)
- Follow Go effective Go guidelines (if Go)
- Use ESLint + Prettier for formatting (Node.js)
- Use gofmt for formatting (Go)
- Meaningful variable names, single responsibility functions
- Comprehensive error handling

### Architecture Patterns
- **Plugin Architecture**: Each agent adapter is a separate plugin/module
- **Registry Pattern**: Central skill registry manages all discovered skills
- **Synchronization Engine**: Monitors source locations and triggers updates
- **Configuration-Driven**: Agent-specific paths and formats defined in configuration

### Testing Strategy
- Unit tests for each adapter and core functionality
- Integration tests for end-to-end skill synchronization
- Mock file system operations for reproducible tests
- Test coverage target: 80%+

### Git Workflow
- Main branch: `main`
- Feature branches: `feature/<name>`
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Squash merge to main

## Domain Context

### Skill Structure
Skills are reusable instruction sets for AI coding agents, defined in SKILL.md files:
- Must include YAML frontmatter with name and description
- Stored in hierarchical directories: `<location>/skills/<skill-name>/SKILL.md`
- Can be project-local or global

### Supported Agents
1. **Antigravity**: Uses `.agent/skills/` and `~/.antigravity/skills/`
2. **Claude**: Uses `.claude/skills/` and `~/.claude/skills/`
3. **Codex**: Uses `.codex/skills/` and `~/.codex/skills/`
4. **GitHub Copilot**: Uses `.github/skills/` and `~/.copilot/skills/`
5. **Cursor**: Uses `.cursor/skills/` and `~/.cursor/skills/`
6. **Gemini CLI**: Uses `.gemini/skills/` and `~/.gemini/skills/`
7. **OpenCode**: Uses `.opencode/skills/` and `~/.config/opencode/skills/`
8. **Qoder**: Uses `.qoder/skills/` and `~/.qoder/skills/`
9. **Windsurf**: Uses `.windsurf/skills/` and `~/.codeium/windsurf/skills/`

### Skill Discovery Sources

Priority order (highest to lowest):
1. **Shared directory**: `.agents/skills/` (project-local, agent-agnostic)
2. **Agent-specific project-local**: `.cursor/skills/`, `.claude/skills/`, `.qoder/skills/`, `.opencode/skills/`, etc.
3. **Agent-specific global**: `~/.cursor/skills/`, `~/.claude/skills/`, `~/.qoder/skills/`, `~/.config/opencode/skills/`, etc.
4. **Central hub**: `~/.agents/skills/` (synchronization target)

The `.agents/skills/` standard (introduced in v0.2.0) provides a unified, agent-agnostic location for project-specific skills that can be shared across all AI coding agents and version controlled with the project.

## Important Constraints
- Must not modify skill content during synchronization
- Must preserve skill metadata and frontmatter
- Must handle concurrent access safely
- Must work cross-platform (macOS, Linux, Windows)
- Must respect agent-specific skill format requirements

## External Dependencies
- File system access for reading/writing skills
- YAML parser for frontmatter
- Markdown parser for validation (optional)
- File watching capability for auto-sync (future)
