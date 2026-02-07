"""Prompt templates for AI skill matching."""

SYSTEM_PROMPT = """You are an expert AI coding assistant that helps developers find relevant skills.
Given a user query and a catalog of available skills, identify the most relevant skills.

Output Format: JSON array with top matches, ordered by relevance.
[
  {{
    "skill": "skill-name",
    "score": 0.95,
    "reasoning": "Brief explanation of why this matches"
  }}
]

Scoring Guidelines:
- 0.9-1.0: Perfect match for the user's need
- 0.7-0.89: Strong relevance with minor gaps
- 0.5-0.69: Moderate relevance, may be helpful
- Below 0.5: Weak relevance, not recommended

Important:
- Only return the JSON array, no other text
- Only return top {top_k} results
- If no skills match well, return an empty array []
"""

USER_PROMPT_TEMPLATE = """User Query: "{query}"

Available Skills:
{skill_catalog}

Find the most relevant skills for this query. Return only JSON."""


def build_skill_catalog(skills: list[dict[str, str]], max_desc_length: int = 150) -> str:
    """Build a formatted skill catalog string.

    Args:
        skills: List of dicts with 'name' and 'description' keys
        max_desc_length: Maximum description length to include

    Returns:
        Formatted catalog string
    """
    lines = []
    for i, skill in enumerate(skills, 1):
        name = skill["name"]
        desc = skill["description"]
        if len(desc) > max_desc_length:
            desc = desc[:max_desc_length] + "..."
        lines.append(f"{i}. {name}: {desc}")
    return "\n".join(lines)


def build_prompt(query: str, skills: list[dict[str, str]], top_k: int = 5) -> tuple[str, str]:
    """Build system and user prompts for skill matching.

    Args:
        query: User's search query
        skills: List of skill dicts with 'name' and 'description'
        top_k: Number of results to return

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system = SYSTEM_PROMPT.format(top_k=top_k)
    catalog = build_skill_catalog(skills)
    user = USER_PROMPT_TEMPLATE.format(query=query, skill_catalog=catalog)
    return system, user
