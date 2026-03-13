## ADDED Requirements

### Requirement: Multi-tool config detection
The system SHALL auto-detect the tool configuration format when installing or upgrading skills.

#### Scenario: Detect Claude config format
- **WHEN** system encounters a skill with `.claude` config
- **THEN** system identifies format as "claude"

#### Scenario: Detect Opencode config format
- **WHEN** system encounters a skill with `.opencode` config
- **THEN** system identifies format as "opencode"

#### Scenario: Detect Cursor config format
- **WHEN** system encounters a skill with `.cursor` config
- **THEN** system identifies format as "cursor"

### Requirement: Config format conversion between tools
The system SHALL convert skill configurations between supported tool formats.

#### Scenario: Convert Claude to Opencode
- **WHEN** user installs a Claude skill in Opencode environment
- **THEN** system converts config to Opencode format

#### Scenario: Convert Opencode to Claude
- **WHEN** user installs an Opencode skill in Claude environment
- **THEN** system converts config to Claude format

#### Scenario: Convert Cursor to Opencode
- **WHEN** user installs a Cursor skill in Opencode environment
- **THEN** system converts config to Opencode format

### Requirement: Tool-specific installation paths
The system SHALL install skills to the correct tool-specific directory.

#### Scenario: Install to Claude skills directory
- **WHEN** user runs install in Claude environment
- **THEN** system installs to `~/.claude/skills/`

#### Scenario: Install to Opencode skills directory
- **WHEN** user runs install in Opencode environment
- **THEN** system installs to `~/.opencode/skills/`

#### Scenario: Install to Cursor skills directory
- **WHEN** user runs install in Cursor environment
- **THEN** system installs to `~/.cursor/skills/`

### Requirement: Multi-tool compatibility metadata
The system SHALL preserve and update compatibility metadata during conversion.

#### Scenario: Update compatibility field
- **WHEN** system converts config format
- **THEN** system updates `compatibility` field to reflect current tool

#### Scenario: Preserve compatibility list
- **WHEN** skill has multiple compatible tools listed
- **THEN** system preserves all compatible tools in converted config

### Requirement: Config validation
The system SHALL validate tool configurations after conversion.

#### Scenario: Validate converted config
- **WHEN** config conversion completes
- **THEN** system validates converted config format

#### Scenario: Report conversion errors
- **WHEN** config conversion fails validation
- **THEN** system displays error and aborts installation
