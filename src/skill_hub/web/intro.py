"""Repo introduction: README summary, caching, and prompt generation."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from skill_hub.web.github_api import Author

INTRO_CACHE_DIR = Path.home() / ".skills_repo" / "intros"


@dataclass
class RepoIntro:
    repo_name: str
    summary: dict = field(default_factory=dict)
    authors: list[Author] = field(default_factory=list)
    cached: bool = False
    generated_at: Optional[datetime] = None
    readme_md5: str = ""


def get_intro_cache_path(repo_name: str) -> Path:
    """Return the cache file path for a repo intro."""
    safe_name = repo_name.replace("/", "__")
    INTRO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return INTRO_CACHE_DIR / f"{safe_name}.json"


def _md5_of_file(path: Path) -> str:
    """Return MD5 hash of file contents."""
    if not path.is_file():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_intro(repo_name: str, readme_path: Path) -> RepoIntro:
    """Load cached intro if valid (README hasn't changed)."""
    cache_path = get_intro_cache_path(repo_name)
    current_md5 = _md5_of_file(readme_path)
    
    if cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("readme_md5") == current_md5:
                authors = [Author(**a) for a in data.get("authors", [])]
                generated = data.get("generated_at")
                return RepoIntro(
                    repo_name=repo_name,
                    summary=data.get("summary", {}),
                    authors=authors,
                    cached=True,
                    generated_at=datetime.fromisoformat(generated) if generated else None,
                    readme_md5=current_md5,
                )
        except Exception:
            pass
    
    return RepoIntro(repo_name=repo_name, readme_md5=current_md5)


def save_intro(intro: RepoIntro) -> None:
    """Save intro to cache file."""
    cache_path = get_intro_cache_path(intro.repo_name)
    data = {
        "repo_name": intro.repo_name,
        "summary": intro.summary,
        "authors": [
            {
                "username": a.username,
                "name": a.name,
                "bio": a.bio,
                "avatar_url": a.avatar_url,
                "profile_url": a.profile_url,
                "role": a.role,
                "contributions": a.contributions,
            }
            for a in intro.authors
        ],
        "cached": True,
        "generated_at": intro.generated_at.isoformat() if intro.generated_at else None,
        "readme_md5": intro.readme_md5,
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_prompt(repo_name: str, readme_content: str) -> str:
    """Generate a prompt for LLM to create a structured summary.
    
    Returns a JSON-formatted prompt string that can be copied to an agent.
    """
    # Truncate README if too long
    max_chars = 8000
    content = readme_content[:max_chars]
    if len(readme_content) > max_chars:
        content += "\n\n[... truncated for brevity ...]"
    
    prompt_data = {
        "task": f"为 skill repo '{repo_name}' 生成结构化摘要",
        "instructions": (
            "请分析以下 README 内容，提取仓库的目的、核心功能、价值主张、"
            "目标用户和技术栈。输出必须是以下格式的 JSON："
        ),
        "output_format": {
            "purpose": "一句话描述仓库的核心目的（30字以内）",
            "features": ["核心功能1", "核心功能2", "核心功能3"],
            "value": "为用户提供的主要价值（50字以内）",
            "target_users": "目标用户群体（20字以内）",
            "tech_stack": ["技术1", "技术2"],
        },
        "repo_name": repo_name,
        "readme": content,
    }
    return json.dumps(prompt_data, ensure_ascii=False, indent=2)


def find_repo_readme(repo_dir: Path) -> Optional[Path]:
    """Find README file path in a repo directory."""
    for name in ["README.md", "Readme.md", "readme.md"]:
        path = repo_dir / name
        if path.is_file():
            return path
    return None


def read_repo_readme(repo_dir: Path) -> Optional[str]:
    """Read README.md content from a repo directory."""
    path = find_repo_readme(repo_dir)
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def generate_summary_via_local_agent(repo_name: str, readme_content: str) -> Optional[dict]:
    """Call local agent CLI (e.g., opencode) to generate a structured summary.

    Uses AGENT_CMD env var (default: opencode). The agent is invoked as:
        <AGENT_CMD> run <prompt>

    Returns the parsed summary dict, or None if agent is not available or fails.
    """
    import os
    import subprocess

    agent_cmd = os.environ.get("AGENT_CMD", "opencode").strip()
    if not agent_cmd:
        return None

    # Truncate README if too long
    max_chars = 8000
    content = readme_content[:max_chars]
    if len(readme_content) > max_chars:
        content += "\n\n[... truncated for brevity ...]"

    prompt = (
        f"Analyze the following README for repo '{repo_name}' and extract structured info. "
        f"Respond ONLY with a JSON object (no markdown, no explanations).\n\n"
        f"README content:\n{content}\n\n"
        "Required JSON format:\n"
        '{\n'
        '  "purpose": "one sentence describing the repo purpose",\n'
        '  "features": ["feature 1", "feature 2"],\n'
        '  "value": "main value proposition",\n'
        '  "target_users": "who should use this",\n'
        '  "tech_stack": ["tech 1", "tech 2"]\n'
        '}'
    )

    try:
        result = subprocess.run(
            [agent_cmd, "run", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        # Try to find JSON in the output (agent may wrap it in markdown or add extra text)
        json_start = output.find('{')
        json_end = output.rfind('}')
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            return None

        parsed = json.loads(output[json_start:json_end + 1])
        # Validate required fields
        if not isinstance(parsed.get("purpose"), str):
            parsed["purpose"] = ""
        if not isinstance(parsed.get("features"), list):
            parsed["features"] = []
        if not isinstance(parsed.get("value"), str):
            parsed["value"] = ""
        if not isinstance(parsed.get("target_users"), str):
            parsed["target_users"] = ""
        if not isinstance(parsed.get("tech_stack"), list):
            parsed["tech_stack"] = []
        return parsed
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, Exception):
        return None
