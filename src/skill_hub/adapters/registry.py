"""Adapter registry for managing agent adapters."""

import logging
from typing import Dict, List, Optional

from skill_hub.adapters.antigravity import AntigravityAdapter
from skill_hub.adapters.base import AgentAdapter
from skill_hub.adapters.claude import ClaudeAdapter
from skill_hub.adapters.codex import CodexAdapter
from skill_hub.adapters.copilot import CopilotAdapter
from skill_hub.adapters.cursor import CursorAdapter
from skill_hub.adapters.gemini import GeminiAdapter
from skill_hub.adapters.opencode import OpenCodeAdapter
from skill_hub.adapters.qoder import QoderAdapter
from skill_hub.adapters.windsurf import WindsurfAdapter
from skill_hub.models import Config

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry for managing agent adapters."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize adapter registry.

        Args:
            config: Application configuration
        """
        self.config = config or Config()
        self._adapters: Dict[str, AgentAdapter] = {}
        self._load_adapters()

    def _load_adapters(self) -> None:
        """Load all available adapters."""
        adapter_classes = [
            AntigravityAdapter,
            ClaudeAdapter,
            CodexAdapter,
            CopilotAdapter,
            CursorAdapter,
            GeminiAdapter,
            OpenCodeAdapter,
            QoderAdapter,
            WindsurfAdapter,
        ]

        for adapter_class in adapter_classes:
            adapter = adapter_class()
            agent_name = adapter.name

            # Apply configuration if available
            if agent_name in self.config.agents:
                adapter.config = self.config.agents[agent_name]

            self._adapters[agent_name] = adapter
            logger.debug(f"Loaded adapter: {agent_name}")

    def get_adapter(self, name: str) -> Optional[AgentAdapter]:
        """
        Get adapter by name.

        Args:
            name: Agent name (antigravity, claude, codex, copilot, cursor, gemini, opencode, qoder, windsurf)

        Returns:
            AgentAdapter instance or None if not found
        """
        return self._adapters.get(name)

    def list_adapters(self) -> List[str]:
        """List all adapter names."""
        return list(self._adapters.keys())

    def get_enabled_adapters(self) -> List[AgentAdapter]:
        """Get list of enabled adapters."""
        return [adapter for adapter in self._adapters.values() if adapter.is_enabled()]

    def health_check_all(self) -> Dict[str, dict]:
        """
        Perform health check on all adapters.

        Returns:
            Dictionary mapping adapter name to health check results
        """
        results = {}
        for name, adapter in self._adapters.items():
            results[name] = adapter.health_check()
        return results
