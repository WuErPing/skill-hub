# Version Bump Skill

A guide for updating project version numbers and CHANGELOG.md across all relevant files.

## Overview

When releasing a new version of a Python project, you need to update version numbers in multiple locations and document the changes in CHANGELOG.md.

## Files to Update

1. **pyproject.toml** - Main project version
2. **src/<package>/__init__.py** - `__version__` variable
3. **CHANGELOG.md** - Add new version entry

## Steps

### 1. Determine New Version

Based on the staged changes, determine the appropriate version bump:
- **Patch (0.0.X)** - Bug fixes only
- **Minor (0.X.0)** - New features, backward compatible
- **Major (X.0.0)** - Breaking changes

### 2. Update pyproject.toml

```toml
[project]
version = "0.4.0"  # Update this line
```

### 3. Update Package __init__.py

```python
# src/<package>/__init__.py
__version__ = "0.4.0"  # Must match pyproject.toml
```

> ⚠️ **Critical**: The CLI typically imports `__version__` from here. If you forget this, `tool --version` will show the old version!

### 4. Update CHANGELOG.md

Add a new section at the top (after `[Unreleased]`):

```markdown
## [Unreleased]

## [0.4.0] - 2026-03-16

### Added
- New feature description
- Another feature

### Changed
- Behavior change

### Fixed
- Bug fix description

### Removed
- Deprecated feature removal
```

Also update the version comparison links at the bottom:

```markdown
[Unreleased]: https://github.com/user/repo/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/user/repo/releases/tag/v0.4.0
[0.3.0]: https://github.com/user/repo/releases/tag/v0.3.0
```

### 5. Stage All Changes

```bash
git add pyproject.toml

git add src/<package>/__init__.py

git add CHANGELOG.md
```

### 6. Verify

```bash
# Check all staged changes
git diff --staged --stat

# Verify the version file change
git diff --staged src/<package>/__init__.py
```

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `tool --version` shows old version | `__init__.py` not updated | Update `__version__` in package init |
| pip installs wrong version | pyproject.toml not updated | Update version in pyproject.toml |
| Links in CHANGELOG broken | Missing version link | Add `[X.X.X]:` link at bottom |

## Template: Version Bump Checklist

```markdown
## Bump to vX.X.X

- [ ] Update `version` in `pyproject.toml`
- [ ] Update `__version__` in `src/<package>/__init__.py`
- [ ] Add version entry in `CHANGELOG.md`
- [ ] Update version links in `CHANGELOG.md`
- [ ] Stage all changes
- [ ] Verify with `git diff --staged`
- [ ] Test install: `pip install -e . && <tool> --version`
```

## Example Commit

```
chore: bump version to 0.4.0

- Update version in pyproject.toml
- Update __version__ in package __init__.py
- Add CHANGELOG entry for v0.4.0
```
