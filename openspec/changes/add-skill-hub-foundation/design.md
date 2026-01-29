# Design Document

## Context

The skill-hub project aims to solve the fragmentation problem in AI coding agent skill management. Currently, developers who use multiple AI coding agents (Cursor, Claude, Qoder, OpenCode) must manually maintain skill definitions in separate configuration directories for each agent. This leads to duplication, inconsistency, and synchronization overhead.

The skill-hub system provides a centralized skill repository at `~/.skills/` and automatic bi-directional synchronization with all agent configurations.

**Stakeholders:**
- Developers using multiple AI coding agents
- Teams sharing skill definitions across members
- Tool maintainers who need to integrate with skill-hub

**Constraints:**
- Must preserve skill content without modifications
- Must work cross-platform (macOS, Linux, Windows)
- Must handle concurrent access safely
- Must be lightweight and fast (< 1s for typical sync operations)
- Phase 1 must support: Cursor, Claude, Qoder, OpenCode

## Goals / Non-Goals

### Goals
- **Unified Discovery**: Find all skills across all agent configurations in one command
- **Automatic Sync**: Bi-directional synchronization between hub and agents
- **Conflict Resolution**: Detect and resolve conflicts when same skill differs across locations
- **Extensibility**: Easy to add support for new agents without core changes
- **Cross-Platform**: Work on macOS, Linux, and Windows
- **Performance**: Fast operations with incremental sync optimization

### Non-Goals (Phase 1)
- **Real-time sync**: File watching and automatic sync (future feature)
- **Cloud sync**: Remote synchronization between machines (future feature)
- **Skill editor**: Built-in editor for creating/modifying skills (use existing editors)
- **Skill marketplace**: Public repository of skills (future feature)
- **Version control**: Git-like versioning for skills (future feature)
- **Permissions**: Fine-grained access control for skills (future feature)

## Decisions

### Decision 1: Technology Stack - Node.js/TypeScript vs Go

**Options:**

**A) Node.js + TypeScript**
- **Pros**: 
  - Excellent cross-platform file system APIs
  - Rich ecosystem for YAML parsing, CLI frameworks (Commander.js/oclif)
  - Faster development with npm ecosystem
  - Easy to package as npm CLI tool
  - Most developers familiar with JavaScript/TypeScript
- **Cons**:
  - Requires Node.js runtime
  - Slightly slower startup time than native binaries
  - Larger distribution size

**B) Go**
- **Pros**:
  - Single binary distribution (no runtime needed)
  - Fast startup and execution
  - Excellent cross-compilation for all platforms
  - Strong standard library for file operations
- **Cons**:
  - Smaller ecosystem for some tasks
  - Longer development time for complex features
  - Less familiar to some contributors

**Decision: Node.js + TypeScript (recommended for Phase 1)**

**Rationale:**
- Faster time to market with rich npm ecosystem
- Easy installation via npm/npx
- Better developer experience for contributors
- Can be rewritten in Go later if performance becomes critical
- Most AI coding agent users already have Node.js installed

### Decision 2: Plugin Architecture for Agent Adapters

**Options:**

**A) Monolithic with hardcoded agents**
- Simple implementation
- All agents in single codebase
- No plugin loading complexity

**B) Plugin architecture with dynamic loading**
- Each agent is a separate module/plugin
- New agents can be added without core changes
- Better separation of concerns

**Decision: Plugin architecture with dynamic loading**

**Rationale:**
- Extensibility is a core requirement
- Easier to test each adapter independently
- Community can contribute new adapters without modifying core
- Cleaner codebase with separation of concerns
- Worth the additional complexity for long-term maintainability

### Decision 3: Conflict Resolution Strategy

**Options:**

**A) Always overwrite (hub → agents)**
- Simple, predictable
- Hub is always source of truth
- No conflict resolution needed

**B) Timestamp-based (newest wins)**
- Automatic resolution
- Respects most recent changes
- Can lose older but correct versions

**C) Manual resolution with prompts**
- User decides on conflicts
- Most flexible
- Slower, requires user interaction

**D) Configurable strategy**
- Support all above strategies
- User chooses default behavior
- Can override per-operation

**Decision: Configurable strategy (default: newest wins)**

**Rationale:**
- Flexibility for different use cases
- Default to automatic (timestamp) for convenience
- Allow manual mode for critical scenarios
- Hub-priority mode for team setups where hub is authoritative

### Decision 4: Metadata Storage Format

**Options:**

**A) Embedded in SKILL.md as comments**
- No separate files
- Self-contained
- Modifies skill content

**B) Separate JSON files per skill**
- Clean separation
- Easy to parse
- More files to manage

**C) Single central database (SQLite)**
- Efficient queries
- Complex dependency
- Overkill for simple metadata

**Decision: Separate JSON files per skill**

**Rationale:**
- Preserves skill content integrity (constraint)
- Easy to read/write with standard tools
- No external database dependencies
- Simple backup/restore (just copy directory)
- Pattern: `~/.skills/.skill-hub/<skill-name>.json`

### Decision 5: Sync Direction Model

**Options:**

**A) Uni-directional only (agents → hub OR hub → agents)**
- Simpler logic
- User chooses direction explicitly
- No automatic merging

**B) Bi-directional with smart merge**
- Pull then push in single operation
- Detects changes on both sides
- Resolves conflicts automatically

**Decision: Both options supported**

**Rationale:**
- Default to bi-directional for convenience (`skill-hub sync`)
- Support explicit directions for control (`--pull`, `--push`)
- Gives users flexibility for different workflows

## Technical Architecture

### Components

```
skill-hub
├── CLI Layer (Commander.js)
│   ├── sync command
│   ├── discover command
│   ├── list command
│   └── agents command
│
├── Core Layer
│   ├── Discovery Engine
│   │   ├── File scanner
│   │   ├── YAML parser
│   │   └── Skill validator
│   │
│   ├── Sync Engine
│   │   ├── Conflict detector
│   │   ├── Conflict resolver
│   │   ├── Metadata manager
│   │   └── Checksum calculator
│   │
│   └── Registry
│       ├── Skill registry
│       └── Metadata store
│
└── Adapter Layer
    ├── Adapter interface
    ├── Cursor adapter
    ├── Claude adapter
    ├── Qoder adapter
    └── OpenCode adapter
```

### Data Flow

**Discovery Flow:**
```
1. User runs: skill-hub discover
2. Discovery engine scans agent directories
3. Each adapter resolves its paths
4. SKILL.md files are parsed and validated
5. Skills added to registry with metadata
6. Registry exported to JSON (optional)
```

**Sync Flow (Pull):**
```
1. User runs: skill-hub sync --pull
2. Discovery engine finds all skills
3. For each skill:
   a. Check if exists in hub
   b. Compare checksums
   c. If different, copy to hub
   d. Update metadata
4. Report summary
```

**Sync Flow (Push):**
```
1. User runs: skill-hub sync --push
2. Read all skills from ~/.skills/
3. For each enabled adapter:
   a. Resolve target directory
   b. Copy skill to adapter directory
   c. Preserve frontmatter and content
4. Report summary
```

**Conflict Resolution Flow:**
```
1. Detect: Multiple versions with different checksums
2. Collect: All versions with timestamps
3. Resolve based on strategy:
   - newest: Compare mtime, keep newest
   - manual: Show diff, prompt user
   - hub-priority: Always use hub version
4. Apply resolution and log decision
```

## Data Models

### Skill Metadata (JSON)
```json
{
  "name": "git-release",
  "description": "Create consistent releases and changelogs",
  "sources": [
    {
      "path": "/Users/alice/.cursor/skills/git-release/SKILL.md",
      "agent": "cursor",
      "discoveredAt": "2026-01-30T10:30:00Z"
    }
  ],
  "checksum": "sha256:abc123...",
  "lastSyncAt": "2026-01-30T10:35:00Z",
  "syncHistory": [
    {
      "timestamp": "2026-01-30T10:35:00Z",
      "operation": "pull",
      "source": "/Users/alice/.cursor/skills/git-release/SKILL.md"
    }
  ]
}
```

### Configuration (config.json)
```json
{
  "version": "1.0.0",
  "conflictResolution": "newest",
  "agents": {
    "cursor": {
      "enabled": true,
      "globalPath": null
    },
    "claude": {
      "enabled": true,
      "globalPath": null
    },
    "qoder": {
      "enabled": true,
      "globalPath": null
    },
    "opencode": {
      "enabled": true,
      "globalPath": null
    }
  },
  "sync": {
    "incremental": true,
    "checkPermissions": true,
    "createDirectories": true
  }
}
```

## Risks / Trade-offs

### Risk 1: Concurrent Access
**Risk**: Multiple processes modifying skills simultaneously could cause corruption

**Mitigation**:
- Use atomic file operations (write to temp, then rename)
- Add lock file during sync operations
- Detect concurrent modifications via checksum validation

### Risk 2: Cross-Platform Path Issues
**Risk**: Windows vs Unix path differences could cause bugs

**Mitigation**:
- Use Node.js path module for all path operations
- Test on all platforms in CI/CD
- Normalize paths before comparisons

### Risk 3: Large Number of Skills
**Risk**: Performance degradation with 1000+ skills

**Mitigation**:
- Implement incremental sync (only process changed skills)
- Use parallel processing for independent operations
- Add progress indicators for long operations
- Defer full optimization to Phase 2 if needed

### Risk 4: Metadata Drift
**Risk**: Metadata could get out of sync with actual skills

**Mitigation**:
- Always validate checksum before trusting metadata
- Implement repair command to rebuild metadata from skills
- Store checksums in metadata for quick validation

### Trade-off: Plugin Complexity vs Extensibility
- **Trade-off**: More complex code for plugin system
- **Benefit**: Easy to add new agents without core changes
- **Decision**: Worth it for long-term maintainability

### Trade-off: Automatic vs Manual Conflict Resolution
- **Trade-off**: Automatic resolution might lose correct version
- **Benefit**: Faster workflow without user intervention
- **Decision**: Configurable with safe default (newest)

## Migration Plan

### Phase 1: Initial Release
1. Release skill-hub with core functionality
2. Users manually copy existing skills to `~/.skills/` or run discovery
3. Document migration process in README

### Phase 2: Future Enhancements (Not in this change)
- File watching for automatic sync
- Cloud sync between machines
- Skill validation and testing
- Skill templates and generators

### Rollback Strategy
- Users can delete `~/.skills/` directory
- Agent configs remain unchanged (non-destructive by default)
- Use `skill-hub sync --rollback` to restore previous state

## Open Questions

1. **Should we validate skill content beyond frontmatter?**
   - Current decision: No, only validate frontmatter structure
   - Rationale: Keep skill-hub focused on management, not validation
   - Can be added in Phase 2 if needed

2. **Should we support skill versioning?**
   - Current decision: No versioning in Phase 1
   - Rationale: Adds complexity, unclear if needed
   - Track in sync history for now, full versioning in Phase 2

3. **Should we support nested skill directories?**
   - Current decision: Flat structure only (`skills/<name>/SKILL.md`)
   - Rationale: Matches current agent conventions
   - Can be extended if agents support it in future

4. **Should we support skill dependencies?**
   - Current decision: No, skills are independent in Phase 1
   - Rationale: No current agent support for dependencies
   - Can be added if agents add this feature
