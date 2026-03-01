# Spec: SSE Streaming Support

## Overview

Implement Server-Sent Events (SSE) streaming for AI responses, following idone's proven architecture.

## Requirements

### Functional Requirements

1. **Streaming Endpoint**: POST `/api/ai/find-stream`
   - Accepts JSON with `query` and `top_k` fields
   - Returns SSE stream with progressive response chunks
   - Proper error handling within stream

2. **Provider Interface**: All providers must implement:
   - `generate()` - synchronous non-streaming
   - `generate_stream()` - async streaming generator
   - `validate_config()` - configuration validation
   - `get_config_schema()` - schema for UI forms

3. **Event Format**:
   ```javascript
   // Data event
   event: data
   data: {"chunk": "text content"}
   
   // Error event
   event: error
   data: {"message": "error description"}
   
   // Done event
   event: done
   data: {"done": true}
   ```

4. **Headers**:
   ```
   Content-Type: text/event-stream
   Cache-Control: no-cache
   Connection: keep-alive
   X-Accel-Buffering: no
   Access-Control-Allow-Origin: *
   ```

### Technical Requirements

- Async generator pattern for streaming
- Proper cleanup on client disconnect
- JSON sanitization for safe encoding
- Newline escaping for SSE format
- Fallback to non-streaming if provider doesn't support streaming

## Implementation

### Provider Streaming Pattern

```python
async def generate_stream(
    self, system_prompt: str, user_prompt: str
) -> AsyncGenerator[str, None]:
    """Stream LLM response."""
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", endpoint, json=payload) as response:
            async for line in response.aiter_lines():
                # Parse SSE format from provider
                if line.startswith("data: "):
                    yield parsed_chunk
```

### FastAPI Endpoint Pattern

```python
@app.post("/api/ai/find-stream")
async def find_stream(request: Request):
    async def generate():
        async for chunk in finder.find_skills_stream(query):
            yield format_sse_event("data", {"chunk": chunk})
        yield format_sse_event("done", {"done": True})
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
```

### Client-Side Integration

```javascript
const eventSource = new EventSource('/api/ai/find-stream', {
    headers: { 'Content-Type': 'application/json' }
});

eventSource.addEventListener('data', (event) => {
    const data = JSON.parse(event.data);
    appendToDisplay(data.chunk);
});

eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    showError(data.message);
    eventSource.close();
});

eventSource.addEventListener('done', (event) => {
    eventSource.close();
});
```

## Testing

### Unit Tests

- Test each provider's `generate_stream()` method
- Mock HTTP responses for streaming
- Verify chunk parsing and yielding

### Integration Tests

- Test SSE endpoint with mock provider
- Verify event format and headers
- Test error handling in stream

### Manual Testing

- Test with real Ollama instance
- Test with real OpenAI API
- Verify browser EventSource integration

## Migration Notes

- Existing non-streaming endpoints remain unchanged
- Clients can opt-in to streaming via new endpoint
- Backward compatibility maintained for legacy config
