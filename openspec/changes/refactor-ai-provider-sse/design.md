# Design: AI Provider Refactor with SSE Streaming

## Architecture Overview

```
skill_hub/
├── ai/
│   ├── providers/
│   │   ├── base.py          # Abstract LLMProvider interface
│   │   ├── ollama.py        # Ollama implementation
│   │   ├── openai.py        # OpenAI implementation
│   │   ├── anthropic.py     # Anthropic implementation (NEW)
│   │   └── __init__.py      # Provider factory
│   ├── config/
│   │   ├── schema.py        # Provider config schemas (NEW)
│   │   ├── manager.py       # Config management (NEW)
│   │   └── validator.py     # Validation logic (NEW)
│   ├── streaming/
│   │   ├── sse.py           # SSE helper utilities (NEW)
│   │   └── generator.py     # Stream generators (NEW)
│   ├── finder.py            # Skill finder (refactored)
│   └── translator.py        # Translator (refactored)
└── web/
    ├── fastapi_app.py       # SSE endpoints (updated)
    └── templates/
        └── config.html      # Config UI (updated)
```

## Key Design Decisions

### 1. Provider Interface (from idone)

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Non-streaming generation"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Streaming generation yielding chunks"""
        pass
    
    @abstractmethod
    def validate_config(self, config: dict) -> list[ValidationError]:
        """Validate provider configuration"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> ProviderConfigSchema:
        """Return configuration schema"""
        pass
```

**Rationale**: Mirrors idone's Go interface, provides clean separation of streaming/non-streaming.

### 2. Config Schema System

```python
@dataclass
class ProviderConfigField:
    name: str
    type: Literal["string", "number", "boolean", "password"]
    label: str
    placeholder: str
    required: bool = False
    help: str = ""

@dataclass
class ProviderConfigSchema:
    provider_type: str
    fields: list[ProviderConfigField]
```

**Rationale**: Enables dynamic form generation in web UI, consistent validation.

### 3. SSE Streaming Endpoint

```python
@app.post("/api/ai/analyze-stream")
async def analyze_skills_stream(request: AIAnalyzeRequest):
    async def event_generator():
        async for chunk in provider.generate_stream(system_prompt, user_prompt):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

**Rationale**: Follows idone's SSE pattern, compatible with EventSource API in browser.

### 4. Provider Factory Pattern

```python
def create_provider(config: ProviderConfig) -> LLMProvider:
    """Create provider instance from config"""
    if config.provider_type == "ollama":
        return OllamaProvider(config)
    elif config.provider_type == "openai":
        return OpenAIProvider(config)
    elif config.provider_type == "anthropic":
        return AnthropicProvider(config)
    raise ValueError(f"Unknown provider: {config.provider_type}")
```

**Rationale**: Clean provider instantiation, easy to extend.

## Implementation Strategy

1. Create new provider package structure
2. Implement base interface and utilities
3. Refactor existing providers (Ollama, OpenAI)
4. Add new provider (Anthropic)
5. Add config schema and validation
6. Implement SSE endpoints
7. Update web UI for streaming
8. Add tests

## Migration Path

- Existing `complete()` method remains for backward compatibility
- Gradual migration of callers to new `generate()` interface
- Streaming opt-in via new endpoints

## Testing Strategy

- Unit tests for each provider
- Integration tests with mock servers
- SSE endpoint tests with stream validation
- Config validation tests
