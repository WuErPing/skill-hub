# Change: Add Skill-Hub Foundation

## Why

AI coding agents (Cursor, Claude, Qoder, OpenCode) each maintain their own skill definitions in separate configuration directories, leading to:
- **Duplication**: Same skills stored multiple times across different agent configs
- **Inconsistency**: Skills drift out of sync when updated in one location
- **Discovery friction**: No centralized view of available skills across all agents
- **Manual overhead**: Developers must manually copy skills between agents

A unified skill management system solves these problems by providing a single source of truth (~/.skills/) and automatic synchronization to all agent configurations.

## What Changes

This change introduces the foundational skill-hub system with three core capabilities:

1. **Skill Discovery**: Scan agent config directories to find existing skills
   - Support for Cursor (`.cursor/`, `~/.cursor/`)
   - Support for Claude (`.claude/`, `~/.claude/`)
   - Support for Qoder (`.qoder/`, `~/.qoder/`)
   - Support for OpenCode (`.opencode/`, `~/.config/opencode/`)
   - Parse SKILL.md files and validate frontmatter
   - Build unified skill registry

2. **Skill Synchronization**: Maintain central skill repository
   - Create and manage `~/.skills/` directory
   - Detect skills from all agent sources
   - Copy skills to central location with metadata
   - Track skill sources and timestamps
   - Prevent content modifications during sync

3. **Agent Adapters**: Distribute skills to agent configs
   - Plugin architecture for each agent type
   - Agent-specific path resolution
   - Respect agent format requirements
   - Bi-directional sync (discover → hub → distribute)
   - Conflict detection and resolution

## Impact

### Affected Specs
- **NEW**: `specs/skill-discovery/spec.md` - Skill discovery engine
- **NEW**: `specs/skill-sync/spec.md` - Central synchronization logic
- **NEW**: `specs/agent-adapters/spec.md` - Agent-specific adapters

### Affected Code
- **NEW**: Core CLI interface (`src/cli.ts` or `cmd/root.go`)
- **NEW**: Skill discovery engine (`src/discovery/` or `pkg/discovery/`)
- **NEW**: Sync engine (`src/sync/` or `pkg/sync/`)
- **NEW**: Agent adapters (`src/adapters/` or `pkg/adapters/`)
- **NEW**: Configuration management (`src/config/` or `pkg/config/`)
- **NEW**: Test suites for all components

### User Impact
- **Breaking**: None (new system)
- **Migration**: Users can manually copy existing skills to `~/.skills/` or run discovery
- **Compatibility**: Works alongside existing agent skill systems without interference
