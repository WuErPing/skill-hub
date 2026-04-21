---
name: project-version-update
description: Update project version number, CHANGELOG, README.md, and README.zh-CN.md for a new release, then capture the workflow as a project skill.
license: MIT
compatibility: cursor, claude, opencode
metadata:
  version: 1.0.0
  author: you@example.com
  updateUrl: https://github.com/wuerping/skill-hub
---

## When to Use

Use this skill when you need to bump the project version (e.g., from 0.6.0 to 0.7.0), update release notes, synchronize documentation, and persist the workflow as a reusable project skill.

## Workflow

### 1. Identify the New Version

Determine the next version number following [Semantic Versioning](https://semver.org/):

- **MAJOR** bump for breaking changes
- **MINOR** bump for new features (backward compatible)
- **PATCH** bump for bug fixes

### 2. Update Version in Source Files

Update all files that hardcode the version number:

```python
# src/skill_hub/__init__.py
__version__ = "0.7.0"
```

```toml
# pyproject.toml
[project]
version = "0.7.0"
```

> Search for the old version string across the codebase to catch any missed locations.

### 3. Update CHANGELOG.md

Add a new section under `## [Unreleased]` following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [0.7.0] - YYYY-MM-DD

### Added
- New features

### Changed
- Behavioral changes

### Fixed
- Bug fixes

### Removed
- Deprecated features
```

Rules:
- Group changes under `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
- Use present tense ("Add", "Fix", "Change")
- Link to the comparison URL at the bottom of the file

### 4. Update README.md

Ensure `README.md` accurately reflects the current feature set:

- Update installation instructions if changed
- Add/remove CLI commands in the command table
- Update architecture diagrams if module structure changed
- Update feature lists

### 5. Sync README.zh-CN.md

Translate the updated `README.md` content into Chinese:

- Keep the same section structure and code blocks
- Translate prose; leave code, URLs, and file paths unchanged
- Maintain the ASCII diagrams (translate labels only if they are inline comments)

### 6. Verify Changes

Run tests and linting to ensure nothing is broken:

```bash
python -m pytest tests/ -v
python -c "from skill_hub import __version__; print(__version__)"
```

### 7. Capture the Workflow as a Skill

After completing the version bump, persist the workflow in `.agents/skills/project-version-update/SKILL.md` so future agents can reuse it.

Create the skill directory and `SKILL.md` with:
- YAML frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`)
- Step-by-step instructions
- Code examples
- Verification commands

## Example

Bumping from `0.6.0` to `0.7.0`:

1. Edit `src/skill_hub/__init__.py` → `__version__ = "0.7.0"`
2. Edit `pyproject.toml` → `version = "0.7.0"`
3. Prepend to `CHANGELOG.md`:
   ```markdown
   ## [0.7.0] - 2026-04-21

   ### Added
   - `version` CLI command
   - `self-update` CLI command
   ```
4. Update `README.md` command table and feature list
5. Translate changes to `README.zh-CN.md`
6. Run tests
7. Update `.agents/skills/project-version-update/SKILL.md` if the workflow evolved
