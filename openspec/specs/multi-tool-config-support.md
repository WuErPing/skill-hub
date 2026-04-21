# Multi-tool Config Support

## Purpose

Support multiple AI tool configurations (Claude, Opencode, Cursor) with automatic format detection and conversion.

## Requirements

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

#### Scenario: Detect private tool config
- **WHEN** system encounters a skill in `.*/skills/private` directory
- **THEN** system identifies it as project-private config

### Requirement: Tool-specific installation paths
The system SHALL install skills to the correct tool-specific directory.

#### Scenario: Install to Claude skills directory
- **WHEN** user runs install with `--tool claude`
- **THEN** system installs to `~/.claude/skills/`

#### Scenario: Install to Opencode skills directory
- **WHEN** user runs install with `--tool opencode`
- **THEN** system installs to `~/.opencode/skills/`

#### Scenario: Install to project-private directory
- **WHEN** user runs install with `--to private`
- **THEN** system installs to `.*/skills/private/`

#### Scenario: Default install path
- **WHEN** user runs install without tool flag
- **THEN** system installs to `~/.agents/skills/`

### Requirement: Tool-specific config conversion
The system SHALL convert skill configurations between supported tool formats when installing to different tool directories.

#### Scenario: Convert Claude config for Opencode
- **WHEN** user installs a Claude skill to Opencode directory
- **THEN** system converts config to Opencode format

#### Scenario: Convert Opencode config for Claude
- **WHEN** user installs an Opencode skill to Claude directory
- **THEN** system converts config to Claude format

#### Scenario: Convert for private directory
- **WHEN** user installs skill to private directory with different tool format
- **THEN** system converts config appropriately

### Requirement: Tool-specific installation feedback
The system SHALL indicate which tool directory a skill is installed to.

#### Scenario: Show install location
- **WHEN** skill is successfully installed
- **THEN** system displays: "Successfully installed skill 'name' to <directory>"

#### Scenario: Show tool name
- **WHEN** listing skills with `--verbose`
- **THEN** each skill shows its tool directory path
