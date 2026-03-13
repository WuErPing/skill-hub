## ADDED Requirements

### Requirement: Global skill upgrade command
The system SHALL provide a `skill-hub upgrade` command to upgrade local skills to global skills.

#### Scenario: Upgrade skill with config conversion
- **WHEN** user runs `skill-hub upgrade skill-name`
- **THEN** system converts config format from `.claude` to `.agent`
- **AND THEN** skill is moved to global skills directory

#### Scenario: Upgrade skill with version update
- **WHEN** user runs `skill-hub upgrade skill-name`
- **THEN** system checks for version updates
- **AND THEN** if newer version exists, system upgrades to new version

#### Scenario: Handle skill not found
- **WHEN** user runs `skill-hub upgrade nonexistent-skill`
- **THEN** system displays clear error message: "Skill not found"

### Requirement: Config format conversion
The system SHALL automatically convert config formats during upgrade.

#### Scenario: Convert .claude to .agent
- **WHEN** user upgrades a skill with `.claude` config
- **THEN** system converts to `.agent` format
- **AND THEN** original `.claude` config is backed up

#### Scenario: Preserve skill metadata during conversion
- **WHEN** user upgrades a skill
- **THEN** system preserves all skill metadata (name, description, license, compatibility)

### Requirement: Upgrade feedback
The system SHALL provide clear feedback during upgrade.

#### Scenario: Show upgrade progress
- **WHEN** user runs upgrade command
- **THEN** system displays: "Upgrading skill 'name'..."

#### Scenario: Show successful upgrade
- **WHEN** skill is successfully upgraded
- **THEN** system displays: "Successfully upgraded skill 'name' to global version X.Y.Z"

### Requirement: Backup before upgrade
The system SHALL create a backup before upgrading skills.

#### Scenario: Create backup before upgrade
- **WHEN** user runs `skill-hub upgrade skill-name`
- **THEN** system creates backup at `~/.agents/skills/backup/skill-name-backup-timestamp`

#### Scenario: Restore from backup on failure
- **WHEN** upgrade fails mid-process
- **THEN** system restores from backup
- **AND THEN** displays error message with backup location
