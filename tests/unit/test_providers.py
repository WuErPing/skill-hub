"""Unit tests for new provider interface."""

import pytest
from skill_hub.ai.providers import (
    create_provider,
    ProviderConfig,
    LLMProvider,
)
from skill_hub.ai.providers.ollama import OllamaProvider
from skill_hub.ai.providers.openai import OpenAIProvider
from skill_hub.ai.providers.anthropic import AnthropicProvider


class TestProviderFactory:
    """Tests for provider factory."""

    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        config = ProviderConfig(
            provider_type="ollama",
            name="Test Ollama",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        provider = create_provider(config)
        assert isinstance(provider, OllamaProvider)
        assert provider.model == "llama2"

    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = ProviderConfig(
            provider_type="openai",
            name="Test OpenAI",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-test",
        )
        provider = create_provider(config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4"

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = ProviderConfig(
            provider_type="anthropic",
            name="Test Anthropic",
            endpoint="https://api.anthropic.com/v1",
            model="claude-3",
            api_key="sk-ant-test",
        )
        provider = create_provider(config)
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-3"

    def test_create_unknown_provider(self):
        """Test creating unknown provider raises error."""
        config = ProviderConfig(
            provider_type="unknown",
            name="Unknown",
            endpoint="http://example.com",
            model="test",
        )
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_provider(config)


class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = ProviderConfig(
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 0

    def test_validate_config_missing_model(self):
        """Test validating config with missing model."""
        config = ProviderConfig(
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert errors[0].field == "model"

    def test_get_config_schema(self):
        """Test getting config schema."""
        config = ProviderConfig(
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        provider = create_provider(config)
        schema = provider.get_config_schema()
        assert schema.provider_type == "ollama"
        assert len(schema.fields) > 0


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = ProviderConfig(
            provider_type="openai",
            name="Test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-12345678901234567890",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 0

    def test_validate_config_missing_api_key(self):
        """Test validating config with missing API key."""
        config = ProviderConfig(
            provider_type="openai",
            name="Test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert errors[0].field == "api_key"

    def test_validate_config_short_api_key(self):
        """Test validating config with short API key."""
        config = ProviderConfig(
            provider_type="openai",
            name="Test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-short",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert "too short" in errors[0].message


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = ProviderConfig(
            provider_type="anthropic",
            name="Test",
            endpoint="https://api.anthropic.com/v1",
            model="claude-3",
            api_key="sk-ant-12345678901234567890",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 0

    def test_validate_config_invalid_api_key_prefix(self):
        """Test validating config with invalid API key prefix."""
        config = ProviderConfig(
            provider_type="anthropic",
            name="Test",
            endpoint="https://api.anthropic.com/v1",
            model="claude-3",
            api_key="sk-invalid",
        )
        provider = create_provider(config)
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert "must start with" in errors[0].message


class TestProviderInterface:
    """Tests for provider interface compliance."""

    def test_ollama_implements_interface(self):
        """Test Ollama implements LLMProvider interface."""
        config = ProviderConfig(
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        provider = create_provider(config)
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_stream')
        assert hasattr(provider, 'validate_config')
        assert hasattr(provider, 'get_config_schema')

    def test_openai_implements_interface(self):
        """Test OpenAI implements LLMProvider interface."""
        config = ProviderConfig(
            provider_type="openai",
            name="Test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-test",
        )
        provider = create_provider(config)
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_stream')
        assert hasattr(provider, 'validate_config')
        assert hasattr(provider, 'get_config_schema')

    def test_anthropic_implements_interface(self):
        """Test Anthropic implements LLMProvider interface."""
        config = ProviderConfig(
            provider_type="anthropic",
            name="Test",
            endpoint="https://api.anthropic.com/v1",
            model="claude-3",
            api_key="sk-ant-test",
        )
        provider = create_provider(config)
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_stream')
        assert hasattr(provider, 'validate_config')
        assert hasattr(provider, 'get_config_schema')
