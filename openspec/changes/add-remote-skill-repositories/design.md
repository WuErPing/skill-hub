# Design Document

## Context

Skill-hub currently only manages skills from local agent configuration directories. Users must manually create or copy skills to their systems. This creates a gap for:
- **Community skill distribution**: Popular skills (like those from https://github.com/anthropics/skills) cannot be easily shared
- **Skill updates**: No mechanism to receive updates to community-maintained skills
- **Team collaboration**: Organizations cannot centrally distribute their skill libraries

This change adds support for pulling skills from remote Git repositories with automatic scheduled synchronization, enabling skill-hub to become a true package manager for AI agent skills.

**Stakeholders:**
- End users who want to use community skills
- Teams who want to share skills across organization
- Skill authors who want to distribute their skills

**Constraints:**
- Must remain lightweight (no heavy dependencies like Docker)
- Must work offline (daemon should gracefully handle no network)
- Must not break existing local skill workflows
- Must support cross-platform (macOS, Linux, Windows)

## Goals / Non-Goals

### Goals
- **Easy repository addition**: Simple command to add GitHub repositories
- **Automatic updates**: Scheduled sync to keep skills current
- **Conflict handling**: Smart resolution when local and remote skills collide
- **Performance**: Incremental sync using commit hashes
- **Reliability**: Graceful error handling for network issues

### Non-Goals (This Phase)
- **Skill versioning**: No support for pinning specific skill versions (future feature)
- **Dependency management**: No skill dependencies between repositories (future)
- **Skill marketplace**: No central registry or discovery service (future)
- **Custom protocols**: Only Git repositories supported (no npm, PyPI, etc.)
- **Bi-directional sync**: Only pull from remote, not push local skills to remote

## Decisions

### Decision 1: Git vs GitHub API

**Options:**

**A) Use Git CLI commands**
- **Pros**: Works with any Git hosting (GitHub, GitLab, self-hosted)
- **Pros**: Handles authentication via git credential helpers
- **Pros**: Reliable and well-tested
- **Cons**: Requires Git installed on system
- **Cons**: Spawning subprocesses adds complexity

**B) Use GitHub API**
- **Pros**: No Git installation required
- **Pros**: Direct file access via API
- **Cons**: GitHub-only, doesn't work with other Git hosts
- **Cons**: API rate limits (60 requests/hour unauthenticated)
- **Cons**: Complex authentication (OAuth, PAT)

**Decision: Git CLI (Option A)**

**Rationale:**
- Git is already widely installed on developer systems
- Supports any Git repository, not just GitHub
- Credential helper integration provides better security
- Shallow clone feature minimizes disk usage
- Can leverage Python's `subprocess` or `GitPython` library

### Decision 2: Scheduling Mechanism

**Options:**

**A) Python `schedule` library**
- **Pros**: Lightweight, pure Python
- **Pros**: Easy cron expression support
- **Cons**: Requires daemon process to stay running
- **Cons**: No persistence across restarts

**B) System cron/Task Scheduler**
- **Pros**: Native OS integration
- **Pros**: Runs even if skill-hub not running
- **Cons**: Platform-specific (cron vs Task Scheduler vs launchd)
- **Cons**: Requires root/admin for installation

**C) `APScheduler` library**
- **Pros**: Robust job scheduling with multiple backends
- **Pros**: Persistent job storage
- **Pros**: Good for complex schedules
- **Cons**: Heavier dependency
- **Cons**: Still needs daemon for in-process scheduler

**D) Hybrid: Daemon + systemd timer/launchd**
- **Pros**: Best of both worlds
- **Pros**: Daemon for development, system service for production
- **Pros**: Platform-native integration

**Decision: Hybrid approach (Option D)**

**Rationale:**
- Use Python `schedule` for daemon mode (development, simple use)
- Provide systemd timer (Linux) and launchd (macOS) templates for production
- Let users choose based on their needs
- Start simple with daemon, add system integration incrementally

### Decision 3: Repository Storage Location

**Options:**

**A) Clone to `~/.skills/repos/<repo-name>/`**
- Simple structure
- Easy to browse
- Name conflicts if multiple repos have same name

**B) Clone to `~/.skills/.skill-hub/repos/<repo-hash>/`**
- Hidden from users
- No name conflicts (hash-based)
- Metadata stored alongside

**C) System temp directory**
- Cleaned on reboot
- Must re-clone frequently
- Not suitable for incremental updates

**Decision: Option B - `~/.skills/.skill-hub/repos/<repo-hash>/`**

**Rationale:**
- Hash prevents naming conflicts
- Hidden directory keeps user's `~/.skills/` clean
- Persistent for incremental sync
- Metadata can be stored alongside in `meta.json`
- Repo hash = SHA-256 of repository URL

### Decision 4: Conflict Resolution Strategy

**Options:**

**A) Always prioritize remote (overwrite local)**
- Simple
- Users lose local modifications
- Not user-friendly

**B) Always prioritize local (skip remote)**
- Safe for users
- Defeats purpose of sync
- Users miss updates

**C) Configurable strategy**
- Flexible
- Can support multiple workflows
- Requires more code

**Decision: Configurable strategy (Option C)**

**Rationale:**
- Default to `remote-priority` for fresh installs (get community updates)
- Allow `local-priority` for users who customize skills
- Support `newest` (timestamp-based) for smart merge
- Support `manual` for interactive resolution
- Warn users when local modifications are overwritten

### Decision 5: Daemon Implementation

**Options:**

**A) Long-running Python process**
- Simple implementation
- Easy to debug
- Must handle signals properly
- PID file management needed

**B) Separate background service**
- Clean separation
- Better resource management
- More complex deployment

**C) No daemon, only manual pull**
- Simplest
- Users must remember to run
- No automatic updates

**Decision: Option A - Long-running Python process with optional system service**

**Rationale:**
- Start with simple daemon for development
- Add systemd/launchd integration for production
- Users can choose manual or automatic
- Keep implementation straightforward

## Technical Architecture

### Components

```
skill-hub (extended)
├── remote/                     # New: Remote repository management
│   ├── manager.py              # Clone, pull, update repositories
│   ├── scanner.py              # Extract skills from repos
│   └── metadata.py             # Track repo state (commits, syncs)
│
├── scheduler/                  # New: Cron scheduling
│   ├── cron.py                 # Cron expression parser
│   ├── daemon.py               # Background daemon process
│   └── systemd.py              # System service templates
│
├── sync/engine.py              # Modified: Add remote sync
├── models.py                   # Modified: Add RepositoryConfig
├── cli.py                      # Modified: Add repo, pull, daemon commands
└── config/                     # New: Configuration management
    └── loader.py               # Load and validate config
```

### Data Flow

**Repository Addition:**
```
1. User: skill-hub repo add https://github.com/anthropics/skills
2. Validate URL format
3. Test git clone (shallow)
4. Add to config.json
5. Run initial pull
```

**Manual Pull:**
```
1. User: skill-hub pull
2. For each enabled repository:
   a. Check cached repo exists
   b. Git pull (or clone if missing)
   c. Read current commit hash
   d. Compare with stored hash
   e. If changed: Extract and import skills
   f. Update metadata with new hash
3. Display summary
```

**Scheduled Sync:**
```
1. Daemon: Check cron schedule
2. If time matches schedule:
   a. Trigger pull operation
   b. Log sync result
   c. On error: Log and continue
3. Wait for next schedule
```

### Configuration Structure

```json
{
  "version": "1.0.0",
  "conflict_resolution": "remote-priority",
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
    "incremental": true,
    "check_permissions": true,
    "create_directories": true,
    "remote_priority": true
  },
  "daemon": {
    "enabled": false,
    "pid_file": "~/.skills/.skill-hub/daemon.pid"
  }
}
```

### Repository Metadata

```json
{
  "url": "https://github.com/anthropics/skills",
  "branch": "main",
  "commit_hash": "abc123def456...",
  "last_sync_at": "2026-01-30T10:30:00Z",
  "skills_imported": ["commit-helper", "weekly-report-helper"],
  "sync_count": 5,
  "last_error": null
}
```

## Risks / Trade-offs

### Risk 1: Git Not Installed

**Risk**: Users might not have Git installed

**Mitigation**:
- Check for git executable on first repo add
- Provide clear error message with installation instructions
- Consider bundling GitPython as alternative
- Document Git as system requirement

### Risk 2: Large Repository Performance

**Risk**: Cloning large repositories could be slow and consume disk space

**Mitigation**:
- Use shallow clone (--depth 1) by default
- Support sparse checkout for large repos (future)
- Show progress indicator during clone
- Allow users to configure depth

### Risk 3: Authentication Complexity

**Risk**: Private repositories require complex authentication

**Mitigation**:
- Start with public repositories only
- Support GitHub PAT via environment variable
- Leverage Git credential helpers
- Document authentication setup clearly

### Risk 4: Network Reliability

**Risk**: Network failures could break sync

**Mitigation**:
- Timeout for git operations (30s default)
- Retry logic for transient failures
- Graceful degradation (skip failed repo, continue)
- Clear error messages with suggested actions

### Risk 5: Daemon Lifecycle Management

**Risk**: Daemon process might not start/stop cleanly

**Mitigation**:
- PID file to track running daemon
- Signal handling for graceful shutdown
- Check for running daemon before starting new one
- Provide clear status command

### Trade-off: Simplicity vs Features

- **Trade-off**: Adding full daemon support increases complexity
- **Benefit**: Automatic updates without user intervention
- **Decision**: Start simple (manual pull), add daemon incrementally
- **Path**: Phase 1 = manual pull, Phase 2 = basic daemon, Phase 3 = system service

### Trade-off: Git Dependency vs Pure Python

- **Trade-off**: Requiring Git CLI adds external dependency
- **Benefit**: Robust, widely-available, supports all Git features
- **Decision**: Accept Git dependency, document as requirement
- **Rationale**: Developer audience likely has Git installed

## Migration Plan

### Phase 1: Manual Pull (This Change)
1. Add repository configuration
2. Implement git clone/pull
3. Add skill extraction from repos
4. Implement `skill-hub repo` commands
5. Implement `skill-hub pull` command
6. Basic conflict resolution

### Phase 2: Basic Daemon (Future)
1. Add Python `schedule` library
2. Implement simple daemon mode
3. Add PID file management
4. Basic schedule execution

### Phase 3: System Integration (Future)
1. Create systemd timer template
2. Create launchd plist template
3. Add install/uninstall commands
4. Platform detection logic

### Rollback Strategy
- Repository configuration is opt-in (no breaking changes)
- Users can disable repositories without removing them
- Daemon can be stopped and disabled
- Manual pull always available as fallback

## Open Questions

1. **Should we support GitLab/Bitbucket explicitly?**
   - Current decision: Git CLI supports any Git host automatically
   - No special handling needed unless API integration required

2. **How to handle skill dependencies?**
   - Current decision: Out of scope for this phase
   - Skills are independent, no dependency resolution

3. **Should we support skill version pinning?**
   - Current decision: Out of scope for this phase
   - Always pull latest from branch
   - Could add version tags support later

4. **Authentication for private repos?**
   - Current decision: Environment variable `SKILL_HUB_GITHUB_TOKEN`
   - Git credential helpers as fallback
   - Document setup process

5. **Repository structure flexibility?**
   - Current decision: Support `path` configuration
   - Scan for `<path>/*/SKILL.md` pattern
   - Document expected structure for skill authors
