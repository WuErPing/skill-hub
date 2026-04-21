"""Skills state tracking — listing, status computation, install/uninstall."""

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from skill_hub.web.repos import REPOS_DIR, load_repos_config, load_skill_mapping, repo_dir

CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
AGENTS_SKILLS = Path.home() / ".agents" / "skills"


@dataclass
class SkillEntry:
    name: str
    repo_name: str
    repo_url: str
    path: Path  # absolute path in the cloned repo
    in_claude: bool   # installed to ~/.claude/skills
    in_agents: bool   # installed to ~/.agents/skills
    md5_source: str   # MD5 of source skill in repo
    md5_claude: str   # MD5 of installed version in ~/.claude/skills (empty if not installed)
    md5_agents: str   # MD5 of installed version in ~/.agents/skills (empty if not installed)

    @property
    def claude_matches_source(self) -> bool:
        return self.in_claude and self.md5_claude == self.md5_source

    @property
    def agents_matches_source(self) -> bool:
        return self.in_agents and self.md5_agents == self.md5_source

    @property
    def status(self) -> str:
        c_ok = self.claude_matches_source
        a_ok = self.agents_matches_source
        if c_ok and a_ok:
            return "已安装"
        elif self.in_claude or self.in_agents:
            return "不一致"
        return "未安装"


def _md5_of_dir(path: Path) -> str:
    """Return a combined MD5 of all files in a directory (sorted by path)."""
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.name.encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _is_skill_dir(path: Path) -> bool:
    """A skill directory is any subdirectory that is not hidden."""
    return path.is_dir() and not path.name.startswith(".")


def list_skills() -> list[SkillEntry]:
    """Scan repos via skill mappings and both install directories, return all skills with status."""
    repos = load_repos_config()
    repo_url_map = {r.name: r.url for r in repos}

    claude_skills: dict[str, str] = {}
    agents_skills: dict[str, str] = {}

    if CLAUDE_SKILLS.exists():
        for d in CLAUDE_SKILLS.iterdir():
            if _is_skill_dir(d):
                claude_skills[d.name] = _md5_of_dir(d)
    if AGENTS_SKILLS.exists():
        for d in AGENTS_SKILLS.iterdir():
            if _is_skill_dir(d):
                agents_skills[d.name] = _md5_of_dir(d)

    skills: list[SkillEntry] = []

    for repo in repos:
        mapping = load_skill_mapping(repo)
        if not mapping:
            continue
        repo_root = repo_dir(repo)
        for skill_name, rel_path in mapping.items():
            skill_path = repo_root / rel_path
            if not skill_path.exists():
                continue

            in_c = skill_name in claude_skills
            in_a = skill_name in agents_skills
            source_md5 = _md5_of_dir(skill_path)

            skills.append(SkillEntry(
                name=skill_name,
                repo_name=repo.name,
                repo_url=repo.url,
                path=skill_path,
                in_claude=in_c,
                in_agents=in_a,
                md5_source=source_md5,
                md5_claude=claude_skills.get(skill_name, ""),
                md5_agents=agents_skills.get(skill_name, ""),
            ))

    return sorted(skills, key=lambda s: (s.repo_name, s.name))


def install_skill(name: str, source_path: Path) -> tuple[bool, str]:
    """Copy skill from source_path to both ~/.claude/skills/ and ~/.agents/skills/."""
    try:
        CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
        AGENTS_SKILLS.mkdir(parents=True, exist_ok=True)

        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        if dest_a.exists():
            shutil.rmtree(dest_a)
        if dest_b.exists():
            shutil.rmtree(dest_b)

        shutil.copytree(source_path, dest_a)
        shutil.copytree(source_path, dest_b)
        return True, f"Installed {name} to both directories"
    except Exception as e:
        return False, str(e)


def install_to_one(name: str, source_path: Path, target: str) -> tuple[bool, str]:
    """Copy skill from source_path to a single directory ('claude' or 'agents')."""
    try:
        if target == "claude":
            dest_dir = CLAUDE_SKILLS
        elif target == "agents":
            dest_dir = AGENTS_SKILLS
        else:
            return False, f"Unknown target: {target}"

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source_path, dest)
        return True, f"Installed {name} to {target}"
    except Exception as e:
        return False, str(e)


def uninstall_skill(name: str) -> tuple[bool, str]:
    """Remove skill from both ~/.claude/skills/ and ~/.agents/skills/."""
    try:
        dest_a = CLAUDE_SKILLS / name
        dest_b = AGENTS_SKILLS / name

        if dest_a.exists():
            shutil.rmtree(dest_a)
        if dest_b.exists():
            shutil.rmtree(dest_b)

        return True, f"Uninstalled {name} from both directories"
    except Exception as e:
        return False, str(e)
