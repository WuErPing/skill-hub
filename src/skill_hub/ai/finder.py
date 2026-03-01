"""AI-powered skill finder service."""

import json
import logging
import re
from typing import AsyncGenerator, List, Optional, Tuple

from skill_hub.ai.config.manager import ProviderConfig
from skill_hub.ai.providers import (
    LLMProvider,
    create_provider,
    get_available_providers,
)
from skill_hub.ai.prompts import build_prompt
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
        self.provider: Optional[LLMProvider] = None
        self.sync_engine = SyncEngine(config)
        
        # Initialize provider based on new config structure
        self._init_provider()

    def _init_provider(self) -> None:
        """Initialize the LLM provider from config."""
        if not self.config.ai.enabled:
            return

        # Try new multi-provider config first
        if hasattr(self.config.ai, 'providers') and self.config.ai.providers:
            # Find active provider
            active_id = self.config.ai.active_provider_id
            for prov_config in self.config.ai.providers:
                if prov_config.get('id') == active_id or prov_config.get('is_active'):
                    try:
                        provider_config = ProviderConfig(
                            id=prov_config.get('id', 0),
                            provider_type=prov_config.get('provider_type', 'ollama'),
                            name=prov_config.get('name', 'Provider'),
                            endpoint=prov_config.get('endpoint', ''),
                            model=prov_config.get('model', ''),
                            api_key=prov_config.get('api_key', ''),
                            is_active=prov_config.get('is_active', False),
                        )
                        self.provider = create_provider(provider_config)
                        logger.info(f"Initialized provider: {provider_config.provider_type}")
                        return
                    except Exception as e:
                        logger.error(f"Failed to initialize provider: {e}")
                        continue
        
        # Fallback to legacy config
        if not self.provider:
            self._init_legacy_provider()

    def _init_legacy_provider(self) -> None:
        """Initialize provider from legacy config structure."""
        try:
            if self.config.ai.provider == "ollama":
                provider_config = ProviderConfig(
                    id=0,
                    provider_type="ollama",
                    name="Ollama",
                    endpoint=self.config.ai.ollama_url,
                    model=self.config.ai.ollama_model,
                )
                self.provider = create_provider(provider_config)
                logger.info("Initialized Ollama provider from legacy config")
            elif self.config.ai.provider == "openai":
                provider_config = ProviderConfig(
                    id=0,
                    provider_type="openai",
                    name="OpenAI",
                    endpoint=self.config.ai.api_url,
                    model=self.config.ai.api_model,
                    api_key=self.config.ai.api_key,
                )
                self.provider = create_provider(provider_config)
                logger.info("Initialized OpenAI provider from legacy config")
        except Exception as e:
            logger.error(f"Failed to initialize legacy provider: {e}")

    def _load_hub_skills(self) -> List[dict]:
        """Load all skills from the hub with their metadata.

        Returns:
            List of skill dicts with 'name', 'description', and 'path' keys
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
                        "path": str(skill_file),
                    })

        return skills

    def _parse_response(self, response: str, skills_data: dict) -> List[SkillMatch]:
        """Parse LLM response into SkillMatch objects.

        Args:
            response: Raw LLM response text
            skills_data: Map of skill name to dict with 'description' and 'path'

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
            if skill_name not in skills_data:
                continue

            score = float(item.get("score", 0.0))
            reasoning = item.get("reasoning", "")
            skill_info = skills_data[skill_name]

            matches.append(SkillMatch(
                name=skill_name,
                description=skill_info["description"],
                score=min(1.0, max(0.0, score)),  # Clamp to [0, 1]
                reasoning=reasoning,
                path=skill_info["path"],
            ))

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    def find_skills(
        self, query: str, top_k: int = 5
    ) -> Tuple[List[SkillMatch], Optional[str]]:
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

        # Build skill name -> data map (description and path)
        skills_data = {s["name"]: {"description": s["description"], "path": s["path"]} for s in skills}

        # Build prompts
        system_prompt, user_prompt = build_prompt(query, skills, top_k)

        # Call provider
        try:
            response = self.provider.generate(system_prompt, user_prompt)
            matches = self._parse_response(response, skills_data)
            return matches[:top_k], None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Provider failed: {e}")
            return [], f"Provider error: {error_msg}"

    async def find_skills_stream(
        self, query: str, top_k: int = 5
    ) -> AsyncGenerator[str, None]:
        """Find relevant skills for a query with streaming response.

        Args:
            query: User's search query
            top_k: Maximum number of results to return

        Yields:
            Chunks of the LLM response
        """
        if not self.config.ai.enabled:
            yield "AI finder is disabled in configuration"
            return

        if not self.provider:
            yield "No AI provider configured"
            return

        # Load skills from hub
        skills = self._load_hub_skills()
        if not skills:
            yield "No skills found in hub. Run 'skill-hub pull' first."
            return

        # Build skill name -> data map (description and path)
        skills_data = {s["name"]: {"description": s["description"], "path": s["path"]} for s in skills}

        # Build prompts
        system_prompt, user_prompt = build_prompt(query, skills, top_k)

        # Stream from provider
        try:
            async for chunk in self.provider.generate_stream(system_prompt, user_prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Stream provider failed: {e}")
            yield f"Stream error: {str(e)}"

    def is_available(self) -> Tuple[bool, str]:
        """Check if AI finder is available.

        Returns:
            Tuple of (is_available, status_message)
        """
        if not self.config.ai.enabled:
            return False, "AI finder is disabled"

        if not self.provider:
            return False, "No AI provider configured"

        return True, f"Using provider: {type(self.provider).__name__}"
