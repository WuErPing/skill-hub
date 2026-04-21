## Context

The current skill-hub CLI only supports a single installation path (`~/.agents/skills`) with basic tool-specific support. The existing implementation has:

- Single global skills directory (`~/.agents/skills`)
- Basic tool detection (Claude vs Opencode)
- One-way installation from GitHub/URL to local
- No support for project-private skills directories

Your flowchart shows a multi-layer architecture:
```
github --> public dirs (~/.agents/skills, ~/.claude/skills)
claude <--> standard (bidirectional config sync)
standard <--> private dirs (.agents/skills/private, etc.)
```

## Goals / Non-Goals

**Goals:**
1. Support multi-layer skill directories (public + private)
2. Enable project-local skills for team collaboration
3. Allow one-way sync from public to private (no auto-bi-sync)
4. Keep CLI commands simple and easy to understand
5. Support existing skill upgrades with version tracking

**Non-Goals:**
1. Automatic bidirectional sync between public and private (user must explicitly trigger)
2. Real-time synchronization
3. Conflict resolution for bidirectional edits

## Decisions

### Decision 1: Directory Structure
**Structure:**
```
~/.agents/skills/           # Public agent-level skills (global)
~/.claude/skills/          # Public tool-level skills (global)
.agents/skills/private/     # Project-private agent-level
.claude/skills/private/     # Project-private tool-level
.others/skills/private/     # Other project-specific locations
```

**Rationale:** 
- Clear separation between public (global) and private (project-local)
- Consistent naming across tools
- Extensible for future private locations

### Decision 2: CLI Command Structure
**Current commands:**
- `skill-hub install <source>` - Install to default path only
- `skill-hub list` - List skills from single directory
- `skill-hub compare` - Compare local vs global

**Proposed new commands:**
```bash
# Install with explicit target
skill-hub install <source> --to public      # Install to global (default)
skill-hub install <source> --to private     # Install to project-private

# List skills from specific directory
skill-hub list                              # List public only (default)
skill-hub list --all                        # List all directories
skill-hub list --public                     # Explicit public
skill-hub list --private                    # List private only

# Compare specific directories
skill-hub compare                           # Compare public vs current project
skill-hub compare --all                     # Compare all directories

# Sync commands (explicit, not automatic)
skill-hub sync <skill-name> --from public --to private
skill-hub sync <skill-name> --from private --to public

# Upgrade (existing skill to new location)
skill-hub upgrade <skill-name> --to private
```

**Rationale:**
- Simple, intuitive commands that match user mental model
- Explicit over implicit (no auto-bi-sync)
- Backward compatible (existing commands work as before)

### Decision 3: Priority System
When same skill exists in multiple directories:
```
Priority: private > public
```

**Rationale:** Project-specific skills override global skills, allowing customization while sharing base skills.

### Decision 4: Sync Direction
One-way sync only (no auto-bi-sync):
```
public --> private  (explicit user action)
private --> public  (explicit user action, rare)
```

**Rationale:** Prevents conflicts and maintains clear ownership of skills.

### Decision 5: Version Tracking
Keep existing version tracking but extend to support multiple directories:
- Store version in SKILL.md frontmatter
- Track which directory each skill comes from
- Show source when listing skills

## Risks / Trade-offs

**Risk 1: Directory discovery complexity**
- More directories to search = slower commands
- Mitigation: Cache directory structure, only scan when needed

**Risk 2: User confusion about which skill is being used**
- Multiple copies of same skill in different directories
- Mitigation: Clear indication of source when listing skills, priority system

**Risk 3: Sync command complexity**
- Need to handle version conflicts, file conflicts
- Mitigation: Start simple (copy only), add conflict resolution later if needed

## Migration Plan

**Phase 1: Directory Discovery**
- Add support for discovering private directories
- Update `list` command to show source directory

**Phase 2: Install Target**
- Add `--to public|private` flag to install command
- Default to public for backward compatibility

**Phase 3: Sync Commands**
- Add explicit sync commands
- One-way sync only (no auto-bi-sync)

**Phase 4: Priority System**
- Implement priority-based skill resolution
- Show which skill will be used when multiple exist

**Rollback Strategy:**
- Keep existing commands unchanged
- New functionality behind flags
- Can disable new behavior by not using new flags

## Open Questions

1. Should `skill-hub list` show all directories by default or just public?
   - **Decision:** Default to public, use `--all` for all directories

2. Should sync preserve version history?
   - **Decision:** Yes, copy version metadata during sync

3. What happens when syncing to existing skill?
   - **Decision:** Show diff, ask for confirmation (or use `--force` flag)

4. Should private skills inherit from public?
   - **Decision:** No, each skill is independent (keep simple)
