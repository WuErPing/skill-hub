## ADDED Requirements

### Requirement: Remote Repository Configuration

The system SHALL allow users to configure remote skill repositories in the central configuration file.

#### Scenario: Add repository via configuration

- **WHEN** a user adds a repository entry to `~/.skills/.skill-hub/config.json`
- **THEN** the configuration SHALL include:
  - `url`: Repository URL (required)
  - `enabled`: Boolean flag (default: true)
  - `branch`: Git branch name (default: "main")
  - `path`: Subdirectory path within repo (default: "")
  - `sync_schedule`: Cron expression for auto-sync (optional)

#### Scenario: Add repository via CLI

- **WHEN** the user runs `skill-hub repo add https://github.com/anthropics/skills`
- **THEN** the system SHALL add the repository to config with default settings
- **AND** it SHALL validate the URL format
- **AND** it SHALL test repository accessibility

#### Scenario: List configured repositories

- **WHEN** the user runs `skill-hub repo list`
- **THEN** the system SHALL display all configured repositories with:
  - Repository URL
  - Enabled status
  - Last sync timestamp
  - Number of skills from this repository

#### Scenario: Disable repository

- **WHEN** the user runs `skill-hub repo disable <url>`
- **THEN** the system SHALL set `enabled: false` for that repository
- **AND** it SHALL not sync from this repository until re-enabled

### Requirement: Git Repository Cloning

The system SHALL clone or update remote repositories to a local cache directory.

#### Scenario: Initial repository clone

- **WHEN** a repository is synced for the first time
- **THEN** the system SHALL clone it to `~/.skills/.skill-hub/repos/<repo-hash>/`
- **AND** it SHALL use shallow clone (depth=1) for efficiency
- **AND** it SHALL check out the specified branch

#### Scenario: Update existing repository

- **WHEN** a repository is synced subsequently
- **THEN** the system SHALL perform `git pull` to update
- **AND** it SHALL detect merge conflicts and report them
- **AND** it SHALL fall back to re-cloning if pull fails

#### Scenario: Handle private repositories

- **WHEN** a repository requires authentication
- **THEN** the system SHALL support GitHub personal access tokens
- **AND** it SHALL read token from environment variable `SKILL_HUB_GITHUB_TOKEN`
- **AND** it SHALL report authentication failures clearly

### Requirement: Skill Extraction from Repositories

The system SHALL extract skills from repository directory structure and import them to the hub.

#### Scenario: Extract skills from repository root

- **WHEN** repository path is empty or "/"
- **THEN** the system SHALL scan for `skills/*/SKILL.md` pattern
- **AND** it SHALL parse and validate each SKILL.md file
- **AND** it SHALL import valid skills to hub

#### Scenario: Extract skills from subdirectory

- **WHEN** repository has path configured (e.g., "/examples/skills")
- **THEN** the system SHALL scan only that subdirectory
- **AND** it SHALL look for `<path>/*/SKILL.md` pattern

#### Scenario: Handle invalid skills in repository

- **WHEN** a SKILL.md file fails validation
- **THEN** the system SHALL skip that skill
- **AND** it SHALL log a warning with file path and error details
- **AND** it SHALL continue processing other skills

#### Scenario: Track skill source repository

- **WHEN** a skill is imported from a remote repository
- **THEN** the metadata SHALL include:
  - Source type: "remote"
  - Repository URL
  - Commit hash
  - Imported timestamp

### Requirement: Repository Metadata Management

The system SHALL track repository state and sync history.

#### Scenario: Store repository metadata

- **WHEN** a repository is synced
- **THEN** the system SHALL create `~/.skills/.skill-hub/repos/<repo-hash>/meta.json` with:
  - Repository URL
  - Current commit hash
  - Last sync timestamp
  - Skills imported count
  - Sync errors (if any)

#### Scenario: Detect repository changes

- **WHEN** syncing a repository
- **THEN** the system SHALL compare current commit hash with stored hash
- **AND** if unchanged, it SHALL skip skill extraction (incremental sync)
- **AND** if changed, it SHALL re-extract all skills

### Requirement: Repository URL Validation

The system SHALL validate repository URLs before adding them to configuration.

#### Scenario: Validate GitHub URL format

- **WHEN** a user adds a GitHub repository URL
- **THEN** the system SHALL accept formats:
  - `https://github.com/owner/repo`
  - `https://github.com/owner/repo.git`
  - `git@github.com:owner/repo.git`

#### Scenario: Test repository accessibility

- **WHEN** adding a repository
- **THEN** the system SHALL attempt a shallow clone
- **AND** if successful, it SHALL confirm repository is accessible
- **AND** if failed, it SHALL report the error and not add the repository

#### Scenario: Reject invalid URLs

- **WHEN** a user provides an invalid URL
- **THEN** the system SHALL reject URLs that are:
  - Not valid git repository URLs
  - Malformed (missing protocol, invalid domain)
  - Point to non-existent repositories
