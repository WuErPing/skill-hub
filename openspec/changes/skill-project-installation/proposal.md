## Why

The current skill-hub tool only provides read-only operations (list, view) on skills from `~/.agents/skills`. Users need a complete skill lifecycle management system that includes:

1. **Installation**: One-click installation of individual skills from external sources (GitHub, local files, etc.)
2. **Upgrade Path**: Ability to upgrade local skills to global skills (for multi-tool compatibility)
3. **Multi-Tool Support**: Native support for Trae, Claude, Cursor, Opencode, Qwen Code, Crush with proper config format detection
4. **Version Management**: Automatic version detection and updates for skills

Without these capabilities, skill-hub remains a discovery tool rather than a complete skill lifecycle manager.

## What Changes

### New Capabilities
- **Skill Installation**: Install a single skill from various sources (GitHub repo, local path, URL)
- **Global Skill Upgrade**: Convert project-local skills to global skills with automatic config format conversion
- **Multi-Tool Config Support**: Auto-detect and support `.claude`, `.agent`, and other tool configs
- **Version Management**: Track skill versions, detect updates, and perform automatic upgrades

### Breaking Changes
- None. This is purely additive functionality.

## Capabilities

### New Capabilities
- `skill-installation`: Install skills from external sources (GitHub repos, local paths, URLs) into the skills directory
- `global-skill-upgrade`: Upgrade project-local skills to global skills with automatic config format conversion (`.claude` → `.agent`)
- `multi-tool-config-support`: Native support for multiple tool configurations (Trae, Claude, Cursor, Opencode, Qwen Code, Crush)
- `version-management`: Built-in version tracking with automatic update detection and skill version validation

### Modified Capabilities
- None. This change introduces entirely new capabilities without modifying existing behavior.

## Impact

### Affected Code
- **New CLI Commands**: `skill-hub install`, `skill-hub upgrade`, `skill-hub update`
- **New Modules**: 
  - `skill_hub/installer.py`: Installation logic and source handlers
  - `skill_hub/upgrader.py`: Global skill upgrade with config conversion
  - `skill_hub/version.py`: Version tracking and update detection
- **Modified Modules**:
  - `skill_hub/models.py`: Add version field to SkillMetadata
  - `skill_hub/discovery/engine.py`: Enhance discovery to include version info

### Dependencies
- **New**: `requests` (for downloading from URLs/GitHub)
- **New**: `gitpython` or subprocess-based git operations (for GitHub repos)
- **Existing**: click, rich, pyyaml (already in pyproject.toml)

### APIs
- New CLI surface area for installation, upgrade, and update commands
- Internal API for version comparison and validation
