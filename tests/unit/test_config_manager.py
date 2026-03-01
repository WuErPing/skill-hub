"""Tests for provider configuration manager."""

import pytest
from skill_hub.ai.config.manager import ProviderConfig, ProviderConfigManager


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_create_basic_config(self):
        """Test creating basic config."""
        config = ProviderConfig(
            id=1,
            provider_type="ollama",
            name="Test Provider",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        assert config.id == 1
        assert config.provider_type == "ollama"
        assert config.name == "Test Provider"
        assert config.endpoint == "http://localhost:11434"
        assert config.model == "llama2"
        assert config.api_key == ""
        assert config.is_active == False

    def test_create_config_with_api_key(self):
        """Test creating config with API key."""
        config = ProviderConfig(
            id=1,
            provider_type="openai",
            name="OpenAI",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-test123",
            is_active=True,
        )
        
        assert config.api_key == "sk-test123"
        assert config.is_active == True

    def test_create_config_with_extra(self):
        """Test creating config with extra fields."""
        config = ProviderConfig(
            id=1,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
            extra={"temperature": 0.7, "max_tokens": 2048},
        )
        
        assert config.extra == {"temperature": 0.7, "max_tokens": 2048}


class TestProviderConfigManager:
    """Tests for ProviderConfigManager."""

    def test_add_provider(self):
        """Test adding a provider."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        provider_id = manager.add_provider(config)
        
        assert provider_id == 1
        assert len(manager.list_providers()) == 1

    def test_add_multiple_providers(self):
        """Test adding multiple providers."""
        manager = ProviderConfigManager()
        
        config1 = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Ollama",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        config2 = ProviderConfig(
            id=0,
            provider_type="openai",
            name="OpenAI",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-test",
        )
        
        id1 = manager.add_provider(config1)
        id2 = manager.add_provider(config2)
        
        assert id1 == 1
        assert id2 == 2
        assert len(manager.list_providers()) == 2

    def test_get_provider_by_id(self):
        """Test getting provider by ID."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        provider_id = manager.add_provider(config)
        retrieved = manager.get_provider(provider_id)
        
        assert retrieved is not None
        assert retrieved.id == provider_id
        assert retrieved.name == "Test"

    def test_get_nonexistent_provider(self):
        """Test getting nonexistent provider."""
        manager = ProviderConfigManager()
        
        retrieved = manager.get_provider(999)
        assert retrieved is None

    def test_set_active_provider(self):
        """Test setting active provider."""
        manager = ProviderConfigManager()
        
        config1 = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Ollama",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        config2 = ProviderConfig(
            id=0,
            provider_type="openai",
            name="OpenAI",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            api_key="sk-test",
        )
        
        id1 = manager.add_provider(config1)
        id2 = manager.add_provider(config2)
        
        # Set second provider as active
        result = manager.set_active_provider(id2)
        
        assert result == True
        active = manager.get_active_provider()
        assert active is not None
        assert active.id == id2
        
        # First provider should be deactivated
        providers = manager.list_providers()
        assert providers[0].is_active == False
        assert providers[1].is_active == True

    def test_set_active_nonexistent_provider(self):
        """Test setting active nonexistent provider."""
        manager = ProviderConfigManager()
        
        result = manager.set_active_provider(999)
        assert result == False

    def test_update_provider(self):
        """Test updating provider."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Ollama",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        provider_id = manager.add_provider(config)
        
        # Update the provider
        result = manager.update_provider(provider_id, {
            "name": "Updated Ollama",
            "model": "llama3",
        })
        
        assert result == True
        
        updated = manager.get_provider(provider_id)
        assert updated.name == "Updated Ollama"
        assert updated.model == "llama3"

    def test_update_nonexistent_provider(self):
        """Test updating nonexistent provider."""
        manager = ProviderConfigManager()
        
        result = manager.update_provider(999, {"name": "Test"})
        assert result == False

    def test_delete_provider(self):
        """Test deleting provider."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        
        provider_id = manager.add_provider(config)
        
        result = manager.delete_provider(provider_id)
        
        assert result == True
        assert len(manager.list_providers()) == 0
        assert manager.get_provider(provider_id) is None

    def test_delete_nonexistent_provider(self):
        """Test deleting nonexistent provider."""
        manager = ProviderConfigManager()
        
        result = manager.delete_provider(999)
        assert result == False

    def test_delete_active_provider(self):
        """Test deleting active provider clears active."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
            is_active=True,
        )
        
        provider_id = manager.add_provider(config)
        
        # Verify it's active
        assert manager.get_active_provider() is not None
        
        # Delete it
        result = manager.delete_provider(provider_id)
        assert result == True
        
        # Active should be cleared
        assert manager.get_active_provider() is None

    def test_add_provider_with_active_flag(self):
        """Test adding provider with is_active=True sets it as active."""
        manager = ProviderConfigManager()
        
        config = ProviderConfig(
            id=0,
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
            is_active=True,
        )
        
        provider_id = manager.add_provider(config)
        
        active = manager.get_active_provider()
        assert active is not None
        assert active.id == provider_id
        assert active.is_active == True

    def test_list_providers(self):
        """Test listing all providers."""
        manager = ProviderConfigManager()
        
        # Add 3 providers
        for i in range(3):
            config = ProviderConfig(
                id=0,
                provider_type="ollama",
                name=f"Provider {i}",
                endpoint="http://localhost:11434",
                model=f"model{i}",
            )
            manager.add_provider(config)
        
        providers = manager.list_providers()
        
        assert len(providers) == 3
        assert all(isinstance(p, ProviderConfig) for p in providers)
