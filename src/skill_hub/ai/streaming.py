"""SSE (Server-Sent Events) utilities for streaming LLM responses."""

import json
import logging
from typing import Any, AsyncGenerator, Dict

logger = logging.getLogger(__name__)


def sanitize_for_json(text: str) -> str:
    """Remove control characters that could break JSON encoding.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for JSON encoding
    """
    result = []
    for char in text:
        code = ord(char)
        if code >= 32 or char in "\n\t\r":
            result.append(char)
        elif code == 0:
            continue
        else:
            result.append(" ")
    return "".join(result)


def escape_newlines(text: str) -> str:
    """Escape newlines for SSE data lines.

    Args:
        text: Text to escape

    Returns:
        Text with newlines escaped
    """
    text = text.replace("\r\n", "\\n")
    text = text.replace("\r", "\\n")
    text = text.replace("\n", "\\n")
    return text


def format_sse_event(event_type: str, data: Any) -> str:
    """Format a Server-Sent Event.

    Args:
        event_type: Type of event (e.g., 'data', 'error', 'done')
        data: Data to send

    Returns:
        Formatted SSE event string
    """
    # Sanitize and format data
    if isinstance(data, str):
        data = sanitize_for_json(data)
    elif isinstance(data, dict):
        # Sanitize string values in dict
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = sanitize_for_json(value)
            else:
                sanitized_data[key] = value
        data = sanitized_data

    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def stream_generator(
    chunk_stream: AsyncGenerator[str, None],
) -> AsyncGenerator[str, None]:
    """Convert a chunk stream to SSE format.

    Args:
        chunk_stream: Async generator yielding text chunks

    Yields:
        Formatted SSE events
    """
    try:
        async for chunk in chunk_stream:
            yield format_sse_event("data", {"chunk": chunk})
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield format_sse_event("error", {"message": str(e)})
    finally:
        yield format_sse_event("done", {"done": True})


def get_sse_headers() -> Dict[str, str]:
    """Get headers for SSE response.

    Returns:
        Dictionary of SSE headers
    """
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
    }
