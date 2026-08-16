# Developer Guide - Refactored Visa Appointment Helper

## Project Overview

This project is a German visa appointment automation tool that:
1. Monitors German consulate visa portals for available appointments
2. Solves captchas automatically using DeathByCaptcha service
3. Sends notifications via Telegram when appointments become available
4. Can automatically book appointments (optional)

## Architecture

### Design Principles

- **Separation of Concerns**: Each module has a single responsibility
- **Configuration as Code**: All settings externalized to `config.py`
- **Logging First**: Comprehensive logging for debugging and monitoring
- **Type Hints**: Modern Python with type annotations
- **Error Handling**: Graceful error handling with informative messages
- **Modularity**: Reusable components that can be imported and used independently

### Module Responsibilities

```
┌─────────────────────────────────────────────────┐
│          run_refactored.sh (Orchestrator)       │
│        - Loads configuration                    │
│        - Handles environment setup              │
│        - Delegates to Python workflow           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│    appointment_handler.py (Application Logic)   │
│        - Orchestrates full workflow             │
│        - Calls sub-modules in correct order     │
│        - Handles error recovery                 │
└──────────────┬────────────────┬─────────────────┘
               │                │
    ┌──────────▼────┐    ┌──────▼──────────┐
    │ extractors.py │    │notifications.py │
    │ - Extract     │    │ - Send alerts   │
    │   dates       │    │ - Format msgs   │
    │ - Extract     │    └─────────────────┘
    │   URLs        │
    │ - Extract     │
    │   times       │
    └──────────────┘
               │
    ┌──────────▼──────────┐
    │    utils.py         │
    │ - HTML parsing      │
    │ - File I/O          │
    │ - Logging           │
    │ - Error handling    │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  config.py          │
    │ - All settings      │
    │ - Constants         │
    │ - Validation logic  │
    └─────────────────────┘
```

## Module Deep Dives

### config.py
**Purpose**: Centralized configuration management

**Key Features**:
- Loads all settings from environment variables
- Auto-creates necessary directories
- Contains date filtering logic (customizable)
- Provides constants for selectors and URLs

**Usage**:
```python
from lib import config
print(config.CONSULATE_BASE_URL)
print(config.TELEGRAM_BOT_TOKEN)
```

**Customization**:
```python
# Edit is_acceptable_date() to customize date filtering
def is_acceptable_date(month: int, day: int) -> bool:
    if month == 3 and day > 24:  # March after 24th
        return True
    if month == 4 and day < 24:  # April before 24th
        return True
    return False
```

### utils.py
**Purpose**: Shared utility functions

**Key Components**:
- `setup_logger()` - Unified logging to file and console
- `load_html_file()` - Parse HTML with error handling
- `save_file()` - Write files with directory creation
- `extract_base64_image()` - Decode captcha images
- `find_element()` / `find_all_elements()` - BeautifulSoup wrappers

**Design Pattern**: All functions include error handling and logging

**Example**:
```python
from lib import utils

logger = utils.setup_logger()
html = utils.load_html_file("/path/to/file.html")
logger.info("Processing HTML")
```

### extractors.py
**Purpose**: HTML extraction logic (formerly 4 separate scripts)

**Functions**:
- `extract_captcha_image()` - Save captcha from base64 in HTML
- `extract_booking_time()` - Get appointment time from page
- `extract_reschedule_url()` - Find booking URL
- `extract_available_date()` - Check for acceptable dates

**Design**: Each function is atomic and testable

**Example**:
```python
from lib import extractors

date = extractors.extract_available_date("/root/folder")
if date:
    print(f"Available: {date}")
```

### notifications.py
**Purpose**: Send user notifications

**Functions**:
- `send_telegram_notification()` - Core Telegram API call
- `notify_available_date()` - Format date availability message
- `notify_appointment_booked()` - Confirm booking
- `notify_error()` - Alert on errors

**Features**:
- Graceful handling of missing credentials
- Emoji-enhanced messages
- Consistent message formatting

### appointment_handler.py
**Purpose**: Main application orchestrator

**Class**: `AppointmentHandler`

**Methods**:
- `__init__(root_folder)` - Initialize handler
- `fetch_captcha_page()` - Download initial page
- `solve_captcha()` - Extract and solve captcha
- `fetch_response_page()` - Get dates page
- `check_and_notify_available_date()` - Parse and alert
- `book_appointment()` - Automatic booking workflow
- `run_full_workflow()` - Complete process

**Usage as Module**:
```python
from lib.appointment_handler import AppointmentHandler

handler = AppointmentHandler("/path/to/root")
handler.run_full_workflow(auto_book=True)
```

## Adding New Features

### Example: Add Email Notifications

1. **Create new module** `lib/email_notifications.py`:
```python
import smtplib
from email.mime.text import MIMEText
from . import config, utils

def send_email(recipient, subject, body):
    logger = utils.setup_logger()
    try:
        # Implementation here
        logger.info(f"Email sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False
```

2. **Update config.py** with email settings:
```python
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
```

3. **Call from appointment_handler.py**:
```python
from lib import email_notifications

if available_date:
    email_notifications.send_email(
        "user@example.com",
        "Visa Appointment Available",
        f"Date: {available_date}"
    )
```

### Example: Add Date Range Preference

Edit `config.py`:
```python
PREFERRED_DATES = {
    "start": "01.03.2024",
    "end": "30.04.2024"
}

def is_acceptable_date(month: int, day: int) -> bool:
    # Parse preferred dates and check range
    # Implementation here
    return date_in_range
```

## Testing

### Unit Test Example

Create `test_extractors.py`:
```python
import unittest
from lib import extractors

class TestExtractors(unittest.TestCase):
    def test_extract_available_date(self):
        # Create mock HTML
        # Test extraction logic
        pass

if __name__ == '__main__':
    unittest.main()
```

### Manual Testing

```bash
# Test configuration loading
python3 -c "from lib import config; print(config.CONSULATE_BASE_URL)"

# Test logger
python3 -c "from lib import utils; logger = utils.setup_logger(); logger.info('Test')"

# Test notifications
python3 -c "from lib.notifications import notify_available_date; notify_available_date('01.05.2024')"
```

## Debugging

### Enable Debug Logging

The logger automatically writes to both console and file:
- **Console**: INFO and above
- **File** (`log/log.txt`): DEBUG and above

### Common Issues

**Issue**: "Form with id 'X' not found"
- Check if HTML selector IDs changed in consulate website
- Update `config.py` selector constants

**Issue**: "Captcha solution file is empty"
- Check DeathByCaptcha credentials
- Verify captcha.jpg was extracted correctly

**Issue**: "Telegram notification failed"
- Verify bot token and chat ID in `.setenv`
- Check internet connection

### Debug Steps

1. **Check logs**:
   ```bash
   tail -f log/log.txt
   grep ERROR log/log.txt
   ```

2. **Test individual components**:
   ```bash
   python3 lib/extract_captcha.py /path/to/root captchapage.html appointment_captcha_month
   python3 lib/parse_response.py /path/to/root
   ```

3. **Inspect HTML files**:
   ```bash
   open target/captchapage.html
   open target/response.html
   ```

## Performance Considerations

- **Network delays**: Script waits 3-5 seconds for pages to load
- **Captcha solving**: Typically 30-60 seconds with DeathByCaptcha
- **Rate limiting**: Consulate may rate-limit requests
- **Logging overhead**: File logging adds minimal overhead

## Security Notes

⚠️ **Never commit `.setenv` file with real credentials**

- Store credentials in environment variables or secure vaults
- Use `.gitignore` to exclude sensitive files
- Rotate credentials regularly
- Don't share logs containing sensitive data

## Version History

### v2.0.0 (Current)
- Complete refactoring into modular architecture
- Centralized configuration management
- Improved logging and error handling
- Type hints throughout
- Better separation of concerns
- Python module imports possible

### v1.0 (Original)
- Monolithic shell script with embedded Python
- Hardcoded configuration values
- Mixed shell and Python logic

## Contributing

When adding features:
1. Follow the module structure
2. Add type hints to functions
3. Include comprehensive error handling
4. Add logging at key points
5. Update this documentation
6. Test both success and failure paths

## Resources

- [DeathByCaptcha API](https://deathbycaptcha.com/api)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

## Support

For issues or questions:
1. Check `log/log.txt` for error messages
2. Review this documentation
3. Test individual modules
4. Check consulate website for changes
