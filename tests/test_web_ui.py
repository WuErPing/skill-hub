"""UI tests for skill-hub web interface using Playwright."""

import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from skill_hub.web.app import create_app


@pytest.fixture
def rendered_html():
    """Render the index.html template using Flask test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/")
        return resp.data.decode("utf-8")


@pytest.fixture
def browser(rendered_html):
    """Create a Playwright browser with the rendered HTML loaded."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Write HTML to temp file and load via file://
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(rendered_html)
            temp_path = f.name
        page.goto(f"file://{temp_path}")
        page.wait_for_load_state("domcontentloaded")
        yield page
        browser.close()
        Path(temp_path).unlink(missing_ok=True)


class TestSettingsPanel:
    """Tests for the settings panel UI."""

    def test_settings_panel_hidden_by_default(self, browser):
        """Settings panel should be hidden on initial page load."""
        panel = browser.locator("#settings-panel")
        assert panel.count() == 1
        assert "hidden" in panel.get_attribute("class")

    def test_settings_button_toggles_panel(self, browser):
        """Clicking settings button should show the panel."""
        settings_btn = browser.locator("#settings-wrap")
        panel = browser.locator("#settings-panel")
        
        settings_btn.click()
        assert "hidden" not in panel.get_attribute("class")
        
        settings_btn.click()
        assert "hidden" in panel.get_attribute("class")

    def test_settings_panel_has_title_and_close_button(self, browser):
        """Settings panel should have a title and close button."""
        settings_btn = browser.locator("#settings-wrap")
        settings_btn.click()
        
        title = browser.locator("#settings-panel h3")
        assert title.count() == 1
        assert title.text_content() in ["Settings", "设置"]
        
        close_btn = browser.locator("#settings-panel button[onclick*='toggleSettingsPanel']")
        assert close_btn.count() == 1

    def test_close_button_hides_panel(self, browser):
        """Clicking the close button should hide the settings panel."""
        settings_btn = browser.locator("#settings-wrap")
        settings_btn.click()
        
        close_btn = browser.locator("#settings-panel button[onclick*='toggleSettingsPanel']")
        close_btn.click()
        
        panel = browser.locator("#settings-panel")
        assert "hidden" in panel.get_attribute("class")

    def test_escape_key_closes_panel(self, browser):
        """Pressing Escape should close the settings panel."""
        settings_btn = browser.locator("#settings-wrap")
        settings_btn.click()
        
        browser.keyboard.press("Escape")
        
        panel = browser.locator("#settings-panel")
        assert "hidden" in panel.get_attribute("class")

    def test_only_one_panel_visible_at_a_time(self, browser):
        """Opening settings should close diagnosis panel and vice versa."""
        settings_btn = browser.locator("#settings-wrap")
        diagnose_btn = browser.locator("#btn-diagnose")
        
        # Open diagnosis panel first
        diagnose_btn.click()
        diagnosis_panel = browser.locator("#diagnosis-panel")
        assert "hidden" not in diagnosis_panel.get_attribute("class")
        
        # Open settings - should close diagnosis
        settings_btn.click()
        settings_panel = browser.locator("#settings-panel")
        assert "hidden" not in settings_panel.get_attribute("class")
        assert "hidden" in diagnosis_panel.get_attribute("class")
        
        # Open diagnosis - should close settings
        diagnose_btn.click()
        assert "hidden" in settings_panel.get_attribute("class")
        assert "hidden" not in diagnosis_panel.get_attribute("class")

    def test_settings_panel_has_form_content(self, browser):
        """Settings panel should contain the settings form elements."""
        settings_btn = browser.locator("#settings-wrap")
        settings_btn.click()
        
        panel = browser.locator("#settings-panel")
        assert panel.locator("#install-dirs-list").count() == 1
        assert panel.locator("#scan-interval").count() == 1
        assert panel.locator("#btn-save-settings").count() == 1


class TestShowAlertModal:
    """Tests for the showAlert modal dialog."""

    def test_show_alert_displays_modal(self, browser):
        """showAlert should display a modal with title and message."""
        browser.evaluate("""() => {
            showAlert('Test message', 'Test Title');
        }""")

        # Modal should be visible
        modal = browser.locator("#alert-modal")
        assert modal.is_visible()

        # Title should be set
        title = browser.locator("#alert-modal-title")
        assert title.text_content() == "Test Title"

        # Message should be set
        message = browser.locator("#alert-modal-message")
        assert message.text_content() == "Test message"

    def test_show_alert_has_only_ok_button(self, browser):
        """showAlert modal should have only an OK button, no cancel."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        ok_btn = browser.locator("#alert-modal-ok")
        assert ok_btn.is_visible()

        # Cancel button should not exist
        cancel_btn = browser.locator("#alert-modal-cancel")
        assert cancel_btn.count() == 0

    def test_show_alert_default_title(self, browser):
        """showAlert should use a default title when none provided."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        title = browser.locator("#alert-modal-title")
        text = title.text_content()
        assert text in ["Alert", "提示"]

    def test_show_alert_ok_button_closes_modal(self, browser):
        """Clicking OK button should close the alert modal."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        modal = browser.locator("#alert-modal")
        assert modal.is_visible()

        ok_btn = browser.locator("#alert-modal-ok")
        ok_btn.click()

        # Wait for animation
        browser.wait_for_timeout(300)
        assert not modal.is_visible()

    def test_show_alert_escape_key_closes_modal(self, browser):
        """Pressing Escape should close the alert modal."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        modal = browser.locator("#alert-modal")
        assert modal.is_visible()

        browser.keyboard.press("Escape")

        # Wait for animation
        browser.wait_for_timeout(300)
        assert not modal.is_visible()

    def test_show_alert_enter_key_closes_modal(self, browser):
        """Pressing Enter should close the alert modal."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        modal = browser.locator("#alert-modal")
        assert modal.is_visible()

        browser.keyboard.press("Enter")

        # Wait for animation
        browser.wait_for_timeout(300)
        assert not modal.is_visible()

    def test_show_alert_click_outside_closes_modal(self, browser):
        """Clicking outside the modal should close it."""
        browser.evaluate("""() => {
            showAlert('Test message');
        }""")

        modal = browser.locator("#alert-modal")
        assert modal.is_visible()

        # Click on the overlay background (outside the modal box)
        modal.click(position={"x": 10, "y": 10})

        # Wait for animation
        browser.wait_for_timeout(300)
        assert not modal.is_visible()

    def test_show_alert_returns_promise(self, browser):
        """showAlert should return a Promise that resolves when closed."""
        result = browser.evaluate("""() => {
            const promise = showAlert('Test message');
            return promise instanceof Promise;
        }""")

        assert result is True
