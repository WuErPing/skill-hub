## Why

The current skill installation system only supports a single global directory (`~/.agents/skills`) and tool-specific directories (`~/.claude/skills`, `~/.opencode/skills`). This doesn't support a multi-layer architecture where users can have both public skills (shared across projects) and private skills (project-specific). The proposed refactoring enables a hierarchical skill installation system that supports:

- Public skills in standard locations (`~/.agents/skills`, `~/.claude/skills`)
- Private skills in project-specific directories (`.agents/skills/private`, `.claude/skills/private`, etc.)

This allows teams to share public skills while maintaining project-specific private skills without conflicts.

## What Changes

### New Capabilities
- **Multi-layer skill directories**: Support for public and private skill directories at multiple levels
- **Bidirectional sync**: Skills can be synced between public and private directories
- **Priority-based resolution**: When same skill exists in multiple locations, use priority order (private > public)
- **Project-local skills**: Skills stored in project-specific directories for team collaboration

### Modified Capabilities
- **skill-installation**: Current spec only supports single installation path. Need to extend to support multiple paths with priority.
- **multi-tool-config-support**: Current spec assumes single tool-specific directory. Need to extend to support project-local config locations.

## Capabilities

### New Capabilities
- `multi-layer-skill-directories`: Support for public and private skill directories at multiple levels
  - `~/.agents/skills` (public agent-level)
  - `.agents/skills/private` (project-private agent-level)
  - `~/.claude/skills` (public tool-level)
  - `.claude/skills/private` (project-private tool-level)
  - Other private locations (`.others/skills/private`, etc.)
  
- `skill-directory-sync`: Bidirectional sync between public and private directories
  - Copy skill from public to private for customization
  - Sync updates from public to private
  
- `priority-based-skill-resolution`: When same skill exists in multiple locations, use priority order
  - Private directories take precedence over public
  - Project-local takes precedence over global

### Modified Capabilities
- `skill-installation`: 
  - Current: Single installation path (`~/.agents/skills`)
  - Modified: Multiple installation paths with priority ordering
  - Add `--private` flag to install to project-local private directory
  - Add `--public` flag to explicitly install to public directory
  
- `multi-tool-config-support`:
  - Current: Single tool-specific directory
  - Modified: Support project-local config locations (`.claude/skills/private`, etc.)

## Impact

### Affected Code
- `skill-hub install` command: Need to support multiple destination paths
- `skill-hub list` command: Need to show skills from all directories with priority indicators
- `skill-hub upgrade` command: Need to handle sync between public and private
- Config resolution logic: Need to search multiple directories with priority

### New Dependencies
- None expected

### Breaking Changes
- None intended. This is an additive change that extends existing functionality.
