"""Internationalization utilities for skill-hub.

This module provides a simple wrapper around Python's gettext
for translating user-facing strings in both CLI and web interfaces.
"""

from __future__ import annotations

import gettext
from pathlib import Path
from typing import Optional

_translator: Optional[gettext.GNUTranslations] = None
_current_language: str = "en"


def init_translation(language: str = "en") -> None:
    """Initialize translation system with specified language.

    If the requested language is not available, falls back to English
    and then to no-op translations as a last resort.
    """
    global _translator, _current_language

    locales_dir = Path(__file__).parent / "locales"

    try:
        _translator = gettext.translation(
            "messages",
            localedir=str(locales_dir),
            languages=[language],
            fallback=True,
        )
        _current_language = language
    except Exception:
        # Fallback to NullTranslations (returns original strings)
        _translator = gettext.NullTranslations()
        _current_language = "en"


def _(message: str) -> str:  # noqa: D401
    """Translate message to current language."""
    global _translator

    if _translator is None:
        init_translation()
    return _translator.gettext(message)


def get_current_language() -> str:
    """Get currently configured language."""
    return _current_language
