# Change: Add Remote Skill Repositories with Cron Sync

## Why

Currently, skill-hub only discovers and syncs skills from local agent configurations. Users need to manually copy or create skills in their local directories. This creates friction when:
- **Sharing skills**: Teams want to distribute curated skill collections
- **Community skills**: Users want to benefit from community-maintained skill repositories (e.g., https://github.com/anthropics/skills)
- **Keeping updated**: Skills in remote repositories are updated but local copies become stale
- **Discovery**: Users are unaware of new skills available in community repositories

A remote repository integration with scheduled synchronization solves these problems by automatically pulling skills from configured GitHub repositories (like https://github.com/anthropics/skills) and keeping them up-to-date.

## What Changes

This change introduces remote skill repository support with automatic synchronization:

1. **Remote Repository Configuration**: Add repository list to config
   - Repository URL (e.g., `https://github.com/anthropics/skills`)
   - Optional branch specification (default: `main`)
   - Optional subdirectory path (e.g., `/skills`)
   - Enable/disable per repository
   - Authentication support for private repos

2. **Repository Cloning & Skill Extraction**: Pull skills from Git repositories
   - Clone or pull remote repositories to local cache
   - Extract skills from repository directory structure
   - Validate skill format before importing
   - Handle repository-specific skill organization

3. **Cron-Based Synchronization**: Scheduled automatic updates
   - Configurable sync schedule (cron expression)
   - Background sync daemon or systemd timer integration
   - Manual `skill-hub pull` command for immediate sync
   - Sync status tracking and logging

4. **Conflict Resolution for Remote Skills**: Handle name conflicts
   - New `remote-priority` conflict resolution strategy
   - Track skill source (local vs remote repository)
   - Warn users about local modifications overwritten by remote

## Impact

### Affected Specs
- **NEW**: `specs/remote-repositories/spec.md` - Remote repository management
- **NEW**: `specs/cron-sync/spec.md` - Scheduled synchronization
- **MODIFIED**: `specs/skill-sync/spec.md` - Extend sync to include remote sources

### Affected Code
- **NEW**: Remote repository adapter (`src/skill_hub/remote/`)
- **NEW**: Cron scheduler (`src/skill_hub/scheduler/`)
- **MODIFIED**: Configuration model (`src/skill_hub/models.py`)
- **MODIFIED**: Sync engine (`src/skill_hub/sync/engine.py`)
- **MODIFIED**: CLI commands (`src/skill_hub/cli.py`)
- **NEW**: Tests for remote repository and scheduling

### User Impact
- **Breaking**: None (additive feature)
- **Migration**: Users can optionally add repository URLs to config
- **New commands**: 
  - `skill-hub repo add <url>` - Add remote repository
  - `skill-hub repo list` - List configured repositories
  - `skill-hub pull` - Pull from all remote repositories
  - `skill-hub schedule` - Configure sync schedule
- **Configuration**: New `repositories` section in config.json

### Example Configuration
```json
{
  "version": "1.0.0",
  "conflict_resolution": "newest",
  "repositories": [
    {
      "url": "https://github.com/anthropics/skills",
      "enabled": true,
      "branch": "main",
      "path": "",
      "sync_schedule": "0 */6 * * *"
    }
  ],
  "sync": {
    "remote_priority": true,
    "incremental": true
  }
}
```
