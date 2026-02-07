"""LLM provider implementations for AI skill finder."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from skill_hub.models import AIConfig

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
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


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""

    def __init__(self, url: str, model: str, timeout: float = 120.0):
        """Initialize Ollama provider.

        Args:
            url: Ollama API URL (e.g., http://localhost:11434)
            model: Model name (e.g., gpt-oss:120b)
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion using Ollama API."""
        endpoint = f"{self.url}/api/generate"

        # Combine prompts for Ollama's generate endpoint
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
            logger.error(f"Failed to connect to Ollama at {self.url}: {e}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.url}. "
                "Make sure Ollama is running with 'ollama serve'."
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise RuntimeError(f"Ollama request failed: {e}") from e


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider."""

    def __init__(self, api_url: str, api_key: str, model: str, timeout: float = 60.0):
        """Initialize OpenAI-compatible provider.

        Args:
            api_url: API base URL (e.g., https://api.openai.com/v1)
            api_key: API key for authentication
            model: Model name (e.g., gpt-4)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion using OpenAI-compatible API."""
        endpoint = f"{self.api_url}/chat/completions"

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
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to API at {self.api_url}: {e}")
            raise ConnectionError(f"Cannot connect to API at {self.api_url}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid API key. Check your configuration.") from e
            elif e.response.status_code == 429:
                raise RuntimeError("API rate limit exceeded. Try again later.") from e
            else:
                raise RuntimeError(f"API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"API request failed: {e}") from e


def create_provider(config: AIConfig) -> Optional[LLMProvider]:
    """Create an LLM provider based on configuration.

    Args:
        config: AI configuration

    Returns:
        LLMProvider instance or None if disabled
    """
    if not config.enabled:
        return None

    if config.provider == "ollama":
        return OllamaProvider(url=config.ollama_url, model=config.ollama_model)
    elif config.provider == "openai":
        if not config.api_key:
            logger.warning("OpenAI provider selected but no API key configured")
            return None
        return OpenAIProvider(
            api_url=config.api_url or "https://api.openai.com/v1",
            api_key=config.api_key,
            model=config.api_model,
        )
    else:
        logger.warning(f"Unknown AI provider: {config.provider}")
        return None


def create_fallback_provider(config: AIConfig) -> Optional[LLMProvider]:
    """Create a fallback provider (OpenAI if Ollama is primary).

    Args:
        config: AI configuration

    Returns:
        Fallback LLMProvider or None
    """
    if config.provider == "ollama" and config.api_key and config.api_url:
        return OpenAIProvider(
            api_url=config.api_url,
            api_key=config.api_key,
            model=config.api_model,
        )
    return None
