"""Integration tests for SSE streaming."""

import pytest
from skill_hub.ai.streaming import (
    sanitize_for_json,
    escape_newlines,
    format_sse_event,
    get_sse_headers,
)


class TestStreamingUtilities:
    """Tests for streaming utility functions."""

    def test_sanitize_for_json_removes_control_chars(self):
        """Test sanitizing removes control characters."""
        text = "Hello\x00World\x1F"
        sanitized = sanitize_for_json(text)
        assert "\x00" not in sanitized
        assert "\x1F" not in sanitized
        assert "Hello" in sanitized
        assert "World" in sanitized

    def test_sanitize_for_json_preserves_printable(self):
        """Test sanitizing preserves printable chars."""
        text = "Hello World! 123\n\t\r"
        sanitized = sanitize_for_json(text)
        assert sanitized == text

    def test_escape_newlines(self):
        """Test escaping newlines."""
        text = "Line 1\nLine 2\r\nLine 3\r"
        escaped = escape_newlines(text)
        assert "\\n" in escaped
        assert "\n" not in escaped
        assert "\r" not in escaped

    def test_format_sse_event_data(self):
        """Test formatting data event."""
        event = format_sse_event("data", {"chunk": "test"})
        assert "event: data" in event
        assert '"chunk": "test"' in event
        assert event.endswith("\n\n")

    def test_format_sse_event_error(self):
        """Test formatting error event."""
        event = format_sse_event("error", {"message": "test error"})
        assert "event: error" in event
        assert '"message": "test error"' in event

    def test_format_sse_event_done(self):
        """Test formatting done event."""
        event = format_sse_event("done", {"done": True})
        assert "event: done" in event
        assert '"done": true' in event

    def test_get_sse_headers(self):
        """Test getting SSE headers."""
        headers = get_sse_headers()
        assert headers["Content-Type"] == "text/event-stream"
        assert headers["Cache-Control"] == "no-cache"
        assert headers["Connection"] == "keep-alive"
        assert headers["X-Accel-Buffering"] == "no"
        assert headers["Access-Control-Allow-Origin"] == "*"


class TestProviderStreaming:
    """Integration tests for provider streaming."""

    @pytest.mark.asyncio
    async def test_ollama_stream_interface(self):
        """Test Ollama stream interface (mock)."""
        from skill_hub.ai.providers import create_provider, ProviderConfig
        
        config = ProviderConfig(
            provider_type="ollama",
            name="Test",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        provider = create_provider(config)
        
        # Mock the HTTP call
        import httpx
        original_stream = httpx.AsyncClient.stream
        
        async def mock_stream(self, method, url, **kwargs):
            class MockResponse:
                async def aiter_lines(self):
                    yield '{"response": "Hello", "done": false}'
                    yield '{"response": " World", "done": true}'
            return MockResponse()
        
        httpx.AsyncClient.stream = mock_stream
        
        try:
            chunks = []
            async for chunk in provider.generate_stream("system", "user"):
                chunks.append(chunk)
            
            assert len(chunks) == 2
            assert "Hello" in chunks[0]
            assert "World" in chunks[1]
        finally:
            httpx.AsyncClient.stream = original_stream


class TestFinderStreaming:
    """Integration tests for AI finder streaming."""

    @pytest.mark.asyncio
    async def test_finder_stream_method_exists(self):
        """Test that finder has streaming method."""
        from skill_hub.models import Config
        from skill_hub.ai.finder import AISkillFinder
        
        config = Config()
        finder = AISkillFinder(config)
        
        assert hasattr(finder, 'find_skills_stream')
        assert callable(getattr(finder, 'find_skills_stream'))
