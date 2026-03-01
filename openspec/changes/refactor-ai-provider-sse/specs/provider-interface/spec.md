# Spec: Provider Interface Design

## Overview

Design a unified LLM provider interface supporting multiple providers (Ollama, OpenAI, Anthropic) with both synchronous and streaming capabilities.

## Provider Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate completion synchronously."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate completion with streaming."""
        pass
    
    @abstractmethod
    def validate_config(self, config: ProviderConfig) -> List[ValidationError]:
        """Validate provider configuration."""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> ProviderConfigSchema:
        """Get configuration schema for UI forms."""
        pass
```

## Configuration Schema

```python
@dataclass
class ProviderConfig:
    id: int
    provider_type: str  # "ollama", "openai", "anthropic"
    name: str
    endpoint: str
    model: str
    api_key: str = ""
    is_active: bool = False

@dataclass
class ProviderConfigField:
    name: str
    type: Literal["string", "number", "boolean", "password"]
    label: str
    placeholder: str
    required: bool = False
    help: str = ""
```

## Provider Implementations

### Ollama Provider

- **Endpoint**: `/api/generate`
- **Format**: Single prompt (combine system + user)
- **Streaming**: JSON lines with `response` field
- **Auth**: None (localhost)

```python
payload = {
    "model": model,
    "prompt": f"{system}\n\n{user}",
    "stream": True,
}
```

### OpenAI Provider

- **Endpoint**: `/v1/chat/completions`
- **Format**: Messages array with roles
- **Streaming**: SSE with `data: ` prefix
- **Auth**: Bearer token

```python
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ],
    "stream": True,
}
```

### Anthropic Provider

- **Endpoint**: `/v1/messages`
- **Format**: Messages + system field
- **Streaming**: SSE with `data: ` prefix
- **Auth**: `x-api-key` header
- **Version**: `anthropic-version` header

```python
payload = {
    "model": model,
    "messages": [{"role": "user", "content": user}],
    "system": system,
    "max_tokens": 4096,
    "stream": True,
}
```

## Factory Pattern

```python
PROVIDER_REGISTRY = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

def create_provider(config: ProviderConfig) -> LLMProvider:
    provider_class = PROVIDER_REGISTRY.get(config.provider_type)
    if not provider_class:
        raise ValueError(f"Unknown provider: {config.provider_type}")
    return provider_class(config)
```

## Validation Rules

### Ollama
- `model`: required
- `endpoint`: must start with `http` if provided

### OpenAI
- `model`: required
- `api_key`: required, min 20 chars
- `endpoint`: must start with `http`

### Anthropic
- `model`: required
- `api_key`: required, must start with `sk-ant-`
- `endpoint`: must start with `http`

## Extension Points

New providers can be added by:

1. Creating new provider class inheriting from `LLMProvider`
2. Implementing all abstract methods
3. Registering in `PROVIDER_REGISTRY`

Example:

```python
class GoogleProvider(LLMProvider):
    # Implementation

register_provider("google", GoogleProvider)
```

## Backward Compatibility

Legacy config structure supported:

```python
# Old format
config.ai.provider = "ollama"
config.ai.ollama_url = "http://localhost:11434"
config.ai.ollama_model = "llama2"

# New format
config.ai.providers = [
    {
        "id": 1,
        "provider_type": "ollama",
        "name": "Local Ollama",
        "endpoint": "http://localhost:11434",
        "model": "llama2",
        "is_active": True,
    }
]
```

Finder automatically detects and uses appropriate format.
