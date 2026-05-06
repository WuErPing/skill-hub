"""GitHub API wrapper for fetching repo author information."""

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class Author:
    username: str
    name: str
    bio: str
    avatar_url: str
    profile_url: str
    role: str  # "owner" | "contributor"
    contributions: int = 0


def _github_api_request(url: str) -> Optional[dict]:
    """Make a GitHub API request with optional GITHUB_TOKEN auth."""
    import os
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_repo_authors(repo_url: str) -> list[Author]:
    """Fetch owner and top contributors for a GitHub repo.
    
    Args:
        repo_url: Full GitHub URL like https://github.com/owner/repo
        
    Returns:
        List of Author objects, owner first, then top 3 contributors.
        Empty list if repo is not GitHub or request fails.
    """
    import re
    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if not match:
        return []
    
    owner, repo = match.group(1), match.group(2)
    authors = []
    
    # Fetch owner info
    owner_data = _github_api_request(f"https://api.github.com/users/{owner}")
    if owner_data:
        authors.append(Author(
            username=owner_data.get("login", owner),
            name=owner_data.get("name") or owner,
            bio=owner_data.get("bio") or "",
            avatar_url=owner_data.get("avatar_url", ""),
            profile_url=owner_data.get("html_url", f"https://github.com/{owner}"),
            role="owner",
            contributions=0,
        ))
    
    # Fetch top 3 contributors
    contributors = _github_api_request(
        f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=3"
    )
    if contributors:
        for contrib in contributors:
            username = contrib.get("login", "")
            if username == owner:
                continue  # Skip owner, already added
            user_data = _github_api_request(f"https://api.github.com/users/{username}")
            if user_data:
                authors.append(Author(
                    username=username,
                    name=user_data.get("name") or username,
                    bio=user_data.get("bio") or "",
                    avatar_url=user_data.get("avatar_url", ""),
                    profile_url=user_data.get("html_url", f"https://github.com/{username}"),
                    role="contributor",
                    contributions=contrib.get("contributions", 0),
                ))
    
    return authors
