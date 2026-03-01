"""AI provider configuration management."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    id: int
    provider_type: str
    name: str
    endpoint: str
    model: str
    api_key: str = ""
    is_active: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class ProviderConfigManager:
    """Manager for LLM provider configurations."""

    def __init__(self):
        """Initialize the config manager."""
        self._providers: Dict[int, ProviderConfig] = {}
        self._active_id: Optional[int] = None
        self._next_id: int = 1

    def add_provider(self, config: ProviderConfig) -> int:
        """Add a new provider configuration.

        Args:
            config: Provider configuration

        Returns:
            ID of the added provider
        """
        config.id = self._next_id
        self._next_id += 1
        self._providers[config.id] = config

        if config.is_active:
            self._active_id = config.id

        return config.id

    def get_provider(self, provider_id: int) -> Optional[ProviderConfig]:
        """Get a provider configuration by ID.

        Args:
            provider_id: Provider ID

        Returns:
            Provider configuration or None if not found
        """
        return self._providers.get(provider_id)

    def get_active_provider(self) -> Optional[ProviderConfig]:
        """Get the active provider configuration.

        Returns:
            Active provider configuration or None
        """
        if self._active_id:
            return self._providers.get(self._active_id)
        return None

    def set_active_provider(self, provider_id: int) -> bool:
        """Set the active provider.

        Args:
            provider_id: Provider ID to activate

        Returns:
            True if successful, False if provider not found
        """
        if provider_id not in self._providers:
            return False

        self._active_id = provider_id
        # Deactivate others
        for config in self._providers.values():
            if config.id != provider_id:
                config.is_active = False
            else:
                config.is_active = True

        return True

    def update_provider(self, provider_id: int, updates: Dict[str, Any]) -> bool:
        """Update a provider configuration.

        Args:
            provider_id: Provider ID
            updates: Dictionary of fields to update

        Returns:
            True if successful, False if provider not found
        """
        config = self._providers.get(provider_id)
        if not config:
            return False

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return True

    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider configuration.

        Args:
            provider_id: Provider ID to delete

        Returns:
            True if successful, False if provider not found
        """
        if provider_id not in self._providers:
            return False

        del self._providers[provider_id]

        if self._active_id == provider_id:
            self._active_id = None
            # Activate first remaining provider
            if self._providers:
                first_id = next(iter(self._providers.keys()))
                self.set_active_provider(first_id)

        return True

    def list_providers(self) -> List[ProviderConfig]:
        """List all provider configurations.

        Returns:
            List of provider configurations
        """
        return list(self._providers.values())
