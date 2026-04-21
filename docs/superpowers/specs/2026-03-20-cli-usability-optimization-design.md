# skill-hub CLI Usability Optimization — Design Spec

**Date**: 2026-03-20
**Status**: Draft
**Author**: Sisyphus

## Problem Statement

The current CLI has two core usability issues:

1. **Abstract terminology** — `public` / `private` are not intuitive. New users don't understand that `public = ~/.agents/skills` (global) and `private = .agents/skills` (project-level).

2. **Hard-to-remember sync command** — `skill-hub sync <name> <from> <to>` uses 3 positional arguments with no clear direction. Users frequently get the order wrong.

Additionally, output is cluttered with parse warnings and a Version column showing "-" for most skills.

## Design Decisions

### Decision 1: Terminology Change

**Change**: `public` → `global`, `private` → `local`

**Rationale**: Aligns with established conventions (e.g., `git config --global` vs `git config --local`). Self-explanatory.

**Scope of change**:
- CLI flags: `--to global`, `--to local`, `--global`, `--local`
- Output text: "Source: global", "Source: local"
- Error messages and help text
- Documentation (README.md, README.zh-CN.md)
- Internal code: `PUBLIC_PATH` → `GLOBAL_PATH`, `source_directory` values

**Backward compatibility**: `--to public` / `--to private` still accepted with a deprecation warning:
```
Warning: --to public is deprecated, use --to global instead
```

### Decision 2: Sync Command Redesign

**Current**: `skill-hub sync <name> <FROM> <TO>` (3 positional args)
**New**: `skill-hub sync <name> --to <target>` (1 positional + 1 named)

| Command | Meaning |
|---------|---------|
| `skill-hub sync my-skill --to global` | Copy from local → global |
| `skill-hub sync my-skill --to local` | Copy from global → local |

- Source is automatically inferred from the `--to` target
- `--dry-run` and `--force` flags preserved
- **No backward compatibility** for old 3-arg syntax (breaking change)

### Decision 3: Output Optimization

#### 3a. Default `list` — Simplified

Current output uses a wide table with Source/Version/Status columns. Default output should be compact:

```
$ skill-hub list
Skills (87):

playwright-skill     Playwright browser automation for end-to-end testing...
linear-claude-skill  Use MCP tools to manage Linear issues and projects...
git-commit-helper    Analyze staged changes and generate conventional...
```

- Name + truncated description (70 chars)
- No table borders, no Source/Version/Status columns
- Filtered views (`--global`, `--local`) still work

#### 3b. `--verbose` Output — Enhanced

Verbose mode shows all details in a readable multi-line format:

```
$ skill-hub list --verbose
playwright-skill
  Description: Playwright browser automation for end-to-end testing and web application interaction
  Path: ~/.agents/skills/playwright-skill/SKILL.md
  Source: global
  Version: 1.0.0
  Compatibility: cursor, claude, opencode

git-commit-helper
  Description: Analyze staged changes and generate conventional commit messages, then execute the commit
  Path: .agents/skills/git-commit-helper/SKILL.md
  Source: local
  Version: 1.0.1
  Status: ★ Overrides global version
```

#### 3c. `--diff` Output — Simplified

Remove the Version column (mostly "-"). Keep only:

| Skill Name | Source | Status |
|------------|--------|--------|

#### 3d. Parse Warning Handling

**Current**: `Failed to parse skill file: ...` printed to stderr for every invalid SKILL.md.
**New**: Suppress by default. Only show in `--verbose` mode. Never block normal output.

Implementation: Catch parse exceptions in `DiscoveryEngine`, log to a buffer, only print if verbose flag is set.

#### 3e. Error Messages — Add Guidance

Current error messages are terse. Add actionable next steps:

```
$ skill-hub view foo
✗ Skill not found: foo

Available skills:
  • playwright-skill
  • linear-claude-skill
  ... (showing first 10)

Tip: Use 'skill-hub list' to see all skills, or 'skill-hub list --verbose' for details.
```

```
$ skill-hub install nonexistent-skill
✗ Skill 'nonexistent-skill' not found locally.

Use 'skill-hub list' to see available skills, or install from a path/GitHub/URL:
  skill-hub install /path/to/skill
  skill-hub install user/repo/skill-name
```

## Affected Files

| File | Changes |
|------|---------|
| `src/skill_hub/cli.py` | All CLI commands — terminology, sync syntax, list output, error messages |
| `src/skill_hub/installer.py` | Terminology in sync/install functions |
| `src/skill_hub/comparison.py` | Output labels (Local Only → "local-only" etc.) |
| `src/skill_hub/models.py` | `source_directory` field description |
| `src/skill_hub/discovery/engine.py` | Parse warning handling |
| `README.md` | All examples and terminology |
| `README.zh-CN.md` | Chinese translation |
| `tests/` | Update test expectations for new output format |

## Version Bump

This is a **breaking change** (sync syntax). Bump to **0.7.0**.

## Out of Scope

- Shell completion (tab-completion for commands and skill names)
- Search/filter by keyword in `list`
- Skill categories/grouping
- Command aliases (`ls`, `get`, `promote`)

These can be addressed in a follow-up if needed.
