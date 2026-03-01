"""Bilingual skill storage manager - manages English and Chinese versions of skills."""

import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

from skill_hub.ai.translator import ContentTranslator
from skill_hub.models import BilingualConfig, Config
from skill_hub.utils import ensure_directory, expand_home

logger = logging.getLogger(__name__)


class BilingualStorageManager:
    """Manages bilingual skill storage with language switching."""

    def __init__(self, config: Config):
        """Initialize bilingual storage manager.

        Args:
            config: Application configuration with bilingual settings
        """
        self.config = config
        self.bilingual_config = config.bilingual
        self.hub_path = expand_home("~/.agents/skills")
        self.backup_path = expand_home(self.bilingual_config.backup_path)
        self.translator = ContentTranslator(config.ai) if config.ai.enabled else None

    def initialize_backup_directories(self) -> None:
        """Initialize backup directory structure for both languages."""
        ensure_directory(self.backup_path)
        ensure_directory(self.backup_path / "en")
        ensure_directory(self.backup_path / "zh_CN")
        logger.info(f"Initialized bilingual backup directories at {self.backup_path}")

    def store_skill_version(
        self, skill_name: str, content: str, language: str
    ) -> bool:
        """Store a skill version in the backup directory.

        Args:
            skill_name: Name of the skill
            content: Skill content (markdown)
            language: Language code ('en' or 'zh_CN')

        Returns:
            True if stored successfully
        """
        if language not in {"en", "zh_CN"}:
            logger.error(f"Invalid language: {language}")
            return False

        skill_dir = self.backup_path / language / skill_name
        ensure_directory(skill_dir)
        skill_file = skill_dir / "SKILL.md"

        try:
            skill_file.write_text(content, encoding="utf-8")
            logger.debug(f"Stored {language} version of skill '{skill_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to store {language} version: {e}")
            return False

    def translate_and_store(
        self, skill_name: str, content: str, source_language: str
    ) -> Tuple[bool, Optional[str]]:
        """Translate skill content and store both versions.

        Args:
            skill_name: Name of the skill
            content: Original skill content
            source_language: Source language ('en' or 'zh_CN')

        Returns:
            Tuple of (success, translated_content or None)
        """
        if not self.bilingual_config.enabled:
            logger.debug("Bilingual storage disabled")
            return False, None

        if not self.translator:
            logger.warning("No translator available")
            return False, None

        # Determine target language
        target_language = "zh_CN" if source_language == "en" else "en"

        # Translate
        if source_language == "en":
            translated = self.translator.translate_to_chinese(content)
        else:
            logger.error("Translation from Chinese to English not yet supported")
            return False, None

        if translated is None:
            logger.error("Translation failed")
            return False, None

        # Store both versions
        self.store_skill_version(skill_name, content, source_language)
        self.store_skill_version(skill_name, translated, target_language)

        logger.info(
            f"Stored bilingual versions for skill '{skill_name}' ({source_language} <-> {target_language})"
        )
        return True, translated

    def switch_language(self, target_language: str) -> bool:
        """Switch active skills to the target language version.

        Args:
            target_language: Target language ('en' or 'zh_CN')

        Returns:
            True if switched successfully
        """
        if target_language not in {"en", "zh_CN"}:
            logger.error(f"Invalid language: {target_language}")
            return False

        backup_lang_dir = self.backup_path / target_language

        if not backup_lang_dir.exists():
            logger.error(f"Backup directory not found: {backup_lang_dir}")
            return False

        try:
            # Backup current hub skills
            if self.hub_path.exists():
                current_backup = self.backup_path / f"current_backup_{target_language}"
                if current_backup.exists():
                    shutil.rmtree(current_backup)
                shutil.copytree(self.hub_path, current_backup)
                logger.debug(f"Backed up current hub skills to {current_backup}")

            # Copy target language skills to hub
            if self.hub_path.exists():
                shutil.rmtree(self.hub_path)

            shutil.copytree(backup_lang_dir, self.hub_path)
            logger.info(f"Switched hub skills to {target_language}")

            return True

        except Exception as e:
            logger.error(f"Failed to switch language: {e}")
            return False

    def get_available_languages(self, skill_name: str) -> list[str]:
        """Get list of available languages for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of language codes (e.g., ['en', 'zh_CN'])
        """
        available = []
        for lang in ["en", "zh_CN"]:
            skill_file = self.backup_path / lang / skill_name / "SKILL.md"
            if skill_file.exists():
                available.append(lang)
        return available

    def sync_skill_to_backup(
        self, skill_name: str, content: str, auto_translate: bool = True
    ) -> bool:
        """Sync a skill to backup storage, optionally translating.

        Args:
            skill_name: Name of the skill
            content: Skill content (assumed to be English)
            auto_translate: Whether to auto-translate

        Returns:
            True if synced successfully
        """
        # Store English version
        self.store_skill_version(skill_name, content, "en")

        # Optionally translate and store Chinese version
        if auto_translate and self.translator:
            translated = self.translator.translate_to_chinese(content)
            if translated:
                self.store_skill_version(skill_name, translated, "zh_CN")
                return True
            else:
                logger.warning(f"Translation failed for skill '{skill_name}'")

        return True

    def is_bilingual_available(self, skill_name: str) -> bool:
        """Check if both language versions are available for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            True if both en and zh_CN versions exist
        """
        en_file = self.backup_path / "en" / skill_name / "SKILL.md"
        zh_file = self.backup_path / "zh_CN" / skill_name / "SKILL.md"
        return en_file.exists() and zh_file.exists()
