"""Base LLM provider interface and configuration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional


@dataclass
class ValidationError:
    """A validation error for a configuration field."""

    field: str
    message: str


@dataclass
class ProviderConfigField:
    """Schema for a provider configuration field."""

    name: str
    type: Literal["string", "number", "boolean", "password"]
    label: str
    placeholder: str
    required: bool = False
    options: List[str] = field(default_factory=list)
    help: str = ""


@dataclass
class ProviderConfigSchema:
    """Schema for provider configuration."""

    provider_type: str
    fields: List[ProviderConfigField]


@dataclass
class ProviderConfig:
    """Provider configuration."""

    provider_type: str
    name: str
    endpoint: str = ""
    api_key: str = ""
    model: str = ""
    is_active: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a completion from the LLM.

        Args:
            system_prompt: System/context prompt
            user_prompt: User query prompt

        Returns:
            LLM response text

        Raises:
            ConnectionError: If unable to connect to the LLM service
            RuntimeError: If the LLM returns an error
        """
        pass

    @abstractmethod
    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion from the LLM.

        Args:
            system_prompt: System/context prompt
            user_prompt: User query prompt

        Yields:
            Chunks of LLM response text

        Raises:
            ConnectionError: If unable to connect to the LLM service
            RuntimeError: If the LLM returns an error
        """
        pass

    @abstractmethod
    def validate_config(self, config: ProviderConfig) -> List[ValidationError]:
        """Validate provider configuration.

        Args:
            config: Provider configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> ProviderConfigSchema:
        """Return the configuration schema for this provider.

        Returns:
            Provider configuration schema
        """
        pass
