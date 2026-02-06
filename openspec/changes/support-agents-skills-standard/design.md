# Design: `.agents/skills` Standard Support

## Architecture Overview

The `.agents/skills/` standard introduces a shared, agent-agnostic location for skills that complements (not replaces) existing agent-specific directories.

### Current Architecture

```
Project Root
├── .cursor/skills/          # Cursor-specific (existing)
├── .claude/skills/          # Claude-specific (existing)
├── .qoder/skills/           # Qoder-specific (existing)
└── .opencode/skills/        # OpenCode-specific (existing)

~/.skills/                   # Central hub (existing)
```

### Proposed Architecture

```
Project Root
├── .agents/skills/          # NEW: Shared location for all agents
├── .cursor/skills/          # Cursor-specific (existing)
├── .claude/skills/          # Claude-specific (existing)
├── .qoder/skills/           # Qoder-specific (existing)
└── .opencode/skills/        # OpenCode-specific (existing)

~/.skills/                   # Central hub (existing)
```

## Component Changes

### 1. AgentAdapter Base Class

**Current Behavior**:
- `get_all_search_paths()` returns project-local (`.cursor/`) + global (`~/.cursor/`)

**New Behavior**:
- `get_all_search_paths()` returns `.agents/skills/` + project-local (`.cursor/`) + global (`~/.cursor/`)
- Add new method: `get_shared_skills_path()` to discover `.agents/skills/`

### 2. DiscoveryEngine

**Current Behavior**:
- Scans `<base_path>/skills/` for SKILL.md files

**New Behavior**:
- Unchanged - DiscoveryEngine already handles arbitrary paths
- Adapters will provide `.agents/skills/` as an additional search path

### 3. Configuration

Add optional config flag to control write behavior:

```json
{
  "agents": {
    "cursor": {
      "enabled": true,
      "global_path": null,
      "use_shared_skills": true  // NEW: write to .agents/skills instead of .cursor/skills
    }
  }
}
```

## Discovery Flow

### Before (Current)

1. Adapter's `get_all_search_paths()` returns:
   - Project-local: `.cursor/skills/`
   - Global: `~/.cursor/skills/`

2. DiscoveryEngine scans each path for `SKILL.md` files

3. Skills are registered with source tracking

### After (Proposed)

1. Adapter's `get_all_search_paths()` returns:
   - **Shared: `.agents/skills/`** ← NEW
   - Project-local: `.cursor/skills/`
   - Global: `~/.cursor/skills/`

2. DiscoveryEngine scans each path (no changes needed)

3. Skills are registered with source tracking (e.g., `source.agent = "shared"` for `.agents/skills/`)

## Write Flow

### Sync Push (Hub → Agents)

**Default behavior** (backward compatible):
```python
# For each agent:
write_to(f"~/.{agent}/skills/{skill_name}/SKILL.md")
```

**Optional behavior** (with `use_shared_skills: true`):
```python
# Write to shared location instead
write_to(f"{project_root}/.agents/skills/{skill_name}/SKILL.md")
```

## Path Resolution Strategy

### Priority Order

When the same skill exists in multiple locations:

1. `.agents/skills/<skill>/SKILL.md`
2. `.cursor/skills/<skill>/SKILL.md` (or agent-specific)
3. `~/.cursor/skills/<skill>/SKILL.md` (global)

Use existing conflict resolution (newest, manual, hub-priority, etc.)

### Implementation

```python
class AgentAdapter:
    def get_all_search_paths(self) -> List[Path]:
        paths = []
        
        # 1. Shared skills (highest priority)
        shared_path = self.get_shared_skills_path()
        if shared_path and shared_path.exists():
            paths.append(shared_path)
        
        # 2. Project-local paths
        paths.extend(self.get_project_paths())
        
        # 3. Global path
        global_path = self.get_global_path()
        if global_path.exists() or self.config.sync.get("create_directories", True):
            paths.append(global_path)
        
        return paths
    
    def get_shared_skills_path(self) -> Optional[Path]:
        """Get shared .agents/skills path if it exists in project."""
        git_root = find_git_root()
        if git_root:
            shared_dir = git_root / ".agents" / "skills"
            return shared_dir if shared_dir.exists() else None
        return None
```

## Backward Compatibility

✅ **Fully backward compatible**:
- Existing projects without `.agents/skills/` work exactly as before
- No changes to default write behavior
- Agent-specific directories still prioritized in discovery order

## Testing Strategy

### Unit Tests

1. Test `get_shared_skills_path()` finds `.agents/skills/` in project root
2. Test `get_all_search_paths()` includes shared path when present
3. Test discovery works with skills in `.agents/skills/`
4. Test conflict resolution between `.agents/skills/` and agent-specific paths

### Integration Tests

1. Create test project with `.agents/skills/`
2. Verify `skill-hub discover` finds shared skills
3. Verify `skill-hub sync --pull` imports shared skills
4. Verify `skill-hub sync --push` with `use_shared_skills: true` writes to shared location

### Edge Cases

1. `.agents/skills/` exists but is empty
2. Same skill in both `.agents/skills/` and `.cursor/skills/`
3. `.agents/` directory exists but `skills/` subdirectory doesn't
4. No git root (non-git project)

## Migration Path

For projects wanting to adopt `.agents/skills/`:

1. Create `.agents/skills/` directory
2. Optionally move skills from `.cursor/skills/` → `.agents/skills/`
3. Update config: `"use_shared_skills": true`
4. Run `skill-hub sync --push` to write to new location

**Note**: Migration is optional and not part of this change.
