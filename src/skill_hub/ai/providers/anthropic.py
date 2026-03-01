"""Anthropic LLM provider implementation."""

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


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration
        """
        self.endpoint = config.endpoint or "https://api.anthropic.com/v1"
        self.endpoint = self.endpoint.rstrip("/")
        if not self.endpoint.endswith("/messages"):
            self.endpoint += "/messages"
        self.api_key = config.api_key
        self.model = config.model
        self.timeout = 60.0
        self.api_version = "2023-06-01"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion using Anthropic API."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "system": system_prompt,
            "max_tokens": 4096,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                if "content" in result and len(result["content"]) > 0:
                    return result["content"][0].get("text", "")
                return ""
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Anthropic API at {self.endpoint}: {e}")
            raise ConnectionError(
                f"Cannot connect to Anthropic API at {self.endpoint}"
            ) from e
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
            logger.error(f"Anthropic API request failed: {e}")
            raise RuntimeError(f"Anthropic API request failed: {e}") from e

    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using Anthropic API.

        Args:
            system_prompt: System/context prompt
            user_prompt: User query prompt

        Yields:
            Chunks of LLM response text
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "system": system_prompt,
            "max_tokens": 4096,
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
                            try:
                                import json

                                result = json.loads(data)
                                if result.get("type") == "content_block_delta":
                                    delta = result.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            yield text
                                elif result.get("type") == "message_stop":
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Anthropic API at {self.endpoint}: {e}")
            raise ConnectionError(
                f"Cannot connect to Anthropic API at {self.endpoint}"
            ) from e
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
            logger.error(f"Anthropic stream request failed: {e}")
            raise RuntimeError(f"Anthropic stream request failed: {e}") from e

    def validate_config(self, config: ProviderConfig) -> List[ValidationError]:
        """Validate Anthropic provider configuration.

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
        elif not config.api_key.startswith("sk-ant-"):
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API key must start with 'sk-ant-'",
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
        """Return the configuration schema for Anthropic.

        Returns:
            Provider configuration schema
        """
        return ProviderConfigSchema(
            provider_type="anthropic",
            fields=[
                ProviderConfigField(
                    name="name",
                    type="string",
                    label="Provider Name",
                    placeholder="e.g., Anthropic Claude-3",
                    required=True,
                    help="A friendly name for this provider",
                ),
                ProviderConfigField(
                    name="endpoint",
                    type="string",
                    label="Endpoint",
                    placeholder="https://api.anthropic.com/v1/messages",
                    required=False,
                    help="Anthropic API endpoint (default: https://api.anthropic.com/v1/messages)",
                ),
                ProviderConfigField(
                    name="model",
                    type="string",
                    label="Model",
                    placeholder="e.g., claude-3-opus-20240229",
                    required=True,
                    help="Model name to use",
                ),
                ProviderConfigField(
                    name="api_key",
                    type="password",
                    label="API Key",
                    placeholder="sk-ant-...",
                    required=True,
                    help="Your Anthropic API key",
                ),
            ],
        )
