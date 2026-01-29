## ADDED Requirements

### Requirement: Central Skill Repository Management

The system SHALL maintain a central skill repository at `~/.skills/` that serves as the single source of truth for all skills across agents.

#### Scenario: Initialize skill hub directory

- **WHEN** the sync engine runs for the first time
- **THEN** it SHALL create `~/.skills/` directory if it doesn't exist
- **AND** it SHALL create a `.skill-hub/` subdirectory for metadata
- **AND** it SHALL set appropriate permissions (user read/write)

#### Scenario: Store skill in central repository

- **WHEN** a skill is synced to the hub
- **THEN** it SHALL be copied to `~/.skills/<skill-name>/SKILL.md`
- **AND** it SHALL preserve the original file content exactly
- **AND** it SHALL not modify frontmatter or markdown content

#### Scenario: Track skill metadata

- **WHEN** a skill is added to the hub
- **THEN** the system SHALL create `~/.skills/.skill-hub/<skill-name>.json` with:
  - Original source locations (array of paths)
  - Last sync timestamp
  - Source agent types
  - Checksum of skill content
  - Sync history (last 10 syncs)

### Requirement: Bi-Directional Skill Synchronization

The system SHALL synchronize skills between agent configuration directories and the central hub in both directions.

#### Scenario: Pull skills from agents to hub

- **WHEN** the user runs `skill-hub sync --pull`
- **THEN** the system SHALL discover all skills from agent configs
- **AND** it SHALL copy new or updated skills to `~/.skills/`
- **AND** it SHALL update metadata for each synced skill

#### Scenario: Push skills from hub to agents

- **WHEN** the user runs `skill-hub sync --push`
- **THEN** the system SHALL read all skills from `~/.skills/`
- **AND** it SHALL copy them to all configured agent directories
- **AND** it SHALL create agent-specific directory structure if needed

#### Scenario: Bi-directional sync (default)

- **WHEN** the user runs `skill-hub sync` without flags
- **THEN** the system SHALL first pull skills from agents to hub
- **AND** it SHALL then push all hub skills to agents
- **AND** it SHALL resolve conflicts using conflict resolution strategy

### Requirement: Conflict Detection and Resolution

The system SHALL detect when the same skill has different content in multiple locations and resolve conflicts according to configured strategy.

#### Scenario: Detect content conflict

- **WHEN** a skill exists in multiple locations with different content
- **THEN** the system SHALL compute checksums for each version
- **AND** it SHALL identify mismatches
- **AND** it SHALL report all conflicting versions with their locations

#### Scenario: Resolve conflict using newest timestamp

- **WHEN** conflict resolution strategy is "newest" (default)
- **THEN** the system SHALL compare file modification timestamps
- **AND** it SHALL keep the version with the most recent timestamp
- **AND** it SHALL log the decision with source information

#### Scenario: Resolve conflict using manual selection

- **WHEN** conflict resolution strategy is "manual"
- **THEN** the system SHALL prompt the user with all versions
- **AND** it SHALL display diff between versions
- **AND** it SHALL wait for user to select which version to keep

#### Scenario: Resolve conflict using hub priority

- **WHEN** conflict resolution strategy is "hub-priority"
- **THEN** the system SHALL always keep the version from `~/.skills/`
- **AND** it SHALL overwrite conflicting versions in agent configs
- **AND** it SHALL log overwritten files

### Requirement: Incremental Sync Optimization

The system SHALL only sync skills that have changed since the last synchronization to improve performance.

#### Scenario: Skip unchanged skills

- **WHEN** a skill's content checksum matches the stored checksum
- **THEN** the system SHALL skip copying that skill
- **AND** it SHALL log "skipped (unchanged)"
- **AND** it SHALL not update the metadata timestamp

#### Scenario: Detect modified skill

- **WHEN** a skill's content checksum differs from stored checksum
- **THEN** the system SHALL mark it as modified
- **AND** it SHALL sync the new content
- **AND** it SHALL update metadata with new checksum and timestamp

#### Scenario: Detect new skill

- **WHEN** a skill exists in source but not in destination
- **THEN** the system SHALL mark it as new
- **AND** it SHALL copy it to destination
- **AND** it SHALL create new metadata entry

#### Scenario: Handle deleted skill

- **WHEN** a skill exists in destination but not in any source
- **THEN** the system SHALL mark it as orphaned
- **AND** it SHALL not delete it automatically
- **AND** it SHALL report it to user for manual review

### Requirement: Sync History and Auditing

The system SHALL maintain a history of synchronization operations for auditing and debugging.

#### Scenario: Log sync operation

- **WHEN** a sync operation completes
- **THEN** the system SHALL append to `~/.skills/.skill-hub/sync.log` with:
  - Timestamp
  - Operation type (pull/push/bi-directional)
  - Skills synced (count)
  - Conflicts detected and resolved
  - Errors encountered

#### Scenario: Query sync history

- **WHEN** the user runs `skill-hub sync --history`
- **THEN** the system SHALL display last 20 sync operations
- **AND** it SHALL show summary statistics for each sync
- **AND** it SHALL allow filtering by date range or operation type

#### Scenario: Rollback to previous sync

- **WHEN** the user runs `skill-hub sync --rollback`
- **THEN** the system SHALL restore skill states from the previous sync
- **AND** it SHALL revert checksum metadata
- **AND** it SHALL log the rollback operation
