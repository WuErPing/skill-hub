# Multi-layer Skill Directories

## Purpose

Support hierarchical directory structure for skills with public and private directories, allowing both global (public) and project-specific (private) skill installations.

## Requirements

### Requirement: Multi-layer skill directory structure
The system SHALL support a hierarchical directory structure for skills with public and private directories.

#### Scenario: Public skill directories
- **WHEN** system looks for skills
- **THEN** it discovers skills in `~/.agents/skills` and `~/.claude/skills`

#### Scenario: Private skill directories
- **WHEN** system looks for project-specific skills
- **THEN** it discovers skills in `.agents/skills/private`, `.claude/skills/private`, and other `.*/skills/private` directories

#### Scenario: Directory discovery
- **WHEN** system scans for skill directories
- **THEN** it finds all hidden directories matching `.*/skills` pattern

### Requirement: Directory priority
The system SHALL assign priority to skill directories when the same skill exists in multiple locations.

#### Scenario: Priority ordering
- **WHEN** same skill exists in both public and private directories
- **THEN** private directory takes precedence over public

#### Scenario: Multiple private locations
- **WHEN** same skill exists in multiple private directories
- **THEN** the first discovered (based on directory scan order) takes precedence

### Requirement: Skill source tracking
The system SHALL track which directory each skill comes from.

#### Scenario: List skills with source
- **WHEN** user runs `skill-hub list --all`
- **THEN** each skill shows its source directory path

#### Scenario: Compare skills with source
- **WHEN** user runs `skill-hub compare`
- **THEN** comparison results show which directory each skill comes from
