"""
Configuration module for visa appointment helper.
Centralized settings for URLs, selectors, logging, and notification channels.
Supports multiple visa types with automatic detection and configuration.
"""
import os
from pathlib import Path

# Root folder
ROOT_FOLDER = os.environ.get("ROOT_FOLDER", os.getcwd())
TARGET_FOLDER = os.path.join(ROOT_FOLDER, "target")
LOG_FOLDER = os.path.join(ROOT_FOLDER, "log")
LOG_FILE = os.path.join(LOG_FOLDER, "log.txt")

# Create necessary directories
Path(TARGET_FOLDER).mkdir(parents=True, exist_ok=True)
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)

# ============================================================================
# UNIVERSAL CONFIGURATION - One setting for all visa types
# ============================================================================

# Embassy Location (e.g., 'kiew', 'berlin', 'moscow')
EMBASSY_LOCATION = os.environ.get("EMBASSY_LOCATION", "kiew")

# Visa Type to monitor (options: 'schengen', 'work', 'study', 'family', 'residence')
# Set to 'auto' to monitor all available types
VISA_TYPE = os.environ.get("VISA_TYPE", "schengen")

# Base consulate URL (typically same for all visa types at an embassy)
CONSULATE_BASE_URL = os.environ.get("CONSULATE_BASE_URL", "https://vis.diplo.de/rktermin/frontend/")

# ============================================================================
# LEGACY CONFIGURATION - Override if needed for specific embassy
# These are auto-set based on VISA_TYPE, but can be overridden
# ============================================================================

# Consul URL Configuration
RESCHEDULING_BASE_URL = os.environ.get("RESCHEDULING_BASE_URL", "")
BOOKING_BASE_URL = os.environ.get("BOOKING_BASE_URL", "")
HOST = os.environ.get("HOST", "https://vis.diplo.de")

# Consulate Details - Auto-set based on VISA_TYPE or override here
CONSULATE_DETAILS = os.environ.get("CONSULATE_DETAILS", "")
LOCATION_CODE = os.environ.get("LOCATION_CODE", EMBASSY_LOCATION)
REALM_ID = os.environ.get("REALM_ID", "561")

# Category ID - varies by visa type and embassy
# For Kyiv: Schengen=1497, Work=1785, Study=1786, Family=1787, Residence=1788
CATEGORY_ID = os.environ.get("CATEGORY_ID", "1497")

RESCHEDULING_TOKEN = os.environ.get("RESCHEDULING_TOKEN", "")

# HTML Selectors
CAPTCHA_SELECTOR_MONTH = "appointment_captcha_month"
REBOOK_CAPTCHA_SELECTOR = "rebook_captcha"
CONTENT_DIV_ID = "content"
ARROW_LINK_CLASS = "arrow"

# Notification Settings
TELEGRAM_API_URL = os.environ.get("TELEGRAM_API_URL", "https://api.telegram.org/bot")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Captcha Solver Settings (DeathByCaptcha)
DBC_USERNAME = os.environ.get("DBC_USERNAME", "")
DBC_PASSWORD = os.environ.get("DBC_PASSWORD", "")
DBC_BINARY_PATH = os.environ.get("DBC_BINARY_PATH", "lib/deathbycaptcha")

# Date Filtering Logic - customize this for your needs
def is_acceptable_date(month: int, day: int) -> bool:
    """
    Determine if the available date should trigger a notification.
    Customize this logic according to your requirements.
    
    Args:
        month: Month as integer (1-12)
        day: Day as integer (1-31)
        
    Returns:
        True if date should trigger notification, False otherwise
    """
    # Example: March after 24th or April before 24th
    if month == 3 and day > 24:
        return True
    if month == 4 and day < 24:
        return True
    return False


# Logging Configuration
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
