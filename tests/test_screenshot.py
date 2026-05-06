"""Tests for screenshot capture and README update functionality."""

import importlib.util
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the screenshot module from skill scripts directory
SCRIPT_PATH = Path(".agents/skills/project-version-update/scripts/screenshot.py")
spec = importlib.util.spec_from_file_location("screenshot_script", SCRIPT_PATH)
screenshot_module = importlib.util.module_from_spec(spec)
sys.modules["screenshot_script"] = screenshot_module
spec.loader.exec_module(screenshot_module)


class TestCaptureHomepageScreenshot:
    """Tests for capture_homepage_screenshot function."""

    def test_function_exists(self):
        """RED: capture_homepage_screenshot function should exist."""
        assert callable(screenshot_module.capture_homepage_screenshot)

    def test_captures_screenshot_and_returns_path(self, tmp_path):
        """RED: Should capture screenshot and return the file path."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()

        mock_page = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch.object(screenshot_module, "sync_playwright") as mock_sync_pw:
            mock_sync_pw.return_value.__enter__.return_value = mock_playwright
            result = screenshot_module.capture_homepage_screenshot(imgs_dir=str(imgs_dir))

        assert result is not None
        assert isinstance(result, (str, Path))
        assert Path(result).parent == imgs_dir
        mock_page.goto.assert_called_once_with("http://127.0.0.1:7860")
        mock_page.screenshot.assert_called_once()
        assert "full_page=True" in str(mock_page.screenshot.call_args)

    def test_uses_timestamped_filename(self, tmp_path):
        """RED: Screenshot filename should include timestamp."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()

        mock_page = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch.object(screenshot_module, "sync_playwright") as mock_sync_pw:
            mock_sync_pw.return_value.__enter__.return_value = mock_playwright
            result = screenshot_module.capture_homepage_screenshot(imgs_dir=str(imgs_dir))

        filename = Path(result).name
        # Should match YYYY-MM-DD-HH-MM-SS.png pattern
        assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.png", filename)


class TestUpdateReadmeScreenshots:
    """Tests for update_readme_screenshots function."""

    def test_function_exists(self):
        """RED: update_readme_screenshots function should exist."""
        assert callable(screenshot_module.update_readme_screenshots)

    def test_updates_readme_md(self, tmp_path):
        """RED: Should update README.md with new screenshot path."""
        readme = tmp_path / "README.md"
        readme.write_text("Line 1\n![](imgs/old-screenshot.png)\nLine 3\n")

        screenshot_module.update_readme_screenshots(
            str(readme),
            str(readme),
            "imgs/2026-05-04-12-00-00.png",
        )

        content = readme.read_text()
        assert "imgs/2026-05-04-12-00-00.png" in content
        assert "old-screenshot.png" not in content

    def test_updates_both_readmes(self, tmp_path):
        """RED: Should update both README.md and README.zh-CN.md."""
        readme_en = tmp_path / "README.md"
        readme_zh = tmp_path / "README.zh-CN.md"
        readme_en.write_text("![](imgs/old.png)\n")
        readme_zh.write_text("![](imgs/old.png)\n")

        screenshot_module.update_readme_screenshots(
            str(readme_en),
            str(readme_zh),
            "imgs/new-screenshot.png",
        )

        assert "imgs/new-screenshot.png" in readme_en.read_text()
        assert "imgs/new-screenshot.png" in readme_zh.read_text()
        assert "old.png" not in readme_en.read_text()
        assert "old.png" not in readme_zh.read_text()


class TestRemoveOldScreenshots:
    """Tests for remove_old_screenshots function."""

    def test_function_exists(self):
        """RED: remove_old_screenshots function should exist."""
        assert callable(screenshot_module.remove_old_screenshots)

    def test_removes_old_screenshots_except_current(self, tmp_path):
        """RED: Should remove old screenshots but keep current one."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()

        old1 = imgs_dir / "2026-04-24-00-54-50.png"
        old2 = imgs_dir / "2026-04-25-10-30-00.png"
        current = imgs_dir / "2026-05-04-12-00-00.png"
        old1.write_text("old1")
        old2.write_text("old2")
        current.write_text("current")

        screenshot_module.remove_old_screenshots(str(imgs_dir), str(current))

        assert not old1.exists()
        assert not old2.exists()
        assert current.exists()

    def test_keeps_non_png_files(self, tmp_path):
        """RED: Should not remove non-PNG files in imgs directory."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()

        old_png = imgs_dir / "2026-04-24-00-54-50.png"
        readme = imgs_dir / "README.txt"
        current = imgs_dir / "2026-05-04-12-00-00.png"
        old_png.write_text("old")
        readme.write_text("readme")
        current.write_text("current")

        screenshot_module.remove_old_screenshots(str(imgs_dir), str(current))

        assert not old_png.exists()
        assert readme.exists()
        assert current.exists()


class TestEnsureServerRunning:
    """Tests for ensure_server_running function."""

    def test_function_exists(self):
        """RED: ensure_server_running function should exist."""
        assert callable(screenshot_module.ensure_server_running)

    def test_does_nothing_if_server_already_running(self):
        """RED: Should not start server if already running."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = MagicMock()
            with patch("subprocess.Popen") as mock_popen:
                result = screenshot_module.ensure_server_running()

        mock_popen.assert_not_called()
        assert result is None

    def test_starts_server_if_not_running(self):
        """RED: Should start server if not already running."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection refused")
            with patch("subprocess.Popen") as mock_popen:
                with patch("time.sleep"):
                    screenshot_module.ensure_server_running()

        mock_popen.assert_called_once()
        assert "skill-hub" in str(mock_popen.call_args)
        assert "web" in str(mock_popen.call_args)


class TestUpdateScreenshotWorkflow:
    """Tests for the high-level update_screenshot workflow."""

    def test_function_exists(self):
        """RED: update_screenshot function should exist."""
        assert callable(screenshot_module.update_screenshot)

    def test_full_workflow(self, tmp_path):
        """RED: Full workflow should capture, update READMEs, and clean up."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()
        readme_en = tmp_path / "README.md"
        readme_zh = tmp_path / "README.zh-CN.md"
        readme_en.write_text("![](imgs/old.png)\n")
        readme_zh.write_text("![](imgs/old.png)\n")
        old_screenshot = imgs_dir / "old.png"
        old_screenshot.write_text("old")

        new_screenshot = imgs_dir / "2026-05-04-12-00-00.png"
        new_screenshot.write_text("new")

        with patch.object(
            screenshot_module, "capture_homepage_screenshot", return_value=new_screenshot
        ):
            with patch.object(
                screenshot_module, "verify_version_matches", return_value=True
            ):
                with patch("urllib.request.urlopen") as mock_urlopen:
                    mock_urlopen.return_value = MagicMock()
                    result = screenshot_module.update_screenshot(
                        imgs_dir=str(imgs_dir),
                        readme_en=str(readme_en),
                        readme_zh=str(readme_zh),
                    )

        assert result is not None
        assert Path(result).exists()
        assert "imgs/" in str(result)
        assert old_screenshot.exists() is False or "old.png" not in readme_en.read_text()
        assert "old.png" not in readme_en.read_text()
        assert "old.png" not in readme_zh.read_text()

    def test_version_mismatch_raises_error(self, tmp_path):
        """RED: Should raise error when version mismatch and user declines."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()
        readme_en = tmp_path / "README.md"
        readme_zh = tmp_path / "README.zh-CN.md"

        with patch.object(
            screenshot_module, "verify_version_matches", return_value=False
        ):
            with patch("builtins.input", return_value="n"):
                with pytest.raises(RuntimeError, match="Version mismatch"):
                    screenshot_module.update_screenshot(
                        imgs_dir=str(imgs_dir),
                        readme_en=str(readme_en),
                        readme_zh=str(readme_zh),
                    )

    def test_version_mismatch_with_override(self, tmp_path):
        """RED: Should continue when version mismatch but user overrides."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()
        readme_en = tmp_path / "README.md"
        readme_zh = tmp_path / "README.zh-CN.md"
        readme_en.write_text("![](imgs/old.png)\n")
        readme_zh.write_text("![](imgs/old.png)\n")

        new_screenshot = imgs_dir / "2026-05-04-12-00-00.png"
        new_screenshot.write_text("new")

        with patch.object(
            screenshot_module, "capture_homepage_screenshot", return_value=new_screenshot
        ):
            with patch.object(
                screenshot_module, "verify_version_matches", return_value=False
            ):
                with patch("builtins.input", return_value="y"):
                    with patch("urllib.request.urlopen") as mock_urlopen:
                        mock_urlopen.return_value = MagicMock()
                        result = screenshot_module.update_screenshot(
                            imgs_dir=str(imgs_dir),
                            readme_en=str(readme_en),
                            readme_zh=str(readme_zh),
                        )

        assert result is not None

    def test_skip_version_verification(self, tmp_path):
        """RED: Should skip version check when verify_version=False."""
        imgs_dir = tmp_path / "imgs"
        imgs_dir.mkdir()
        readme_en = tmp_path / "README.md"
        readme_zh = tmp_path / "README.zh-CN.md"
        readme_en.write_text("![](imgs/old.png)\n")
        readme_zh.write_text("![](imgs/old.png)\n")

        new_screenshot = imgs_dir / "2026-05-04-12-00-00.png"
        new_screenshot.write_text("new")

        with patch.object(
            screenshot_module, "capture_homepage_screenshot", return_value=new_screenshot
        ):
            # verify_version_matches should not be called
            with patch.object(
                screenshot_module, "verify_version_matches"
            ) as mock_verify:
                with patch("urllib.request.urlopen") as mock_urlopen:
                    mock_urlopen.return_value = MagicMock()
                    result = screenshot_module.update_screenshot(
                        imgs_dir=str(imgs_dir),
                        readme_en=str(readme_en),
                        readme_zh=str(readme_zh),
                        verify_version=False,
                    )

        mock_verify.assert_not_called()
        assert result is not None
