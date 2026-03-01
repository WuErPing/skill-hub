"""OpenAI-compatible LLM provider implementation."""

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


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible LLM provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        self.endpoint = config.endpoint or "https://api.openai.com/v1"
        self.endpoint = self.endpoint.rstrip("/")
        if not self.endpoint.endswith("/chat/completions"):
            self.endpoint += "/chat/completions"
        self.api_key = config.api_key
        self.model = config.model
        self.timeout = 60.0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion using OpenAI-compatible API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to API at {self.endpoint}: {e}")
            raise ConnectionError(f"Cannot connect to API at {self.endpoint}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid API key. Check your configuration.") from e
            elif e.response.status_code == 429:
                raise RuntimeError(
                    "API rate limit exceeded. Try again later."
                ) from e
            else:
                raise RuntimeError(f"API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"API request failed: {e}") from e

    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using OpenAI-compatible API.

        Args:
            system_prompt: System/context prompt
            user_prompt: User query prompt

        Yields:
            Chunks of LLM response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self.endpoint, json=payload, headers=headers
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                break
                            try:
                                import json

                                result = json.loads(data)
                                if "choices" in result and len(result["choices"]) > 0:
                                    delta = result["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to API at {self.endpoint}: {e}")
            raise ConnectionError(f"Cannot connect to API at {self.endpoint}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid API key. Check your configuration.") from e
            elif e.response.status_code == 429:
                raise RuntimeError(
                    "API rate limit exceeded. Try again later."
                ) from e
            else:
                raise RuntimeError(f"API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"API stream request failed: {e}")
            raise RuntimeError(f"API stream request failed: {e}") from e

    def validate_config(self, config: ProviderConfig) -> List[ValidationError]:
        """Validate OpenAI provider configuration.

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

        if not config.api_key:
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API key is required",
                )
            )
        elif len(config.api_key) < 20:
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API key appears to be invalid (too short)",
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
        """Return the configuration schema for OpenAI.

        Returns:
            Provider configuration schema
        """
        return ProviderConfigSchema(
            provider_type="openai",
            fields=[
                ProviderConfigField(
                    name="name",
                    type="string",
                    label="Provider Name",
                    placeholder="e.g., OpenAI GPT-4",
                    required=True,
                    help="A friendly name for this provider",
                ),
                ProviderConfigField(
                    name="endpoint",
                    type="string",
                    label="Endpoint",
                    placeholder="https://api.openai.com/v1/chat/completions",
                    required=False,
                    help="OpenAI API endpoint (default: https://api.openai.com/v1/chat/completions)",
                ),
                ProviderConfigField(
                    name="model",
                    type="string",
                    label="Model",
                    placeholder="e.g., gpt-4, gpt-3.5-turbo",
                    required=True,
                    help="Model name to use",
                ),
                ProviderConfigField(
                    name="api_key",
                    type="password",
                    label="API Key",
                    placeholder="sk-...",
                    required=True,
                    help="Your OpenAI API key",
                ),
            ],
        )
