## 1. Core Model Updates

- [x] 1.1 Add `version` field to SkillMetadata model in models.py
- [x] 1.2 Update Skill class to include version property
- [x] 1.3 Add `updateUrl` field to SkillMetadata for update detection

## 2. Installer Module (`skill_hub/installer.py`)

- [x] 2.1 Create installer module structure with CLI command
- [x] 2.2 Implement GitHub installation handler (download from repo)
- [x] 2.3 Implement local path installation handler
- [x] 2.4 Implement URL installation handler (download SKILL.md)
- [x] 2.5 Add validation for installed skills
- [x] 2.6 Implement installation feedback messages

## 3. Upgrader Module (`skill_hub/upgrader.py`)

- [x] 3.1 Create upgrader module structure with CLI command
- [x] 3.2 Implement config format detection (Claude, Opencode, Cursor)
- [x] 3.3 Implement .claude → .agent config conversion
- [x] 3.4 Implement backup before upgrade
- [x] 3.5 Implement rollback on failure

## 4. Version Module (`skill_hub/version.py`)

- [x] 4.1 Create version module structure
- [x] 4.2 Implement semver parsing and comparison
- [x] 4.3 Implement update detection (check remote for newer version)
- [x] 4.4 Implement `skill-hub update` CLI command
- [x] 4.5 Implement version history tracking

## 5. Discovery Engine Updates (`skill_hub/discovery/engine.py`)

- [x] 5.1 Update discover_skills to include version info
- [x] 5.2 Add version validation during discovery

## 6. CLI Updates (`skill_hub/cli.py`)

- [x] 6.1 Add `install` command with GitHub/local/URL sources
- [x] 6.2 Add `upgrade` command for upgrading skills
- [x] 6.3 Add `update` command for checking/updating versions

## 7. Dependencies (`pyproject.toml`)

- [x] 7.1 Add `requests` dependency
- [x] 7.2 Verify subprocess-based git operations (no external dep needed)

## 8. Testing

- [x] 8.1 Write unit tests for installer module
- [x] 8.2 Write unit tests for upgrader module
- [x] 8.3 Write unit tests for version module
- [x] 8.4 Write integration tests for CLI commands

## 9. Documentation

- [x] 9.1 Update README.md with installation instructions
- [x] 9.2 Add upgrade documentation
- [x] 9.3 Add version management documentation
