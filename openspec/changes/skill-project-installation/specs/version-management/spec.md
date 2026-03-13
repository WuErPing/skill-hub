## ADDED Requirements

### Requirement: Version tracking in SKILL.md
The system SHALL store skill version information in the SKILL.md frontmatter.

#### Scenario: Store version in frontmatter
- **WHEN** skill is installed or upgraded
- **THEN** system stores version in `metadata.version` field

#### Scenario: Parse semver format
- **WHEN** system reads skill version
- **THEN** system parses semantic versioning (e.g., `1.0.0`, `2.1.3-beta`)

### Requirement: Version comparison
The system SHALL compare skill versions to detect updates.

#### Scenario: Compare two versions
- **WHEN** system compares version A and B
- **THEN** system determines if A > B, A < B, or A == B

#### Scenario: Handle prerelease versions
- **WHEN** system compares prerelease versions
- **THEN** system follows semver precedence rules

### Requirement: Update detection
The system SHALL check for skill updates.

#### Scenario: Check single skill update
- **WHEN** user runs `skill-hub update skill-name`
- **THEN** system checks remote for newer version

#### Scenario: Check all skills updates
- **WHEN** user runs `skill-hub update --all`
- **THEN** system checks all installed skills for updates

#### Scenario: Show available updates
- **WHEN** updates are found
- **THEN** system displays: "skill-name: current X.Y.Z → available A.B.C"

### Requirement: Version upgrade
The system SHALL apply version updates to skills.

#### Scenario: Upgrade skill to latest version
- **WHEN** user runs `skill-hub upgrade skill-name`
- **THEN** system downloads and installs latest version

#### Scenario: Upgrade to specific version
- **WHEN** user runs `skill-hub upgrade skill-name --version A.B.C`
- **THEN** system installs specified version

#### Scenario: Handle upgrade failure
- **WHEN** upgrade fails
- **THEN** system rolls back to previous version

### Requirement: Version metadata
The system SHALL support additional version metadata.

#### Scenario: Store update URL
- **WHEN** skill is installed
- **THEN** system stores `metadata.updateUrl` if present

#### Scenario: Use update URL for version check
- **WHEN** checking for updates
- **THEN** system queries `metadata.updateUrl` if present

### Requirement: Version history
The system SHALL maintain version history for upgrades.

#### Scenario: Track upgrade history
- **WHEN** skill is upgraded
- **THEN** system records previous version

#### Scenario: Rollback to previous version
- **WHEN** user runs `skill-hub rollback skill-name`
- **THEN** system restores previous version
