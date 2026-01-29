## ADDED Requirements

### Requirement: Multi-Agent Skill Discovery

The system SHALL discover skill definitions from multiple AI coding agent configuration directories (Cursor, Claude, Qoder, OpenCode) in both project-local and global locations.

#### Scenario: Discover Cursor skills globally

- **WHEN** the discovery engine scans the file system
- **THEN** it SHALL find all SKILL.md files in `~/.cursor/skills/*/SKILL.md`
- **AND** it SHALL parse the YAML frontmatter from each file
- **AND** it SHALL validate that `name` and `description` fields are present

#### Scenario: Discover Claude skills in project

- **WHEN** the discovery engine scans a project directory
- **THEN** it SHALL find all SKILL.md files in `.claude/skills/*/SKILL.md`
- **AND** it SHALL record the project path as the skill source location

#### Scenario: Discover Qoder skills

- **WHEN** the discovery engine scans configured locations
- **THEN** it SHALL find skills in `.qoder/skills/*/SKILL.md` (project-local)
- **AND** it SHALL find skills in `~/.qoder/skills/*/SKILL.md` (global)

#### Scenario: Discover OpenCode skills

- **WHEN** the discovery engine scans configured locations
- **THEN** it SHALL find skills in `.opencode/skills/*/SKILL.md` (project-local)
- **AND** it SHALL find skills in `~/.config/opencode/skills/*/SKILL.md` (global)

### Requirement: Skill Metadata Extraction

The system SHALL extract and validate skill metadata from SKILL.md frontmatter according to the skill specification format.

#### Scenario: Parse valid frontmatter

- **WHEN** a SKILL.md file contains valid YAML frontmatter
- **THEN** the system SHALL extract the `name` field (required)
- **AND** it SHALL extract the `description` field (required)
- **AND** it SHALL extract optional fields: `license`, `compatibility`, `metadata`

#### Scenario: Validate skill name format

- **WHEN** parsing a skill name
- **THEN** it SHALL accept names matching `^[a-z0-9]+(-[a-z0-9]+)*$`
- **AND** it SHALL reject names with uppercase letters
- **AND** it SHALL reject names starting or ending with hyphens
- **AND** it SHALL reject names with consecutive hyphens

#### Scenario: Validate description length

- **WHEN** parsing a skill description
- **THEN** it SHALL accept descriptions between 1-1024 characters
- **AND** it SHALL reject empty descriptions
- **AND** it SHALL reject descriptions exceeding 1024 characters

#### Scenario: Handle missing frontmatter

- **WHEN** a SKILL.md file lacks YAML frontmatter
- **THEN** the system SHALL skip the file
- **AND** it SHALL log a warning with the file path
- **AND** it SHALL continue processing other skills

### Requirement: Skill Registry Construction

The system SHALL build a unified skill registry containing all discovered skills with their metadata and source information.

#### Scenario: Register discovered skill

- **WHEN** a valid skill is discovered
- **THEN** it SHALL be added to the registry with:
  - Skill name (unique identifier)
  - Description
  - Source location (full file path)
  - Agent type (cursor, claude, qoder, opencode)
  - Discovery timestamp
  - Optional metadata fields

#### Scenario: Handle duplicate skill names

- **WHEN** multiple skills with the same name are discovered
- **THEN** the system SHALL keep all instances in the registry
- **AND** it SHALL mark them as duplicates with source information
- **AND** it SHALL report the conflict to the user

#### Scenario: Export registry as JSON

- **WHEN** the user requests registry export
- **THEN** the system SHALL serialize the registry to JSON format
- **AND** it SHALL include all skill metadata and source information
- **AND** it SHALL be readable by external tools

### Requirement: Cross-Platform Path Resolution

The system SHALL resolve agent configuration paths correctly on macOS, Linux, and Windows.

#### Scenario: Resolve home directory on Unix

- **WHEN** running on macOS or Linux
- **THEN** it SHALL expand `~` to the user's home directory from $HOME
- **AND** it SHALL use forward slashes for path separators

#### Scenario: Resolve home directory on Windows

- **WHEN** running on Windows
- **THEN** it SHALL expand `~` to %USERPROFILE%
- **AND** it SHALL use backslashes for path separators
- **AND** it SHALL handle Windows drive letters correctly

#### Scenario: Resolve relative project paths

- **WHEN** scanning for project-local skills
- **THEN** it SHALL start from the current working directory
- **AND** it SHALL walk up the directory tree to find git root (if applicable)
- **AND** it SHALL search for `.cursor/`, `.claude/`, `.qoder/`, `.opencode/` directories
