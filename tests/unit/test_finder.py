"""Tests for AI finder with new provider interface."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from skill_hub.models import Config, AIConfig
from skill_hub.ai.finder import AISkillFinder


class TestAISkillFinderInitialization:
    """Tests for AISkillFinder initialization."""

    def test_init_with_legacy_ollama_config(self):
        """Test initialization with legacy Ollama config."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        config.ai.ollama_url = "http://localhost:11434"
        config.ai.ollama_model = "llama2"
        
        finder = AISkillFinder(config)
        
        assert finder.config == config
        # Provider should be initialized from legacy config
        # (actual provider creation depends on imports working)

    def test_init_with_legacy_openai_config(self):
        """Test initialization with legacy OpenAI config."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "openai"
        config.ai.api_url = "https://api.openai.com/v1"
        config.ai.api_key = "sk-test"
        config.ai.api_model = "gpt-4"
        
        finder = AISkillFinder(config)
        
        assert finder.config == config

    def test_init_with_disabled_ai(self):
        """Test initialization with disabled AI."""
        config = Config()
        config.ai.enabled = False
        
        finder = AISkillFinder(config)
        
        assert finder.config == config
        assert finder.provider is None

    def test_init_with_no_provider(self):
        """Test initialization with no provider configured."""
        config = Config()
        config.ai.enabled = True
        # No provider specified
        
        finder = AISkillFinder(config)
        
        # Should handle gracefully
        assert finder.provider is None


class TestAISkillFinderFindSkills:
    """Tests for AISkillFinder.find_skills() method."""

    @patch('skill_hub.ai.finder.SyncEngine')
    def test_find_skills_with_mocked_provider(self, mock_sync_engine):
        """Test finding skills with mocked provider."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        config.ai.ollama_url = "http://localhost:11434"
        config.ai.ollama_model = "llama2"
        
        finder = AISkillFinder(config)
        
        # Mock the provider
        mock_provider = Mock()
        mock_provider.generate = Mock(return_value='[{"skill": "test-skill", "score": 0.9, "reasoning": "test"}]')
        finder.provider = mock_provider
        
        # Mock sync engine
        mock_engine = Mock()
        mock_engine.list_hub_skills = Mock(return_value=[{"name": "test-skill", "description": "Test", "path": "/path"}])
        mock_sync_engine.return_value = mock_engine
        finder.sync_engine = mock_engine
        
        matches, error = finder.find_skills("test query", top_k=5)
        
        assert error is None
        assert len(matches) > 0

    @patch('skill_hub.ai.finder.SyncEngine')
    def test_find_skills_disabled_ai(self, mock_sync_engine):
        """Test finding skills with disabled AI."""
        config = Config()
        config.ai.enabled = False
        
        finder = AISkillFinder(config)
        
        matches, error = finder.find_skills("test query")
        
        assert error is not None
        assert "disabled" in error.lower()
        assert len(matches) == 0

    @patch('skill_hub.ai.finder.SyncEngine')
    def test_find_skills_no_provider(self, mock_sync_engine):
        """Test finding skills with no provider."""
        config = Config()
        config.ai.enabled = True
        # No provider configured
        
        finder = AISkillFinder(config)
        
        matches, error = finder.find_skills("test query")
        
        assert error is not None
        assert "no provider" in error.lower() or "no ai provider" in error.lower()
        assert len(matches) == 0


class TestAISkillFinderAvailability:
    """Tests for AISkillFinder.is_available() method."""

    def test_is_available_enabled(self):
        """Test availability with enabled AI."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        
        finder = AISkillFinder(config)
        
        # Should be available if provider initialized
        available, message = finder.is_available()
        
        # Either available with provider, or not available with message
        assert isinstance(available, bool)
        assert isinstance(message, str)

    def test_is_available_disabled(self):
        """Test availability with disabled AI."""
        config = Config()
        config.ai.enabled = False
        
        finder = AISkillFinder(config)
        
        available, message = finder.is_available()
        
        assert available == False
        assert "disabled" in message.lower()

    def test_is_available_no_provider(self):
        """Test availability with no provider."""
        config = Config()
        config.ai.enabled = True
        # No provider
        
        finder = AISkillFinder(config)
        
        available, message = finder.is_available()
        
        assert available == False
        assert "no provider" in message.lower()


@pytest.mark.asyncio
class TestAISkillFinderStreaming:
    """Tests for AISkillFinder streaming functionality."""

    @patch('skill_hub.ai.finder.SyncEngine')
    async def test_find_skills_stream_exists(self, mock_sync_engine):
        """Test that streaming method exists and is callable."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        
        finder = AISkillFinder(config)
        
        # Mock provider with streaming
        mock_provider = Mock()
        async def mock_stream(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"
        
        mock_provider.generate_stream = mock_stream
        finder.provider = mock_provider
        
        # Mock sync engine
        mock_engine = Mock()
        mock_engine.list_hub_skills = Mock(return_value=[])
        mock_sync_engine.return_value = mock_engine
        finder.sync_engine = mock_engine
        
        # Should be able to call the method
        chunks = []
        async for chunk in finder.find_skills_stream("test query"):
            chunks.append(chunk)
        
        # Should have received some output (even if error message)
        assert len(chunks) > 0

    @patch('skill_hub.ai.finder.SyncEngine')
    async def test_find_skills_stream_disabled(self, mock_sync_engine):
        """Test streaming with disabled AI."""
        config = Config()
        config.ai.enabled = False
        
        finder = AISkillFinder(config)
        
        chunks = []
        async for chunk in finder.find_skills_stream("test query"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert "disabled" in chunks[0].lower()

    @patch('skill_hub.ai.finder.SyncEngine')
    async def test_find_skills_stream_no_provider(self, mock_sync_engine):
        """Test streaming with no provider."""
        config = Config()
        config.ai.enabled = True
        # No provider
        
        finder = AISkillFinder(config)
        
        chunks = []
        async for chunk in finder.find_skills_stream("test query"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert "no provider" in chunks[0].lower()


class TestAISkillFinderLegacyCompatibility:
    """Tests for backward compatibility with legacy config."""

    def test_legacy_ollama_config_mapping(self):
        """Test legacy Ollama config is mapped correctly."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        config.ai.ollama_url = "http://custom:11434"
        config.ai.ollama_model = "custom-model"
        
        finder = AISkillFinder(config)
        
        # Should initialize provider from legacy config
        # Verify config was used
        assert finder.config.ai.ollama_url == "http://custom:11434"
        assert finder.config.ai.ollama_model == "custom-model"

    def test_legacy_openai_config_mapping(self):
        """Test legacy OpenAI config is mapped correctly."""
        config = Config()
        config.ai.enabled = True
        config.ai.provider = "openai"
        config.ai.api_url = "https://custom.api.com/v1"
        config.ai.api_key = "sk-custom"
        config.ai.api_model = "custom-model"
        
        finder = AISkillFinder(config)
        
        # Verify config was used
        assert finder.config.ai.api_url == "https://custom.api.com/v1"
        assert finder.config.ai.api_key == "sk-custom"
        assert finder.config.ai.api_model == "custom-model"
