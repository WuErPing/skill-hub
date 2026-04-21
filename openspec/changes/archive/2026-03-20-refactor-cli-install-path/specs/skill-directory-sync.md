## ADDED Requirements

### Requirement: Explicit sync command
The system SHALL provide an explicit `skill-hub sync` command for moving skills between directories.

#### Scenario: Sync from public to private
- **WHEN** user runs `skill-hub sync <skill-name> --from public --to private`
- **THEN** skill is copied from global directory to project-private directory

#### Scenario: Sync from private to public
- **WHEN** user runs `skill-hub sync <skill-name> --from private --to public`
- **THEN** skill is copied from project-private directory to global directory

#### Scenario: Sync with version update
- **WHEN** user syncs a skill that has newer version in source
- **THEN** destination gets the newer version

### Requirement: One-way sync only
The system SHALL NOT perform automatic bidirectional synchronization.

#### Scenario: No auto-bi-sync
- **WHEN** user does not run sync command
- **THEN** skills in public and private directories remain independent

#### Scenario: Explicit sync required
- **WHEN** user wants to update private skill from public
- **THEN** user must explicitly run sync command

### Requirement: Sync confirmation
The system SHALL require explicit confirmation before overwriting existing skills.

#### Scenario: Overwrite protection
- **WHEN** sync would overwrite an existing skill in destination
- **THEN** system asks for confirmation (or use `--force` flag to skip)

#### Scenario: Dry run option
- **WHEN** user runs `skill-hub sync --dry-run`
- **THEN** system shows what would be synced without making changes

### Requirement: Sync status reporting
The system SHALL provide clear feedback about sync operations.

#### Scenario: Successful sync
- **WHEN** skill is synced successfully
- **THEN** system displays: "Successfully synced <skill-name> from <source> to <destination>"

#### Scenario: Sync failure
- **WHEN** sync fails (e.g., skill not found in source)
- **THEN** system displays clear error message
