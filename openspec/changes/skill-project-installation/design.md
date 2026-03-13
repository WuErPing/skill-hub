## Context

**Current State**: skill-hub is a read-only skill discovery tool that lists skills from `~/.agents/skills`. It can list, view, and show paths but cannot install, upgrade, or manage skill versions.

**Key Constraints**:
- Skills are stored as directories with `SKILL.md` files containing YAML frontmatter
- Multiple tool ecosystems exist (Claude, Cursor, Opencode, Qwen Code, Crush) with different config formats
- No existing version tracking mechanism for skills
- Users need a complete lifecycle management system

**Stakeholders**: Skill authors, skill consumers, multi-tool users who want consistent skill experiences across tools.

## Goals / Non-Goals

**Goals:**
1. **One-click Skill Installation**: Install skills from GitHub repos, local paths, or URLs into `~/.agents/skills`
2. **Global Skill Upgrade**: Convert project-local skills to global skills with automatic config format conversion (`.claude` → `.agent`)
3. **Multi-Tool Config Support**: Auto-detect and support Trae, Claude, Cursor, Opencode, Qwen Code, Crush configurations
4. **Version Management**: Track skill versions with automatic update detection and upgrade capabilities

**Non-Goals:**
- Building a package registry or repository hosting (skills remain in `~/.agents/skills`)
- Modifying existing skill content (only copy/upgrade)
- Version control for skill source code (version tracking only)
- Cross-tool skill synchronization beyond config format conversion

## Decisions

### Decision 1: Installation Source Strategy
**Choice**: Support three installation sources:
- GitHub repositories (e.g., `user/repo/skill-name`)
- Local paths (absolute or relative)
- Direct URLs to SKILL.md files

**Rationale**: Covers the most common skill distribution patterns while keeping implementation focused. GitHub is the primary distribution method for community skills.

**Alternatives Considered**: 
- Package registry (too complex for MVP)
- Git submodules (different use case)

### Decision 2: Version Tracking Mechanism
**Choice**: Store version in SKILL.md frontmatter as `metadata.version` (semver), with optional `metadata.updateUrl` for update detection.

**Rationale**: 
- Minimal change to existing skill format
- Version is part of skill metadata, easy to check and update
- `updateUrl` allows skills to point to their latest version info

**Alternatives Considered**:
- Separate metadata file (more complex, harder to discover)
- Git tags (only works for GitHub repos)

### Decision 3: Config Format Conversion Strategy
**Choice**: Create a mapping layer for config format conversion:
- `.claude` → `.agent`: Simple path transformation
- Multi-tool support via config templates

**Rationale**: Each tool has different config structures. A mapping approach allows clean separation and easy addition of new tools.

**Alternatives Considered**:
- Single unified config format (breaks tool-specific features)
- Manual conversion (defeats the purpose of automation)

### Decision 4: Upgrade vs. Install Separation
**Choice**: Keep install and upgrade as separate commands:
- `skill-hub install`: Install new skills
- `skill-hub upgrade`: Upgrade existing skills (local → global)
- `skill-hub update`: Check and apply version updates

**Rationale**: Clear separation of concerns. Users may want to upgrade without checking for version updates.

**Alternatives Considered**: Single `update` command (less explicit about intent)

### Decision 5: Dependency Management
**Choice**: Use `requests` for HTTP operations, subprocess-based git for GitHub repos.

**Rationale**: 
- `requests` is lightweight and well-established
- subprocess avoids gitpython dependency bloat while still supporting GitHub operations

**Alternatives Considered**: 
- `httpx` (async, overkill for CLI)
- `gitpython` (additional dependency when subprocess suffices)

## Risks / Trade-offs

**Risk 1: GitHub API Rate Limiting**
- **Mitigation**: Use unauthenticated requests with clear error messages, suggest authentication for higher limits

**Risk 2: Config Format Complexity**
- **Mitigation**: Start with core tools (Claude, Cursor), extensible architecture for new tools

**Risk 3: Version Conflict Resolution**
- **Mitigation**: Simple semver comparison, explicit user confirmation for upgrades

**Risk 4: Path Resolution Ambiguity**
- **Mitigation**: Clear documentation of global vs. local paths, explicit configuration option

**Risk 5: Backward Compatibility**
- **Mitigation**: Version field optional in SKILL.md, graceful degradation for skills without version info

## Migration Plan

**Deployment Steps**:
1. Add `version` field to SkillMetadata model
2. Create installer module with source handlers
3. Create upgrader module with config conversion logic
4. Create version module with update detection
5. Add CLI commands (install, upgrade, update)
6. Update discovery engine to include version info

**Rollback Strategy**: 
- All changes are additive (no breaking changes)
- Can remove new CLI commands if needed
- Existing skills without version info continue to work

**Open Questions**:
1. Should we support installing from local directories (not just GitHub)?
   - **Decision**: Yes, already included in scope
2. Should we create a skill index/registry?
   - **Decision**: No, out of scope for MVP
3. Should we support skill dependencies?
   - **Decision**: No, out of scope for MVP
4. Should we auto-backup skills before upgrade?
   - **Decision**: Yes, add as optional flag
