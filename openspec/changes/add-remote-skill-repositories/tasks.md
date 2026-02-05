# Implementation Tasks

## 1. Configuration and Data Models

- [x] 1.1 Add `RepositoryConfig` dataclass to models.py
- [x] 1.2 Add `repositories` field to Config dataclass
- [x] 1.3 Add `remote_priority` to sync configuration
- [ ] 1.4 Create configuration schema validation
- [ ] 1.5 Add configuration migration for existing users
- [ ] 1.6 Write unit tests for new models

## 2. Remote Repository Manager

- [x] 2.1 Create `src/skill_hub/remote/` module
- [x] 2.2 Implement `RepositoryManager` class
- [x] 2.3 Add Git clone functionality with shallow clones
- [x] 2.4 Add Git pull/update functionality
- [x] 2.5 Implement repository hash computation
- [x] 2.6 Add authentication support (GitHub PAT from env var)
- [x] 2.7 Create repository metadata storage (meta.json)
- [x] 2.8 Add commit hash tracking for incremental sync
- [ ] 2.9 Write unit tests for repository manager

## 3. Skill Extraction from Repositories

- [x] 3.1 Create `RepositorySkillScanner` class
- [x] 3.2 Implement skill discovery in repository directories
- [x] 3.3 Add support for subdirectory paths
- [x] 3.4 Integrate with existing skill parser
- [x] 3.5 Add skill source tracking (remote metadata)
- [x] 3.6 Handle invalid skills gracefully
- [ ] 3.7 Write unit tests for skill extraction

## 4. Repository CLI Commands

- [x] 4.1 Add `repo` command group to CLI
- [x] 4.2 Implement `skill-hub repo add <url>` command
- [x] 4.3 Implement `skill-hub repo list` command
- [x] 4.4 Implement `skill-hub repo remove <url>` command
- [ ] 4.5 Implement `skill-hub repo disable <url>` command
- [ ] 4.6 Implement `skill-hub repo enable <url>` command
- [x] 4.7 Add URL validation and accessibility testing
- [x] 4.8 Add rich table output for repo list

## 5. Pull Command

- [x] 5.1 Implement `skill-hub pull` command
- [x] 5.2 Add pull from all repositories
- [x] 5.3 Add pull from specific repository
- [x] 5.4 Integrate with sync engine
- [x] 5.5 Add progress indicators for each repository
- [x] 5.6 Display summary of pulled skills
- [x] 5.7 Handle errors and continue with remaining repos

## 6. Conflict Resolution Enhancement

- [x] 6.1 Add `remote-priority` conflict resolution strategy
- [x] 6.2 Add `local-priority` conflict resolution strategy
- [x] 6.3 Extend existing conflict detector for remote skills
- [x] 6.4 Track skill source (local vs remote) in metadata
- [ ] 6.5 Implement conflict warning for overwritten local skills
- [ ] 6.6 Write tests for conflict resolution scenarios

## 7. Cron Scheduling System

- [ ] 7.1 Add `schedule` or `APScheduler` dependency to pyproject.toml
- [ ] 7.2 Create `src/skill_hub/scheduler/` module
- [ ] 7.3 Implement cron expression parser and validator
- [ ] 7.4 Create schedule configuration loader
- [ ] 7.5 Implement task scheduler with cron support
- [ ] 7.6 Add per-repository schedule override
- [ ] 7.7 Write unit tests for scheduler

## 8. Background Daemon

- [ ] 8.1 Create daemon module with process management
- [ ] 8.2 Implement `skill-hub daemon start` command
- [ ] 8.3 Implement `skill-hub daemon stop` command
- [ ] 8.4 Implement `skill-hub daemon status` command
- [ ] 8.5 Add PID file management for daemon
- [ ] 8.6 Add graceful shutdown handling
- [ ] 8.7 Implement scheduled sync execution
- [ ] 8.8 Add error handling and retry logic

## 9. System Integration

- [ ] 9.1 Create systemd service file template (Linux)
- [ ] 9.2 Create launchd plist template (macOS)
- [ ] 9.3 Implement `skill-hub daemon install` command
- [ ] 9.4 Implement `skill-hub daemon uninstall` command
- [ ] 9.5 Add platform detection (Linux/macOS/Windows)
- [ ] 9.6 Document system service installation

## 10. Sync History and Logging

- [ ] 10.1 Extend sync history to include remote syncs
- [ ] 10.2 Add trigger type field (manual/scheduled/remote)
- [ ] 10.3 Update `skill-hub sync --history` to show remote syncs
- [ ] 10.4 Add filtering by source type
- [ ] 10.5 Implement detailed error logging
- [ ] 10.6 Add optional system notifications (macOS/Linux)

## 11. Incremental Sync Optimization

- [ ] 11.1 Implement commit hash comparison
- [ ] 11.2 Skip unchanged repositories
- [ ] 11.3 Add selective skill update based on checksums
- [ ] 11.4 Optimize git operations (shallow clone, sparse checkout)
- [ ] 11.5 Add performance metrics logging

## 12. Error Handling and Resilience

- [ ] 12.1 Add network timeout handling
- [ ] 12.2 Add authentication error detection
- [ ] 12.3 Add repository not found handling
- [ ] 12.4 Implement fallback to re-clone on pull failure
- [ ] 12.5 Add retry logic for transient failures
- [ ] 12.6 Ensure daemon continues on single repo failure

## 13. Testing

- [ ] 13.1 Write unit tests for repository manager
- [ ] 13.2 Write unit tests for skill extraction
- [ ] 13.3 Write unit tests for scheduler
- [ ] 13.4 Write integration tests for full pull workflow
- [ ] 13.5 Write tests for conflict resolution
- [ ] 13.6 Test daemon start/stop functionality
- [ ] 13.7 Test error scenarios (network, auth, etc.)
- [ ] 13.8 Achieve 80%+ code coverage for new code

## 14. Documentation

- [ ] 14.1 Update README with remote repository features
- [ ] 14.2 Document `skill-hub repo` commands
- [ ] 14.3 Document `skill-hub pull` command
- [ ] 14.4 Document `skill-hub daemon` commands
- [ ] 14.5 Add configuration examples for repositories
- [ ] 14.6 Document cron expression format
- [ ] 14.7 Create troubleshooting guide for remote sync
- [ ] 14.8 Add examples with https://github.com/anthropics/skills

## 15. Validation and Polish

- [ ] 15.1 Test with real GitHub repositories
- [ ] 15.2 Test with https://github.com/anthropics/skills specifically
- [ ] 15.3 Verify daemon runs reliably on all platforms
- [ ] 15.4 Optimize performance for large repositories
- [ ] 15.5 Polish CLI output and error messages
- [ ] 15.6 Final code review and cleanup
