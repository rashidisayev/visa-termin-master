"""
Pytest configuration and shared fixtures for visa appointment tests.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        target_dir = Path(tmpdir) / "target"
        log_dir = Path(tmpdir) / "log"
        target_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        yield tmpdir


@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    original_env = os.environ.copy()
    
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            os.environ[key] = str(value) if value is not None else ""
    
    yield _set_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_legacy_portal_html():
    """Sample HTML from legacy RKTerMin portal."""
    return """
    <html>
    <head><title>Appointment</title></head>
    <body>
        <div id="content">
            <form id="appointment_captcha_month">
                <h4>Appointment date: 25.04.2024</h4>
                <h4>Appointment date: 26.04.2024</h4>
            </form>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_new_portal_html():
    """Sample HTML from new digital embassy portal."""
    return """
    <html>
    <head><title>Appointment</title></head>
    <body>
        <div class="appointment-slots">
            <div class="slot" data-date="2024-04-25" data-time="10:00">
                <span class="available">Available</span>
            </div>
            <div class="slot" data-date="2024-04-26" data-time="14:30">
                <span class="available">Available</span>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_doctolib_html():
    """Sample HTML from Doctolib-based portal."""
    return """
    <html>
    <head><title>Appointment</title></head>
    <body>
        <div class="doctolib-container">
            <div class="appointment-slot" data-date="2024-04-25">
                <button class="book-btn">Book 10:00</button>
            </div>
            <div class="appointment-slot" data-date="2024-04-26">
                <button class="book-btn">Book 14:30</button>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_visa_html_with_captcha():
    """Sample HTML page with appointment form and captcha."""
    return """
    <html>
    <head><title>Visa Appointment</title></head>
    <body>
        <div id="content">
            <form id="appointment_captcha_month">
                <img id="captcha_image" src="data:image/jpeg;base64,..." />
                <h4>Appointment date: 25.04.2024</h4>
                <input type="text" name="captcha_input" />
                <button type="submit">Book</button>
            </form>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_logger(mocker):
    """Mock logger for testing."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def mock_telegram_notification(mocker):
    """Mock Telegram notification."""
    return mocker.patch("lib.notifications.send_telegram_notification")


@pytest.fixture
def mock_dbc_solve(mocker):
    """Mock DeathByCaptcha solver."""
    return mocker.patch("lib.notifications.solve_captcha")


@pytest.fixture
def cleanup_config():
    """Clean up config imports."""
    # Remove config from modules cache before test
    import sys
    modules_to_remove = [m for m in sys.modules if m.startswith("lib")]
    for m in modules_to_remove:
        del sys.modules[m]
    
    yield
    
    # Clean up after test
    modules_to_remove = [m for m in sys.modules if m.startswith("lib")]
    for m in modules_to_remove:
        del sys.modules[m]
