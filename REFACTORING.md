# Refactoring Summary

This codebase has been refactored from a monolithic shell script with scattered Python modules into a well-organized, modular Python package with the following improvements:

## 🏗️ New Structure

### Python Package: `lib/`

```
lib/
├── __init__.py                  # Package initialization
├── config.py                    # Centralized configuration management
├── utils.py                     # Shared utility functions (logging, HTML parsing, file I/O)
├── extractors.py               # HTML extraction logic (consolidated from 4 scripts)
├── notifications.py            # Telegram notification handling
├── appointment_handler.py       # Main orchestration logic
├── extract_captcha.py          # CLI wrapper (legacy)
├── extract_booking_time.py     # CLI wrapper (legacy)
├── extract_resch_appt_url.py   # CLI wrapper (legacy)
├── parse_response.py           # CLI wrapper (legacy)
└── deathbycaptcha/             # Captcha solver binary
```

### Shell Scripts

- **`run_refactored.sh`** - New simplified entry point (delegates to Python)
- **`run.sh`** - Original script (kept for backward compatibility)

## ✨ Key Improvements

### 1. **Configuration Management** (`config.py`)
- ✅ Centralized configuration from environment variables
- ✅ All hardcoded URLs, selectors, and credentials now configurable
- ✅ Custom date filtering logic in one place
- ✅ Directories automatically created on module load

### 2. **Utilities Module** (`utils.py`)
- ✅ Unified logging system (file + console)
- ✅ HTML file loading and parsing
- ✅ File I/O operations with error handling
- ✅ Base64 image extraction
- ✅ Type hints for better IDE support
- ✅ Proper error handling and logging

### 3. **Extractors Module** (`extractors.py`)
- ✅ Consolidated HTML extraction logic from 4 separate scripts
- ✅ Consistent error handling and logging
- ✅ Reusable functions instead of one-off scripts
- ✅ Better code maintainability
- ✅ Clear function documentation

### 4. **Notifications Module** (`notifications.py`)
- ✅ Centralized Telegram notifications
- ✅ Different notification types for different scenarios
- ✅ Graceful handling of missing credentials
- ✅ Formatted, emoji-enhanced messages

### 5. **Appointment Handler** (`appointment_handler.py`)
- ✅ Object-oriented approach with `AppointmentHandler` class
- ✅ Modular workflow steps (fetch → solve → check → book)
- ✅ Full error handling and logging throughout
- ✅ Can be imported as a module or run as CLI
- ✅ Supports optional auto-booking mode

### 6. **Shell Script Improvements** (`run_refactored.sh`)
- ✅ Much simpler and more readable (~60 lines vs ~100+ original)
- ✅ Proper error handling with trap
- ✅ Clear logging with timestamps
- ✅ Configuration loading and validation
- ✅ Environment variable export for Python module

## 🔧 Usage

### New Workflow (Recommended)

1. **Update `.setenv` file** with your configuration:
   ```bash
   export ROOT_FOLDER="/path/to/visa-termin-master"
   export CONSULATE_BASE_URL="https://vis.diplo.de/rktermin/frontend/"
   export CONSULATE_DETAILS="locationCode=kiew&realmId=561&categoryId=1497"
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   export DBC_USERNAME="your_dbc_username"
   export DBC_PASSWORD="your_dbc_password"
   # ... other settings
   ```

2. **Run the refactored script**:
   ```bash
   chmod +x run_refactored.sh
   ./run_refactored.sh
   
   # With auto-booking enabled:
   export AUTO_BOOK=true
   ./run_refactored.sh
   ```

3. **Check logs**:
   ```bash
   tail -f log/log.txt
   ```

### Using as Python Module

```python
from lib.appointment_handler import AppointmentHandler

# Create handler
handler = AppointmentHandler(root_folder="/path/to/project")

# Run workflow
handler.run_full_workflow(auto_book=True)
```

## 📝 Configuration Examples

### `setenv` File Template

```bash
#!/bin/bash

# Root folder
export ROOT_FOLDER="$(pwd)"

# Consulate URLs and Details
export CONSULATE_BASE_URL="https://vis.diplo.de/rktermin/frontend/"
export RESCHEDULING_BASE_URL="https://vis.diplo.de/rktermin/frontend/account/"
export BOOKING_BASE_URL="https://vis.diplo.de/rktermin/frontend/account/"
export HOST="https://vis.diplo.de"
export CONSULATE_DETAILS="locationCode=kiew&realmId=561&categoryId=1497"
export LOCATION_CODE="kiew"
export REALM_ID="561"
export CATEGORY_ID="1497"
export RESCHEDULING_TOKEN="your_token"

# Telegram Notifications
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# DeathByCaptcha Credentials
export DBC_USERNAME="your_username"
export DBC_PASSWORD="your_password"

# Auto-booking (optional)
export AUTO_BOOK="false"
```

## 🧪 Testing Individual Components

```bash
# Test configuration loading
python3 -c "from lib import config; print(config.CONSULATE_BASE_URL)"

# Test extractor functions
python3 -c "from lib.extractors import extract_available_date; print(extract_available_date('/path/to/root'))"

# Test notification
python3 -c "from lib.notifications import send_telegram_notification; send_telegram_notification('Test message')"
```

## 🔄 Migration from Old Scripts

The old individual Python scripts (`extract_captcha.py`, etc.) have been updated to act as CLI wrappers around the new modules:

- They maintain backward compatibility
- They now use the refactored modules internally
- They provide consistent logging
- They have better error handling

You can still call them individually:
```bash
python3 lib/extract_captcha.py /path/to/root captchapage.html appointment_captcha_month
python3 lib/parse_response.py /path/to/root
```

## 🐛 Improvements in Code Quality

### Before
- Mixed shell and Python logic
- Hardcoded URLs and selectors throughout
- No centralized logging
- Duplicated HTML parsing code
- Poor error handling
- Difficult to test

### After
- Clean separation of concerns
- Centralized configuration
- Unified logging system
- Reusable utility functions
- Comprehensive error handling
- Easily testable modules
- Type hints for IDE support
- Better documentation

## 📦 Dependencies

- `beautifulsoup4` - HTML parsing
- Python 3.6+ - For type hints and f-strings

Install with:
```bash
pip3 install -r requirements.txt
```

## 🚀 Next Steps

1. **Copy** `setenv.example` to `setenv` and update with your values
2. **Run** `chmod +x run_refactored.sh`
3. **Test** with `./run_refactored.sh` (will only check, not book)
4. **Set** `AUTO_BOOK=true` when ready to enable auto-booking
5. **Schedule** with cron for automated checks

## 📋 Cron Example

```bash
# Check every 30 minutes during business hours
*/30 8-17 * * 1-5 cd /path/to/visa-termin-master && ./run_refactored.sh
```

## 🎯 Future Enhancements

- Unit tests for all modules
- Database logging for historical data
- Web dashboard for monitoring
- Multiple appointment date preferences
- Email notifications in addition to Telegram
- Better error recovery and retry logic
- Configuration validation tool
