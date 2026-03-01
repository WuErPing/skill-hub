"""Ollama LLM provider implementation."""

import logging
from typing import AsyncGenerator, List

import httpx

from skill_hub.ai.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderConfigField,
    ProviderConfigSchema,
    ValidationError,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize Ollama provider.

        Args:
            config: Provider configuration
        """
        self.endpoint = config.endpoint or "http://localhost:11434"
        self.endpoint = self.endpoint.rstrip("/")
        self.model = config.model
        self.timeout = 120.0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion using Ollama API."""
        endpoint = f"{self.endpoint}/api/generate"
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.endpoint}: {e}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.endpoint}. "
                "Make sure Ollama is running with 'ollama serve'."
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise RuntimeError(f"Ollama request failed: {e}") from e

    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using Ollama API.

        Args:
            system_prompt: System/context prompt
            user_prompt: User query prompt

        Yields:
            Chunks of LLM response text
        """
        endpoint = f"{self.endpoint}/api/generate"
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", endpoint, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            import json

                            result = json.loads(line)
                            if "response" in result:
                                chunk = result["response"]
                                if chunk:
                                    yield chunk
                            if result.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.endpoint}: {e}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.endpoint}. "
                "Make sure Ollama is running with 'ollama serve'."
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Ollama stream request failed: {e}")
            raise RuntimeError(f"Ollama stream request failed: {e}") from e

    def validate_config(self, config: ProviderConfig) -> List[ValidationError]:
        """Validate Ollama provider configuration.

        Args:
            config: Provider configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not config.model:
            errors.append(
                ValidationError(
                    field="model",
                    message="Model name is required",
                )
            )

        if config.endpoint and not config.endpoint.startswith("http"):
            errors.append(
                ValidationError(
                    field="endpoint",
                    message="Endpoint must be a valid HTTP URL",
                )
            )

        return errors

    def get_config_schema(self) -> ProviderConfigSchema:
        """Return the configuration schema for Ollama.

        Returns:
            Provider configuration schema
        """
        return ProviderConfigSchema(
            provider_type="ollama",
            fields=[
                ProviderConfigField(
                    name="name",
                    type="string",
                    label="Provider Name",
                    placeholder="e.g., Local Ollama",
                    required=True,
                    help="A friendly name for this provider",
                ),
                ProviderConfigField(
                    name="endpoint",
                    type="string",
                    label="Endpoint",
                    placeholder="http://localhost:11434",
                    required=False,
                    help="Ollama server endpoint (default: http://localhost:11434)",
                ),
                ProviderConfigField(
                    name="model",
                    type="string",
                    label="Model",
                    placeholder="e.g., llama2, gpt-oss:20b",
                    required=True,
                    help="Model name to use (run 'ollama list' for available models)",
                ),
            ],
        )
