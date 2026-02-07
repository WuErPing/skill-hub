"""AI-powered content translator for skill previews."""

import logging
from typing import Optional, Tuple

from skill_hub.ai.providers import LLMProvider, create_provider
from skill_hub.models import AIConfig

logger = logging.getLogger(__name__)


class ContentTranslator:
    """Translate markdown content using AI providers."""

    def __init__(self, config: AIConfig):
        """Initialize translator with AI config.

        Args:
            config: AI configuration for LLM provider
        """
        self.config = config
        self.provider = create_provider(config) if config.enabled else None

    def is_available(self) -> Tuple[bool, str]:
        """Check if translator is available.

        Returns:
            Tuple of (available, status_message)
        """
        if not self.config.enabled:
            return False, "AI translation is disabled in configuration"

        if not self.provider:
            return False, "No AI provider configured for translation"

        return True, f"Translation available using {self.config.provider}"

    def translate_to_chinese(self, content: str) -> Optional[str]:
        """Translate English content to Chinese.

        Args:
            content: Markdown content in English

        Returns:
            Translated content in Chinese, or None if translation fails
        """
        if not self.provider:
            logger.warning("No AI provider available for translation")
            return None

        system_prompt = """You are a professional technical translator specializing in software documentation and skill guides.

Your task is to translate English markdown content to Chinese (Simplified Chinese).

IMPORTANT RULES:
1. Preserve all markdown formatting (headings, code blocks, lists, links, bold, italic, etc.)
2. Keep code blocks and code snippets unchanged
3. Keep URLs and file paths unchanged
4. Translate technical terms accurately while maintaining clarity
5. Use natural Chinese expressions suitable for developers
6. Maintain the original structure and formatting
7. Do NOT add any explanations or additional content
8. Output ONLY the translated markdown content"""

        user_prompt = f"""Translate the following markdown content to Chinese:

{content}"""

        try:
            translated = self.provider.complete(system_prompt, user_prompt)
            return translated.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return None

    def detect_language(self, content: str) -> str:
        """Detect the primary language of the content.

        Args:
            content: Content to detect language from

        Returns:
            'en' for English, 'zh' for Chinese, 'unknown' otherwise
        """
        # Simple heuristic: count Chinese characters
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        total_chars = len([c for c in content if c.isalnum()])

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh"
        elif chinese_ratio < 0.1:
            return "en"
        else:
            return "unknown"
