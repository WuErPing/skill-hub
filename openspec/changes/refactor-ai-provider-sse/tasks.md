# Tasks: Refactor AI Provider with SSE Streaming

## Implementation Tasks

- [x] **Task 1**: Create provider package structure
  - [x] Create `skill_hub/ai/providers/` package
  - [x] Implement `base.py` with `LLMProvider` abstract class
  - [x] Implement `ollama.py` with `OllamaProvider`
  - [x] Implement `openai.py` with `OpenAIProvider`
  - [x] Implement `anthropic.py` with `AnthropicProvider`
  - [x] Implement `factory.py` with provider factory

- [x] **Task 2**: Add streaming utilities
  - [x] Implement `streaming.py` with SSE helpers
  - [x] Add `sanitize_for_json()` function
  - [x] Add `escape_newlines()` function
  - [x] Add `format_sse_event()` function
  - [x] Add `stream_generator()` async generator
  - [x] Add `get_sse_headers()` function

- [x] **Task 3**: Implement config management
  - [x] Create `skill_hub/ai/config/` package
  - [x] Implement `ProviderConfig` dataclass
  - [x] Implement `ProviderConfigManager` class

- [x] **Task 4**: Refactor existing AI finder to use new providers
  - [x] Update `finder.py` to use new provider interface
  - [x] Replace direct provider instantiation with factory
  - [x] Update error handling
  - [x] Add `find_skills_stream()` async method

- [x] **Task 5**: Implement SSE endpoints in FastAPI
  - [x] Add `/api/ai/find-stream` endpoint
  - [x] Configure proper SSE headers
  - [x] Add error handling for streaming
  - [x] Add helper functions for SSE formatting

- [ ] **Task 6**: Update web UI for streaming
  - [ ] Update `find.html` to use EventSource API
  - [ ] Add real-time response display
  - [ ] Add loading indicators
  - [ ] Handle stream completion gracefully

- [ ] **Task 7**: Add tests
  - [ ] Unit tests for each provider
  - [ ] Integration tests with mock servers
  - [ ] SSE endpoint tests
  - [ ] Config manager tests

## Notes

- Maintain backward compatibility where possible
- Ensure all providers implement both sync and async interfaces
- Follow idone's patterns for SSE streaming
- Test with real LLM providers

## Summary

**Completed**: Tasks 1-5 (core infrastructure complete)
**Remaining**: Web UI updates (Task 6) and tests (Task 7)

The core refactoring is complete:
- New provider interface with streaming support
- Three provider implementations (Ollama, OpenAI, Anthropic)
- SSE streaming utilities
- FastAPI streaming endpoint
- Backward compatibility with legacy config
