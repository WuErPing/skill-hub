# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
make install     # pip install -e .
make test        # pytest tests/ -v --tb=short
make lint        # ruff check src/ tests/
make build       # python -m build
```

Run a single test: `pytest tests/test_web.py::test_install_skill -v`

Run the web UI locally: `skill-hub web` (http://127.0.0.1:7860)

## Architecture

**Stack**: Python 3.9+, Click CLI, Flask web UI (single-page, server-rendered), PyYAML, Rich

**Data flow**: GitHub repos/local dirs are cloned/scanned into `~/.skills_repo/repos/`, skill mappings are saved to `~/.skills_repo/mappings/`, and skills are installed (copy or symlink) to configurable target directories (default: `~/.claude/skills/` and `~/.agents/skills/`).

**Key modules** (all under `src/skill_hub/`):

- `cli.py` — Click CLI entrypoint (`web`, `version`, `self-update` commands)
- `web/app.py` — Flask app factory; starts background scheduler on boot; injects initial data into server-rendered template
- `web/api.py` — All `/api/*` REST endpoints (Blueprint with `url_prefix="/api"`)
- `web/repos.py` — Repo management: `Repo` dataclass, `repos.yaml` persistence, git clone/pull/fetch, skill discovery (`_find_skills_in_repo`), async task tracking (`RepoTask` with background threads)
- `web/state.py` — Skill install/uninstall logic, MD5-based staleness detection (with disk-persisted cache at `~/.skills_repo/md5_cache.json`), `SkillEntry` and `DirStatus` dataclasses
- `web/config.py` — Install directory configuration (`~/.skills_repo/config.json`), `InstallDir` dataclass with abbreviation generation
- `web/scheduler.py` — Singleton `RepoScheduler` that periodically checks repos for remote updates (default 30 min)
- `models.py` — `SkillMetadata` dataclass (parsed from SKILL.md YAML frontmatter)
- `utils/yaml_parser.py` — Parses `---`-delimited YAML frontmatter from SKILL.md files
- `utils/path_utils.py` — `expand_home()` for cross-platform `~` expansion

**Web UI**: Single `index.html` template. Flask renders initial data server-side; the frontend uses vanilla JS `fetch()` calls to `/api/*` endpoints for all interactions.

## Key Conventions

- **Version sync**: Two files must stay in sync on version bumps — `src/skill_hub/__init__.py` (`__version__`) and `pyproject.toml` (`project.version`). Use the `project-version-update` skill for the full release workflow.
- **Linting**: ruff only. No type checker configured.
- **Testing**: Flask test client with `temp_home` fixture that patches module-level path constants to `tmp_path`. Tests monkey-patch `skill_hub.web.repos.SKILLS_REPO_ROOT`, `REPOS_YAML`, etc.
- **SKILL.md format**: YAML frontmatter (`name`, `description` required; `license`, `compatibility`, `metadata` optional) + markdown body
- **Install methods**: Skills can be installed via `copy` (shutil.copytree) or `symlink` (os.symlink with copy fallback). The API accepts `method` parameter.
- **Multi-directory install**: Install dirs are configurable via `config.json`. The API supports per-directory install/uninstall via `/skills/<name>/install-to` and `/skills/<name>/uninstall-from`.
- **Private skills** for this repo live in `.agents/skills/` (project-level).
