# Skill Installation

## Purpose

Enable installation of skills from various sources (GitHub, local path, URL) with support for different target directories.

## Requirements

### Requirement: Skill installation from GitHub repository
The system SHALL allow users to install a skill from a GitHub repository by specifying the repository path (e.g., `user/repo/skill-name`).

#### Scenario: Install skill from GitHub to public directory
- **WHEN** user runs `skill-hub install user/repo/skill-name`
- **THEN** system clones or downloads the skill from GitHub
- **AND THEN** skill is installed to `~/.agents/skills/skill-name`

#### Scenario: Install skill from GitHub with custom directory name
- **WHEN** user runs `skill-hub install user/repo/skill-name --as custom-name`
- **THEN** system installs skill to `~/.agents/skills/custom-name`

#### Scenario: Install skill from GitHub to private directory
- **WHEN** user runs `skill-hub install user/repo/skill-name --to private`
- **THEN** system installs skill to `.agents/skills/private/custom-name`

#### Scenario: Handle GitHub repository not found
- **WHEN** user runs `skill-hub install nonexistent/repo/skill-name`
- **THEN** system displays clear error message: "Skill not found on GitHub"

#### Scenario: Handle invalid GitHub URL
- **WHEN** user runs `skill-hub install not-a-valid-url`
- **THEN** system displays clear error message: "Invalid GitHub repository format"

### Requirement: Skill installation from local path
The system SHALL allow users to install a skill from a local directory path.

#### Scenario: Install skill from absolute local path
- **WHEN** user runs `skill-hub install /absolute/path/to/skill`
- **THEN** system copies skill directory to `~/.agents/skills/`

#### Scenario: Install skill from relative local path
- **WHEN** user runs `skill-hub install ./relative/path/to/skill`
- **THEN** system resolves relative path and copies skill to `~/.agents/skills/`

#### Scenario: Install skill from local path to private directory
- **WHEN** user runs `skill-hub install /path/to/skill --to private`
- **THEN** system copies skill to `.agents/skills/private/`

#### Scenario: Handle non-existent local path
- **WHEN** user runs `skill-hub install /nonexistent/path`
- **THEN** system displays clear error message: "Skill directory not found"

### Requirement: Skill installation from URL
The system SHALL allow users to install a skill by specifying a direct URL to a SKILL.md file.

#### Scenario: Install skill from direct URL
- **WHEN** user runs `skill-hub install https://example.com/path/to/SKILL.md`
- **THEN** system downloads the file and installs it as a skill

#### Scenario: Install skill from URL to private directory
- **WHEN** user runs `skill-hub install https://example.com/path/to/SKILL.md --to private`
- **THEN** system installs skill to `.agents/skills/private/`

#### Scenario: Handle invalid URL
- **WHEN** user runs `skill-hub install https://invalid-url`
- **THEN** system displays clear error message: "Failed to download skill from URL"

### Requirement: Install validation
The system SHALL validate the installed skill before completing installation.

#### Scenario: Validate SKILL.md format
- **WHEN** user installs a skill with invalid YAML frontmatter
- **THEN** system displays error and aborts installation

#### Scenario: Validate required fields
- **WHEN** user installs a skill missing required `name` or `description`
- **THEN** system displays error and aborts installation

### Requirement: Install feedback
The system SHALL provide clear feedback during installation.

#### Scenario: Show installation progress
- **WHEN** user runs install command
- **THEN** system displays: "Installing skill 'name'..."

#### Scenario: Show successful installation
- **WHEN** skill is successfully installed
- **THEN** system displays: "Successfully installed skill 'name' to <directory>"

### Requirement: Install target selection
The system SHALL allow users to specify where skills are installed.

#### Scenario: Default install to public
- **WHEN** user runs `skill-hub install <source>` without target flag
- **THEN** skill is installed to public directory (`~/.agents/skills`)

#### Scenario: Install to private
- **WHEN** user runs `skill-hub install <source> --to private`
- **THEN** skill is installed to project-private directory

#### Scenario: Install to specific tool
- **WHEN** user runs `skill-hub install <source> --tool claude`
- **THEN** skill is installed to `~/.claude/skills/`

### Requirement: Install with custom name
The system SHALL allow users to specify a custom name for installed skills.

#### Scenario: Custom name with default target
- **WHEN** user runs `skill-hub install <source> --as custom-name`
- **THEN** skill is installed with name `custom-name` to default directory

#### Scenario: Custom name with private target
- **WHEN** user runs `skill-hub install <source> --as custom-name --to private`
- **THEN** skill is installed with name `custom-name` to private directory
