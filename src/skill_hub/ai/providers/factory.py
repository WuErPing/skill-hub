"""Provider factory for creating LLM provider instances."""

import logging
from typing import Dict, List, Optional, Type

from skill_hub.ai.providers.base import LLMProvider, ProviderConfig
from skill_hub.ai.providers.ollama import OllamaProvider
from skill_hub.ai.providers.openai import OpenAIProvider
from skill_hub.ai.providers.anthropic import AnthropicProvider

logger = logging.getLogger(__name__)

# Registry of available providers
PROVIDER_REGISTRY: Dict[str, Type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def create_provider(config: ProviderConfig) -> LLMProvider:
    """Create a provider instance from configuration.

    Args:
        config: Provider configuration

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    provider_class = PROVIDER_REGISTRY.get(config.provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {config.provider_type}")

    return provider_class(config)


def get_available_providers() -> List[str]:
    """Get list of available provider types.

    Returns:
        List of provider type names
    """
    return list(PROVIDER_REGISTRY.keys())


def register_provider(provider_type: str, provider_class: Type[LLMProvider]) -> None:
    """Register a new provider type.

    Args:
        provider_type: Provider type name
        provider_class: Provider class to register
    """
    PROVIDER_REGISTRY[provider_type] = provider_class
    logger.info(f"Registered provider: {provider_type}")
