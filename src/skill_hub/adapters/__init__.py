"""Agent adapters for different AI coding assistants."""

from .antigravity import AntigravityAdapter
from .base import AgentAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .copilot import CopilotAdapter
from .cursor import CursorAdapter
from .gemini import GeminiAdapter
from .opencode import OpenCodeAdapter
from .qoder import QoderAdapter
from .registry import AdapterRegistry
from .windsurf import WindsurfAdapter

__all__ = [
    "AgentAdapter",
    "AntigravityAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "CursorAdapter",
    "GeminiAdapter",
    "OpenCodeAdapter",
    "QoderAdapter",
    "AdapterRegistry",
    "WindsurfAdapter",
]
