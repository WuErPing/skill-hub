"""Simple LLM client using stdlib urllib. No external dependencies.

Supports OpenAI-compatible APIs via environment variables:
- OPENAI_API_KEY: required
- OPENAI_BASE_URL: optional, defaults to https://api.openai.com/v1
- LLM_MODEL: optional, defaults to gpt-4o-mini
"""

import json
import os
import urllib.request
from typing import Optional


def _get_api_key() -> Optional[str]:
    return os.environ.get("OPENAI_API_KEY")


def _get_base_url() -> str:
    return os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def _get_model() -> str:
    return os.environ.get("LLM_MODEL", "gpt-4o-mini")


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[str]:
    """Call LLM API and return the response content.

    Returns None if API key is not set or request fails.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    base_url = _get_base_url()
    model = _get_model()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None
