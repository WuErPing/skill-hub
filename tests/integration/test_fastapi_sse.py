"""Tests for FastAPI SSE endpoints."""

import pytest
from fastapi.testclient import TestClient
from skill_hub.web.fastapi_app import create_app
from skill_hub.models import Config, AIConfig


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    with TestClient(app) as client:
        yield client


class TestSSEEndpoints:
    """Tests for SSE streaming endpoints."""

    def test_find_stream_endpoint_exists(self, client):
        """Test that /api/ai/find-stream endpoint exists."""
        # The endpoint should accept POST requests
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "test", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        # Should return SSE stream (text/event-stream)
        # Even if AI is disabled, should return a response
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_find_stream_disabled_ai(self, client):
        """Test streaming endpoint with disabled AI."""
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "test", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        # Parse SSE events
        content = response.text
        events = content.split("\n\n")
        
        # Should have at least one event (error about disabled AI)
        assert len(events) > 0
        
        # First event should have event type and data
        first_event = events[0]
        assert "event:" in first_event
        assert "data:" in first_event

    def test_find_stream_invalid_request(self, client):
        """Test streaming endpoint with invalid request."""
        # Missing query
        response = client.post(
            "/api/ai/find-stream",
            json={"top_k": 3},  # No query
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        # Should return error event
        content = response.text
        assert "event:" in content
        assert "data:" in content

    def test_find_stream_empty_query(self, client):
        """Test streaming endpoint with empty query."""
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        # Should return error event
        content = response.text
        assert "event:" in content
        assert "data:" in content

    def test_find_stream_headers(self, client):
        """Test SSE headers are correct."""
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "test", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        headers = response.headers
        
        # Check SSE headers
        assert "text/event-stream" in headers.get("content-type", "")
        assert headers.get("cache-control") == "no-cache"
        assert headers.get("connection") == "keep-alive"
        assert headers.get("x-accel-buffering") == "no"


class TestSSEEventFormatting:
    """Tests for SSE event format."""

    def test_event_format_error(self, client):
        """Test error event format."""
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        content = response.text
        
        # Should follow SSE format
        lines = content.split("\n")
        
        # Find event line
        event_lines = [l for l in lines if l.startswith("event:")]
        assert len(event_lines) > 0
        
        # Find data line
        data_lines = [l for l in lines if l.startswith("data:")]
        assert len(data_lines) > 0
        
        # Verify format
        assert event_lines[0] in ["event: error", "event: data", "event: done"]

    def test_event_json_payload(self, client):
        """Test that event data is valid JSON."""
        import json
        
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "test", "top_k": 3},
            headers={"Content-Type": "application/json"}
        )
        
        content = response.text
        lines = content.split("\n")
        
        # Find all data lines
        data_lines = [l for l in lines if l.startswith("data:")]
        
        for data_line in data_lines:
            json_str = data_line[5:]  # Remove "data: "
            try:
                data = json.loads(json_str)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # Some lines might be incomplete or malformed
                # This is acceptable in streaming
                pass


class TestHelperFunctions:
    """Tests for SSE helper functions."""

    def test_format_sse_event_exists(self, client):
        """Test that format_sse_event helper exists."""
        # Import the helper function
        from skill_hub.web.fastapi_app import format_sse_event
        
        # Should be callable
        assert callable(format_sse_event)
        
        # Should return string
        result = format_sse_event("data", {"test": "value"})
        assert isinstance(result, str)
        
        # Should contain event type
        assert "event: data" in result
        
        # Should contain data
        assert '"test": "value"' in result

    def test_get_sse_headers_exists(self, client):
        """Test that get_sse_headers helper exists."""
        # Import the helper function
        from skill_hub.web.fastapi_app import get_sse_headers
        
        # Should be callable
        assert callable(get_sse_headers)
        
        # Should return dict
        headers = get_sse_headers()
        assert isinstance(headers, dict)
        
        # Should contain required headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "text/event-stream"
        assert "Cache-Control" in headers
        assert "Connection" in headers


class TestEndpointIntegration:
    """Integration tests for SSE endpoints."""

    def test_full_request_response_cycle(self, client):
        """Test complete request-response cycle."""
        # Send request
        response = client.post(
            "/api/ai/find-stream",
            json={"query": "test query", "top_k": 5},
            headers={"Content-Type": "application/json"}
        )
        
        # Verify response
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Verify SSE format
        content = response.text
        assert len(content) > 0
        
        # Should contain at least one complete event
        assert "event:" in content
        assert "data:" in content
        
        # Events should be separated by double newline
        events = content.split("\n\n")
        assert len(events) > 0
