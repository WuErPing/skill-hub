# Proposal: Support `.agents/skills` Standard Directory

## Problem Statement

Currently, skill-hub only discovers skills from agent-specific directories (`.cursor/skills/`, `.claude/skills/`, etc.) and a global hub (`~/.skills/`). However, there is an emerging standard for a unified, agent-agnostic directory: `.agents/skills/`.

This standard would allow:
- **Single source of truth**: One directory for all agents in a project
- **Simplified onboarding**: New team members only need to know about `.agents/skills/`
- **Agent-agnostic**: Skills work across all AI coding agents without duplication
- **Better IDE integration**: Standard location for tooling to discover skills

## Proposed Solution

Add support for discovering skills from `.agents/skills/` directory structure, treating it as a shared, agent-agnostic location that all adapters can read from and write to.

### Key Design Decisions

1. **Discovery Priority**: `.agents/skills/` should be discovered alongside (not instead of) existing agent-specific paths
2. **Write Behavior**: When syncing to agents, skills should still go to agent-specific directories (`.cursor/skills/`, etc.) unless explicitly configured
3. **Pull Behavior**: When pulling from agents, check `.agents/skills/` in addition to agent-specific paths
4. **Conflict Resolution**: If the same skill exists in both `.agents/skills/` and agent-specific path, use existing conflict resolution strategy (newest by default)

## Scope

This change adds a new standard path for skill discovery without removing or breaking existing agent-specific paths. It's an additive enhancement that makes skill-hub more flexible and future-proof.

## Out of Scope

- Migrating existing skills from agent-specific paths to `.agents/skills/`
- Removing support for agent-specific directories
- Automatic de-duplication across `.agents/skills/` and agent-specific paths
- Configuration UI for choosing write destination

## Success Criteria

- [ ] Skills in `.agents/skills/<skill-name>/SKILL.md` are discovered by all adapters
- [ ] `skill-hub discover` includes skills from `.agents/skills/`
- [ ] `skill-hub sync --pull` pulls skills from `.agents/skills/` into hub
- [ ] `skill-hub sync --push` can optionally push to `.agents/skills/` (via config)
- [ ] Health checks report on `.agents/skills/` availability
- [ ] Documentation updated to explain the new standard path

## Dependencies

None. This is an isolated enhancement to the adapter and discovery subsystems.

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Confusion between `.agents/skills/` and agent-specific paths | Medium | Clear documentation explaining when to use each |
| Duplication if skills exist in multiple locations | Low | Existing conflict resolution handles this |
| Breaking changes to adapter interface | Medium | Make `.agents/skills/` support opt-in via base adapter |

## Alternative Approaches Considered

1. **Replace agent-specific paths entirely**: Too disruptive, breaks existing setups
2. **Only support `.agents/skills/` for new projects**: Inconsistent behavior
3. **Make `.agents/skills/` the only writable path**: Forces migration, rejected

## Timeline Estimate

- Design & spec: 1 day
- Implementation: 2-3 days
- Testing & validation: 1 day
- Documentation: 1 day

**Total**: ~5-6 days
