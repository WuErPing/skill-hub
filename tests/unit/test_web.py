"""Basic tests for the web interface."""

from __future__ import annotations

from typing import Any

from skill_hub.web import create_app


def test_create_app() -> None:
    app = create_app()
    assert app is not None


def test_index_page() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    text: str = response.get_data(as_text=True)
    assert "skill-hub Web UI" in text


def test_api_config() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/api/config")
    assert response.status_code == 200
    data: Any = response.get_json()
    assert data["ok"] is True
    assert "config" in data
