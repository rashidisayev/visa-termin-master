"""
Configuration module for visa appointment helper.
Centralized settings for URLs, selectors, logging, and notification channels.
Supports multiple visa types with automatic detection and configuration.
"""
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

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

# Visa Type label, for logging only. What actually selects the appointment is
# the LOCATION_CODE / REALM_ID / CATEGORY_ID triple below.
VISA_TYPE = os.environ.get("VISA_TYPE", "schengen")

# ============================================================================
# PORTAL CONFIGURATION
# ============================================================================

# Consul URL Configuration
# The live appointment system is service2.diplo.de/rktermin/extern/*.do -
# every step is reached from the month view, so only the base entry point
# and the host origin need to be configured.
PORTAL_BASE = os.environ.get("PORTAL_BASE", "https://service2.diplo.de/rktermin/extern")
CONSULATE_BASE_URL = os.environ.get(
    "CONSULATE_BASE_URL", f"{PORTAL_BASE}/appointment_showMonth.do"
)
HOST = os.environ.get("HOST", "https://service2.diplo.de/rktermin")

# Consulate Details - Auto-set based on VISA_TYPE or override here
LOCATION_CODE = os.environ.get("LOCATION_CODE", EMBASSY_LOCATION)
REALM_ID = os.environ.get("REALM_ID", "")

# Category ID - varies by visa type and embassy.
# Works for both Schengen (C) and national (D) visas: the portal uses the
# same booking flow for every category, only these IDs differ.
CATEGORY_ID = os.environ.get("CATEGORY_ID", "")

CONSULATE_DETAILS = os.environ.get(
    "CONSULATE_DETAILS",
    f"locationCode={LOCATION_CODE}&realmId={REALM_ID}&categoryId={CATEGORY_ID}",
)


def _parse_targets() -> list:
    """
    Build the list of appointment targets to monitor.

    VISA_TARGETS lets one run watch several categories at once - typically a
    C (Schengen) and a D (national) category, which usually sit under
    different realmIds:

        VISA_TARGETS="kiew:561:1497,kiew:562:1785"

    Falls back to the single LOCATION_CODE/REALM_ID/CATEGORY_ID triple.
    """
    raw = os.environ.get("VISA_TARGETS", "").strip()
    targets = []

    if raw:
        for entry in raw.split(","):
            parts = [p.strip() for p in entry.split(":")]
            if len(parts) != 3 or not all(parts):
                continue
            targets.append({
                "locationCode": parts[0], "realmId": parts[1], "categoryId": parts[2],
            })

    if not targets and LOCATION_CODE and REALM_ID and CATEGORY_ID:
        targets.append({
            "locationCode": LOCATION_CODE, "realmId": REALM_ID, "categoryId": CATEGORY_ID,
        })

    return targets


VISA_TARGETS = _parse_targets()

RESCHEDULING_TOKEN = os.environ.get("RESCHEDULING_TOKEN", "")

# ============================================================================
# Booking Settings
# ============================================================================

# Applicant details written into the actual appointment record.
# Required for auto-booking; the portal will not accept an empty form.
APPLICANT_LASTNAME = os.environ.get("APPLICANT_LASTNAME", "")
APPLICANT_FIRSTNAME = os.environ.get("APPLICANT_FIRSTNAME", "")
APPLICANT_EMAIL = os.environ.get("APPLICANT_EMAIL", "")

# The passport number is written into the booking and is what the mission
# blocks after a no-show, so it must be the real one. Confirmed present on
# the Kyiv national-visa form ("Is your passport number ... correct?").
APPLICANT_PASSPORT = os.environ.get("APPLICANT_PASSPORT", "")

# Some categories ask for extra fields. Anything the form wants that is not
# covered above can be supplied here as name=value pairs, comma separated:
#   APPLICANT_EXTRA_FIELDS="birthDate=01.01.1990,phone=+4915112345678"
APPLICANT_EXTRA_FIELDS = {
    key.strip(): value.strip()
    for key, _, value in (
        pair.partition("=") for pair in os.environ.get("APPLICANT_EXTRA_FIELDS", "").split(",")
    )
    if key.strip() and value.strip()
}

# Further details some embassies ask for. Baku's national visa form wants all
# of these, as fields named "fields[0].content", "fields1content" and so on.
APPLICANT_BIRTHDATE = os.environ.get("APPLICANT_BIRTHDATE", "")
APPLICANT_PHONE = os.environ.get("APPLICANT_PHONE", "")

# Purpose of journey, where the form offers a dropdown (this is how a "family
# reunion" D visa is selected - it is an option, not a separate category).
# Matched case-insensitively against the option text, so a fragment is enough.
APPLICANT_PURPOSE = os.environ.get("APPLICANT_PURPOSE", "")

# Fields are matched against BOTH the field name and its visible label, because
# embassies define custom fields with meaningless names ("fields[0].content")
# whose meaning appears only in the label. Keys are substrings; the first match
# wins, so put more specific terms first.
APPLICANT_FIELD_HINTS = {
    # name-based
    "lastname": APPLICANT_LASTNAME,
    "surname": APPLICANT_LASTNAME,
    "firstname": APPLICANT_FIRSTNAME,
    "givenname": APPLICANT_FIRSTNAME,
    "email": APPLICANT_EMAIL,
    "passport": APPLICANT_PASSPORT,
    "passno": APPLICANT_PASSPORT,
    # label-based, in the languages the portal actually uses
    "reisepass": APPLICANT_PASSPORT,
    "pasport": APPLICANT_PASSPORT,
    "geburtsdatum": APPLICANT_BIRTHDATE,
    "date of birth": APPLICANT_BIRTHDATE,
    "doğum": APPLICANT_BIRTHDATE,
    "telefon": APPLICANT_PHONE,
    "telephone": APPLICANT_PHONE,
    "nachname": APPLICANT_LASTNAME,
    "vorname": APPLICANT_FIRSTNAME,
    "e-mail": APPLICANT_EMAIL,
}

# Book automatically when an acceptable date is found
AUTO_BOOK = os.environ.get("AUTO_BOOK", "false").lower() in ("true", "1", "yes")

# Dry run: walk the entire booking flow against the live portal, solve the
# booking captcha, build the exact POST body - then stop without submitting.
# Leave this on until you have seen a dry run succeed.
BOOKING_DRY_RUN = os.environ.get("BOOKING_DRY_RUN", "true").lower() in ("true", "1", "yes")

# The portal rejects unknown clients with 403, so identify as a browser
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)

# HTML Selectors
CAPTCHA_SELECTOR_MONTH = "appointment_captcha_month"
REBOOK_CAPTCHA_SELECTOR = "rebook_captcha"

# Struts dispatches on the submit button's name, which must be POSTed
SHOW_MONTH_ACTION = "action:appointment_showMonth"
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

# Solvers misread these captchas a fair fraction of the time (measured around
# 1 in 4 against the live portal). A single miss must not cost a free slot, so
# retry with a fresh captcha before giving up.
CAPTCHA_MAX_ATTEMPTS = int(os.environ.get("CAPTCHA_MAX_ATTEMPTS", "3"))

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

# ============================================================================
# Date Filtering
# ============================================================================

# Accept any appointment inside this window, as DD.MM.YYYY.
# EARLIEST defaults to today, LATEST to "no upper bound".
EARLIEST_DATE = os.environ.get("EARLIEST_DATE", "").strip()
LATEST_DATE = os.environ.get("LATEST_DATE", "").strip()

# Optional: only accept these weekdays (0=Monday .. 6=Sunday), e.g. "0,1,2"
ACCEPTED_WEEKDAYS = [
    int(d) for d in os.environ.get("ACCEPTED_WEEKDAYS", "").split(",") if d.strip().isdigit()
]


def _parse_date(value: str) -> Optional[date]:
    """Parse a DD.MM.YYYY string, returning None if it is empty or malformed."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        return None


def is_acceptable_date(month: int, day: int, year: Optional[int] = None) -> bool:
    """
    Decide whether an offered appointment date should be taken.

    Driven entirely by EARLIEST_DATE / LATEST_DATE / ACCEPTED_WEEKDAYS so the
    same code works for Schengen (C) and national (D) appointments without
    editing this file.

    Args:
        month: Month as integer (1-12)
        day: Day as integer (1-31)
        year: Four-digit year. Required for a correct comparison; when it is
            omitted the current year is assumed, which is why callers should
            always pass it.

    Returns:
        True if the date falls inside the configured window
    """
    try:
        candidate = date(year or date.today().year, month, day)
    except ValueError:
        return False

    earliest = _parse_date(EARLIEST_DATE) or date.today()
    if candidate < earliest:
        return False

    latest = _parse_date(LATEST_DATE)
    if latest and candidate > latest:
        return False

    if ACCEPTED_WEEKDAYS and candidate.weekday() not in ACCEPTED_WEEKDAYS:
        return False

    return True


# Logging Configuration
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
