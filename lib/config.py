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

# Captcha Solver Settings (2Captcha)
# Get an API key at https://2captcha.com/enterpage
CAPTCHA_PROVIDER = os.environ.get("CAPTCHA_PROVIDER", "2captcha")
CAPTCHA_API_KEY = os.environ.get("CAPTCHA_API_KEY") or os.environ.get("TWOCAPTCHA_API_KEY", "")

# API endpoints (only change these if you use a 2Captcha-compatible service)
CAPTCHA_API_URL = os.environ.get("CAPTCHA_API_URL", "https://2captcha.com/in.php")
CAPTCHA_RESULT_URL = os.environ.get("CAPTCHA_RESULT_URL", "https://2captcha.com/res.php")

# Total seconds to wait for a solution before giving up
CAPTCHA_TIMEOUT = int(os.environ.get("CAPTCHA_TIMEOUT", "120"))
# Seconds between result polls, and per-HTTP-request timeout
CAPTCHA_POLL_INTERVAL = int(os.environ.get("CAPTCHA_POLL_INTERVAL", "5"))
CAPTCHA_HTTP_TIMEOUT = int(os.environ.get("CAPTCHA_HTTP_TIMEOUT", "30"))

# Captcha hints passed to the workers - the consulate captcha is a short
# alphanumeric string, so the defaults leave the length unconstrained.
# Case-sensitive solving is requested because it is never worse: a correctly
# cased answer is accepted whether or not the portal compares case.
CAPTCHA_CASE_SENSITIVE = os.environ.get("CAPTCHA_CASE_SENSITIVE", "true").lower() in ("true", "1", "yes")
CAPTCHA_NUMERIC = int(os.environ.get("CAPTCHA_NUMERIC", "0"))  # 0=any, 1=digits only, 2=letters only
CAPTCHA_MIN_LENGTH = int(os.environ.get("CAPTCHA_MIN_LENGTH", "0"))
CAPTCHA_MAX_LENGTH = int(os.environ.get("CAPTCHA_MAX_LENGTH", "0"))

# Report unusable solutions back to 2Captcha so they are refunded
CAPTCHA_REPORT_BAD = os.environ.get("CAPTCHA_REPORT_BAD", "true").lower() in ("true", "1", "yes")

# Pipe-separated phrases that mean the portal rejected the captcha solution.
# These are the exact strings the RK-Termin portal returns (verified live):
#   DE: "Der eingegebene Text ist falsch"
#   EN: "The entered text was wrong"
# Extend this if your embassy's portal words the error differently.
CAPTCHA_ERROR_MARKERS = [
    marker.strip().lower()
    for marker in os.environ.get(
        "CAPTCHA_ERROR_MARKERS",
        "eingegebene text ist falsch|entered text was wrong",
    ).split("|")
    if marker.strip()
]

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
