## ADDED Requirements

### Requirement: Agent Adapter Architecture

The system SHALL provide a plugin-based architecture where each AI coding agent is supported through a dedicated adapter implementation.

#### Scenario: Load agent adapters dynamically

- **WHEN** the system initializes
- **THEN** it SHALL discover all available adapter plugins
- **AND** it SHALL register adapters for cursor, claude, qoder, and opencode
- **AND** it SHALL allow future agent types to be added without modifying core code

#### Scenario: Query supported agents

- **WHEN** the user runs `skill-hub agents`
- **THEN** the system SHALL list all loaded adapters with:
  - Agent name
  - Version supported
  - Configuration paths (project-local and global)
  - Status (enabled/disabled)

### Requirement: Cursor Adapter Implementation

The system SHALL provide an adapter for Cursor that handles its specific skill directory structure and conventions.

#### Scenario: Resolve Cursor project-local path

- **WHEN** the Cursor adapter resolves project paths
- **THEN** it SHALL look for `.cursor/skills/*/SKILL.md`
- **AND** it SHALL start from current directory and walk up to git root

#### Scenario: Resolve Cursor global path

- **WHEN** the Cursor adapter resolves global paths
- **THEN** it SHALL look for `~/.cursor/skills/*/SKILL.md`
- **AND** it SHALL expand home directory correctly per platform

#### Scenario: Write skill to Cursor config

- **WHEN** the adapter distributes a skill to Cursor
- **THEN** it SHALL create directory `~/.cursor/skills/<skill-name>/`
- **AND** it SHALL write SKILL.md with preserved content
- **AND** it SHALL verify the directory name matches frontmatter name

### Requirement: Claude Adapter Implementation

The system SHALL provide an adapter for Claude that handles its specific skill directory structure and conventions.

#### Scenario: Resolve Claude project-local path

- **WHEN** the Claude adapter resolves project paths
- **THEN** it SHALL look for `.claude/skills/*/SKILL.md`
- **AND** it SHALL start from current directory and walk up to git root

#### Scenario: Resolve Claude global path

- **WHEN** the Claude adapter resolves global paths
- **THEN** it SHALL look for `~/.claude/skills/*/SKILL.md`
- **AND** it SHALL expand home directory correctly per platform

#### Scenario: Write skill to Claude config

- **WHEN** the adapter distributes a skill to Claude
- **THEN** it SHALL create directory `~/.claude/skills/<skill-name>/`
- **AND** it SHALL write SKILL.md with preserved content
- **AND** it SHALL verify the directory name matches frontmatter name

### Requirement: Qoder Adapter Implementation

The system SHALL provide an adapter for Qoder that handles its specific skill directory structure and conventions.

#### Scenario: Resolve Qoder project-local path

- **WHEN** the Qoder adapter resolves project paths
- **THEN** it SHALL look for `.qoder/skills/*/SKILL.md`
- **AND** it SHALL start from current directory and walk up to git root

#### Scenario: Resolve Qoder global path

- **WHEN** the Qoder adapter resolves global paths
- **THEN** it SHALL look for `~/.qoder/skills/*/SKILL.md`
- **AND** it SHALL expand home directory correctly per platform

#### Scenario: Write skill to Qoder config

- **WHEN** the adapter distributes a skill to Qoder
- **THEN** it SHALL create directory `~/.qoder/skills/<skill-name>/`
- **AND** it SHALL write SKILL.md with preserved content
- **AND** it SHALL verify the directory name matches frontmatter name

### Requirement: OpenCode Adapter Implementation

The system SHALL provide an adapter for OpenCode that handles its specific skill directory structure and conventions.

#### Scenario: Resolve OpenCode project-local path

- **WHEN** the OpenCode adapter resolves project paths
- **THEN** it SHALL look for `.opencode/skills/*/SKILL.md`
- **AND** it SHALL start from current directory and walk up to git root

#### Scenario: Resolve OpenCode global path

- **WHEN** the OpenCode adapter resolves global paths
- **THEN** it SHALL look for `~/.config/opencode/skills/*/SKILL.md`
- **AND** it SHALL expand home directory correctly per platform

#### Scenario: Write skill to OpenCode config

- **WHEN** the adapter distributes a skill to OpenCode
- **THEN** it SHALL create directory `~/.config/opencode/skills/<skill-name>/`
- **AND** it SHALL write SKILL.md with preserved content
- **AND** it SHALL verify the directory name matches frontmatter name

### Requirement: Adapter Configuration

The system SHALL allow users to configure which agents are enabled and customize their paths.

#### Scenario: Configure enabled agents

- **WHEN** the user edits `~/.skills/.skill-hub/config.json`
- **THEN** they SHALL be able to enable/disable specific adapters:
  ```json
  {
    "agents": {
      "cursor": { "enabled": true },
      "claude": { "enabled": true },
      "qoder": { "enabled": false },
      "opencode": { "enabled": true }
    }
  }
  ```
- **AND** disabled adapters SHALL be skipped during sync

#### Scenario: Override default paths

- **WHEN** the user configures custom paths in config.json
- **THEN** the system SHALL use those paths instead of defaults:
  ```json
  {
    "agents": {
      "cursor": {
        "enabled": true,
        "globalPath": "/custom/path/cursor/skills"
      }
    }
  }
  ```
- **AND** it SHALL validate that custom paths are absolute

#### Scenario: Validate adapter configuration

- **WHEN** the system loads adapter configuration
- **THEN** it SHALL validate that all paths exist or can be created
- **AND** it SHALL warn about misconfigured adapters
- **AND** it SHALL skip adapters with invalid configuration

### Requirement: Adapter Error Handling

The system SHALL handle adapter-specific errors gracefully and continue processing other adapters.

#### Scenario: Handle missing agent directory

- **WHEN** an adapter cannot find its target directory
- **THEN** it SHALL log a warning with the expected path
- **AND** it SHALL skip that adapter for the current operation
- **AND** it SHALL continue processing other adapters

#### Scenario: Handle permission errors

- **WHEN** an adapter lacks write permissions to target directory
- **THEN** it SHALL log an error with the path and permission details
- **AND** it SHALL skip writing to that adapter
- **AND** it SHALL report the error in sync summary

#### Scenario: Handle corrupted skill files

- **WHEN** an adapter encounters a corrupted SKILL.md file
- **THEN** it SHALL log the error with file path
- **AND** it SHALL skip that specific skill
- **AND** it SHALL continue processing other skills

#### Scenario: Adapter health check

- **WHEN** the user runs `skill-hub agents --check`
- **THEN** the system SHALL test each adapter by:
  - Verifying paths exist or can be created
  - Checking read/write permissions
  - Validating configuration
- **AND** it SHALL report health status for each adapter
