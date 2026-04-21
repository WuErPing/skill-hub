# Priority-based Skill Resolution

## Purpose

Define priority rules for resolving which skill to use when the same skill exists in multiple directories.

## Requirements

### Requirement: Priority-based skill resolution
When the same skill exists in multiple directories, the system SHALL use priority ordering to determine which skill to use.

#### Scenario: Private takes precedence
- **WHEN** same skill exists in both public and private directories
- **THEN** private directory skill is used

#### Scenario: Multiple private locations
- **WHEN** same skill exists in multiple private directories
- **THEN** first discovered directory takes precedence

#### Scenario: Priority order
- **WHEN** resolving skill priority
- **THEN** order is: private > public

### Requirement: Priority indication in list
The system SHALL indicate which skill will be used when multiple copies exist.

#### Scenario: List shows priority
- **WHEN** user runs `skill-hub list`
- **THEN** skills show which directory they come from

#### Scenario: Duplicate warning
- **WHEN** same skill exists in multiple directories
- **THEN** system warns user about duplicates

### Requirement: Priority in compare
The comparison system SHALL respect priority when comparing skills.

#### Scenario: Compare shows winning skill
- **WHEN** user runs `skill-hub compare`
- **THEN** comparison shows which skill would be used based on priority

#### Scenario: Priority status
- **WHEN** comparing skills with same name in different directories
- **THEN** status indicates which would take precedence
