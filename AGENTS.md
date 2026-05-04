# skill-hub — Agent Guide

skill-hub is a Python CLI + Flask web UI for managing agent skills from GitHub repos and local directories. Skills are installed to `~/.claude/skills/` and `~/.agents/skills/`.

## Development Commands

```bash
make install     # pip install -e .
make test        # pytest tests/ -v --tb=short
make lint        # ruff check src/ tests/
make build       # python -m build
```

Run the web UI locally: `skill-hub web` (opens on http://127.0.0.1:7860).

## Project Structure

- `src/skill_hub/cli.py` — Click CLI entrypoint (`web`, `version`, `self-update`)
- `src/skill_hub/web/` — Flask app (`app.py` factory, `api.py` routes, `repos.py` git ops, `state.py` skill tracking)
- `src/skill_hub/models.py` — `SkillMetadata` dataclass (YAML frontmatter from `SKILL.md`)
- `tests/` — pytest suite; `conftest.py` is minimal

## Version Bumping

Two files must stay in sync:
1. `src/skill_hub/__init__.py` — `__version__`
2. `pyproject.toml` — `project.version`

Use the `.agents/skills/project-version-update/` skill for the full release workflow (update CHANGELOG.md, README.md, README.zh-CN.md, tag, push).

## Key Conventions

- **SKILL.md** format: YAML frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`) + markdown body
- **Install directories** are configured in `~/.skills_repo/config.json` (managed via web UI). Defaults: `~/.claude/skills/` and `~/.agents/skills/`.
- **Repo config** lives in `~/.skills_repo/repos.yaml` (managed via web UI). Remote repos clone into `~/.skills_repo/repos/`.
- **Private skills** for this repo live in `.agents/skills/` (project-level). Only `project-version-update` is currently persisted.
- **Linting**: ruff only. No type checker (mypy/pytype) is configured.
- **Testing**: pytest with short traceback. No CI workflows exist in `.github/workflows/`.
