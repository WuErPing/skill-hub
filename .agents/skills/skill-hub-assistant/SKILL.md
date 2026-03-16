---
name: skill-hub-assistant
description: Manage agent skills using skill-hub CLI. Use this skill when the user asks to list, view, install, sync, update, or search skills in natural language — for example "show me all my skills", "install this skill to public", "what does the git-commit-helper skill do?", "sync my local skill to global", "check for skill updates", or any task involving ~/.agents/skills or .agents/skills directories.
metadata:
  author: erpingwu@gmail.com
  created: '2026-03-16'
  version: 1.0.0
---

# skill-hub Assistant

Translate natural language requests into `skill-hub` CLI commands and execute them.

## Intent → Command Mapping

| User intent | Command |
|-------------|---------|
| List / show all skills | `skill-hub list` |
| List with details | `skill-hub list --verbose` |
| List only public / global | `skill-hub list --public` |
| List only private / project | `skill-hub list --private` |
| Compare private vs public | `skill-hub list --diff` |
| Read / show a skill | `skill-hub view <name>` |
| Where are skills stored | `skill-hub path` |
| Install a skill (local / GitHub / URL) | `skill-hub install <source>` |
| Install to global / public | `skill-hub install <source> --to public` |
| Install with a different name | `skill-hub install <source> --as <name>` |
| Promote private → public | `skill-hub sync <name> private public` |
| Pull public → private | `skill-hub sync <name> public private` |
| Preview sync without changes | `skill-hub sync <name> <from> <to> --dry-run` |
| Check for skill updates | `skill-hub update` or `skill-hub update <name>` |
| Check skill-hub version | `skill-hub version` |
| Upgrade skill-hub itself | `skill-hub self-update` |

## Workflow

1. **Understand intent** — identify the operation (list / view / install / sync / update) and any arguments (skill name, source, target scope).
2. **Clarify if ambiguous** — ask for the skill name or source if the user didn't provide it.
3. **Run the command** — execute via shell. Always show the output to the user.
4. **Explain the result** — briefly summarize what happened or what the output means.

## Scope Resolution

- "global" / "public" / "shared" → `--to public` / `public` scope → `~/.agents/skills/`
- "local" / "private" / "project" → `--to private` / `private` scope → `.agents/skills/`
- Default (no scope mentioned) → private

## Install Source Resolution

- Path starting with `/`, `./`, or `~/` → local path install
- Pattern `user/repo/skill-name` → GitHub install
- URL starting with `http` → URL install
- Bare skill name → search discovered skills, then install from found path

## Notes

- Always run `skill-hub list` first when the user isn't sure what skills exist.
- Use `--dry-run` before destructive sync operations when the user seems unsure.
- Use `--force` only when the user explicitly wants to overwrite.
