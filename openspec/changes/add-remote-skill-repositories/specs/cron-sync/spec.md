## ADDED Requirements

### Requirement: Cron Schedule Configuration

The system SHALL allow users to configure automatic synchronization schedules using cron expressions.

#### Scenario: Configure global sync schedule

- **WHEN** a user sets `sync_schedule` in config.json
- **THEN** the system SHALL accept standard cron expressions (5 fields)
- **AND** it SHALL validate the cron syntax before accepting
- **AND** it SHALL use this schedule for all enabled repositories

#### Scenario: Configure per-repository schedule

- **WHEN** a repository has its own `sync_schedule` field
- **THEN** the system SHALL use repository-specific schedule over global
- **AND** it SHALL support disabling auto-sync with empty string or null

#### Scenario: Default sync schedule

- **WHEN** no sync schedule is configured
- **THEN** the system SHALL not enable automatic synchronization
- **AND** it SHALL only sync when manually triggered via `skill-hub pull`

### Requirement: Manual Pull Command

The system SHALL provide a command to manually pull skills from all remote repositories.

#### Scenario: Pull from all repositories

- **WHEN** the user runs `skill-hub pull`
- **THEN** the system SHALL sync from all enabled remote repositories
- **AND** it SHALL display progress for each repository
- **AND** it SHALL show summary of skills pulled

#### Scenario: Pull from specific repository

- **WHEN** the user runs `skill-hub pull <url>`
- **THEN** the system SHALL sync only from the specified repository
- **AND** it SHALL report if repository URL is not configured

#### Scenario: Pull with conflict resolution

- **WHEN** pulling skills conflicts with local skills
- **THEN** the system SHALL apply configured conflict resolution strategy
- **AND** it SHALL use `remote-priority` if configured in sync settings

### Requirement: Background Sync Daemon

The system SHALL provide a background service for scheduled synchronization.

#### Scenario: Start sync daemon

- **WHEN** the user runs `skill-hub daemon start`
- **THEN** the system SHALL start a background process
- **AND** it SHALL check schedule configuration
- **AND** it SHALL begin scheduling sync tasks based on cron expressions

#### Scenario: Stop sync daemon

- **WHEN** the user runs `skill-hub daemon stop`
- **THEN** the system SHALL gracefully stop the background process
- **AND** it SHALL complete any in-progress sync before stopping

#### Scenario: Check daemon status

- **WHEN** the user runs `skill-hub daemon status`
- **THEN** the system SHALL report whether daemon is running
- **AND** it SHALL show next scheduled sync time
- **AND** it SHALL display last sync timestamp

#### Scenario: Daemon on system startup

- **WHEN** system starts and daemon is enabled
- **THEN** the system SHALL auto-start via systemd timer (Linux) or launchd (macOS)
- **AND** it SHALL provide installation command: `skill-hub daemon install`

### Requirement: Sync History and Logging

The system SHALL maintain detailed logs of scheduled and manual synchronizations.

#### Scenario: Log sync operations

- **WHEN** a sync operation occurs (manual or scheduled)
- **THEN** the system SHALL append to `~/.skills/.skill-hub/sync.log` with:
  - Timestamp
  - Trigger type (manual/scheduled)
  - Repository URLs synced
  - Skills pulled count
  - Errors encountered

#### Scenario: View sync history

- **WHEN** the user runs `skill-hub sync --history`
- **THEN** the system SHALL display last 20 sync operations
- **AND** it SHALL include both local and remote syncs
- **AND** it SHALL allow filtering by source type

#### Scenario: Sync failure notification

- **WHEN** a scheduled sync fails
- **THEN** the system SHALL log detailed error information
- **AND** it SHALL optionally notify user via system notification (if configured)
- **AND** it SHALL retry on next scheduled time

### Requirement: Incremental Remote Sync

The system SHALL only pull changed skills from remote repositories to optimize performance.

#### Scenario: Detect repository changes via commit hash

- **WHEN** syncing a repository
- **THEN** the system SHALL fetch latest commit hash
- **AND** if hash matches stored hash, it SHALL skip pull
- **AND** if hash differs, it SHALL pull and extract skills

#### Scenario: Selective skill update

- **WHEN** repository content changes
- **THEN** the system SHALL only update skills that changed
- **AND** it SHALL compute checksums to detect skill modifications
- **AND** it SHALL skip unchanged skills

### Requirement: Conflict Resolution for Remote Skills

The system SHALL handle conflicts between local skills and remote repository skills.

#### Scenario: Remote priority strategy

- **WHEN** conflict resolution is set to "remote-priority"
- **THEN** the system SHALL always use version from remote repository
- **AND** it SHALL warn if overwriting locally modified skills

#### Scenario: Local priority strategy

- **WHEN** conflict resolution is set to "local-priority"
- **THEN** the system SHALL keep local version
- **AND** it SHALL log that remote version was skipped

#### Scenario: Newest priority strategy

- **WHEN** conflict resolution is set to "newest"
- **THEN** the system SHALL compare modification timestamps
- **AND** it SHALL keep the version with most recent timestamp
- **AND** it SHALL log the decision

#### Scenario: Manual conflict resolution

- **WHEN** conflict resolution is set to "manual"
- **THEN** the system SHALL prompt user to choose version
- **AND** it SHALL show diff between local and remote
- **AND** it SHALL wait for user decision before proceeding

### Requirement: Network and Error Handling

The system SHALL handle network failures and git errors gracefully during scheduled syncs.

#### Scenario: Handle network timeout

- **WHEN** git clone or pull times out
- **THEN** the system SHALL log timeout error
- **AND** it SHALL skip that repository
- **AND** it SHALL continue with remaining repositories

#### Scenario: Handle authentication failure

- **WHEN** repository requires authentication but token is invalid
- **THEN** the system SHALL log authentication error
- **AND** it SHALL not retry until token is updated
- **AND** it SHALL notify user of authentication issue

#### Scenario: Handle repository not found

- **WHEN** repository URL returns 404
- **THEN** the system SHALL log repository not found error
- **AND** it SHALL suggest disabling or removing the repository
- **AND** it SHALL continue with other repositories
