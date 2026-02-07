"""AI-powered skill finder service."""

import json
import logging
import re
from typing import List, Optional

from skill_hub.ai.prompts import build_prompt
from skill_hub.ai.providers import create_fallback_provider, create_provider
from skill_hub.models import Config, SkillMatch
from skill_hub.sync import SyncEngine
from skill_hub.utils import parse_skill_file_from_path

logger = logging.getLogger(__name__)


class AISkillFinder:
    """AI-powered skill finder service."""

    def __init__(self, config: Config):
        """Initialize AI skill finder.

        Args:
            config: Application configuration
        """
        self.config = config
        self.provider = create_provider(config.ai)
        self.fallback_provider = create_fallback_provider(config.ai)
        self.sync_engine = SyncEngine(config)

    def _load_hub_skills(self) -> List[dict]:
        """Load all skills from the hub with their metadata.

        Returns:
            List of skill dicts with 'name' and 'description' keys
        """
        skills = []
        skill_names = self.sync_engine.list_hub_skills()

        for skill_name in skill_names:
            skill_dir = self.sync_engine.hub_path / skill_name
            skill_file = skill_dir / "SKILL.md"

            if skill_file.exists():
                result = parse_skill_file_from_path(skill_file)
                if result:
                    metadata, _ = result
                    skills.append({
                        "name": metadata.name,
                        "description": metadata.description,
                    })

        return skills

    def _parse_response(self, response: str, skills_map: dict) -> List[SkillMatch]:
        """Parse LLM response into SkillMatch objects.

        Args:
            response: Raw LLM response text
            skills_map: Map of skill name to description

        Returns:
            List of SkillMatch objects
        """
        # Try to extract JSON from response
        # Sometimes LLMs wrap JSON in markdown code blocks
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            logger.warning("No JSON array found in response")
            return []

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return []

        matches = []
        for item in data:
            skill_name = item.get("skill", "")
            if skill_name not in skills_map:
                continue

            score = float(item.get("score", 0.0))
            reasoning = item.get("reasoning", "")

            matches.append(SkillMatch(
                name=skill_name,
                description=skills_map[skill_name],
                score=min(1.0, max(0.0, score)),  # Clamp to [0, 1]
                reasoning=reasoning,
            ))

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    def find_skills(
        self, query: str, top_k: int = 5
    ) -> tuple[List[SkillMatch], Optional[str]]:
        """Find relevant skills for a query.

        Args:
            query: User's search query
            top_k: Maximum number of results to return

        Returns:
            Tuple of (list of SkillMatch objects, error message or None)
        """
        if not self.config.ai.enabled:
            return [], "AI finder is disabled in configuration"

        if not self.provider:
            return [], "No AI provider configured"

        # Load skills from hub
        skills = self._load_hub_skills()
        if not skills:
            return [], "No skills found in hub. Run 'skill-hub pull' first."

        # Build skill name -> description map
        skills_map = {s["name"]: s["description"] for s in skills}

        # Build prompts
        system_prompt, user_prompt = build_prompt(query, skills, top_k)

        # Try primary provider
        error_msg = None
        try:
            response = self.provider.complete(system_prompt, user_prompt)
            matches = self._parse_response(response, skills_map)
            return matches[:top_k], None
        except ConnectionError as e:
            error_msg = str(e)
            logger.warning(f"Primary provider failed: {e}")

        # Try fallback provider if available
        if self.fallback_provider:
            try:
                logger.info("Trying fallback provider...")
                response = self.fallback_provider.complete(system_prompt, user_prompt)
                matches = self._parse_response(response, skills_map)
                return matches[:top_k], None
            except Exception as e:
                logger.warning(f"Fallback provider also failed: {e}")
                error_msg = f"All providers failed. Primary: {error_msg}, Fallback: {e}"

        return [], error_msg

    def is_available(self) -> tuple[bool, str]:
        """Check if AI finder is available.

        Returns:
            Tuple of (is_available, status_message)
        """
        if not self.config.ai.enabled:
            return False, "AI finder is disabled"

        if not self.provider:
            return False, "No AI provider configured"

        return True, f"Using {self.config.ai.provider} provider"
