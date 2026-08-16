# visa-appointment-helper

🎫 A German visa appointment automation tool that monitors visa portals, solves captchas, and sends notifications when appointments become available.

**📢 This codebase has been refactored for better maintainability and modularity. See [REFACTORING.md](REFACTORING.md) for details.**

---

## ✨ Features

- ✅ Automatically checks for available visa appointments
- ✅ Solves captchas via the 2Captcha API
- ✅ Sends notifications via Telegram when dates become available
- ✅ Can automatically book appointments (optional)
- ✅ Comprehensive logging and error handling
- ✅ Modular Python package architecture
- ✅ Centralized configuration management
- ✅ Type-hinted code for better IDE support

## 📋 Requirements

- Python 3.6 or higher
- `beautifulsoup4` for HTML parsing
- `requests` for the 2Captcha API
- 2Captcha account and API key (pay-as-you-go, ~$0.5-1 per 1000 captchas)
- Telegram bot token and chat ID
- German consulate visa portal access

## 🚀 Quick Start

### 1. Installation

```bash
# Clone/download the repository
cd visa-termin-master

# Run setup (installs dependencies, makes scripts executable)
chmod +x setup_refactored.sh
./setup_refactored.sh
```

### 2. Configuration

```bash
# Copy example configuration
cp setenv.example setenv

# Edit setenv with your values
# Required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, CAPTCHA_API_KEY
nano setenv
```

### 3. Run

```bash
# Simple check (no booking)
./run_refactored.sh

# With auto-booking enabled
export AUTO_BOOK=true
./run_refactored.sh

# Check logs
tail -f log/log.txt
```

## 🔧 Configuration

Create a `.setenv` file in the project root:

```bash
export ROOT_FOLDER="$(pwd)"
export CONSULATE_BASE_URL="https://vis.diplo.de/rktermin/frontend/"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export CAPTCHA_API_KEY="your_2captcha_api_key"
export CONSULATE_DETAILS="locationCode=kiew&realmId=561&categoryId=1497"
```

See [setenv.example](setenv.example) for all available options.

## 📚 Documentation

- **[REFACTORING.md](REFACTORING.md)** - Architecture improvements and new structure
- **[DEVELOPER.md](DEVELOPER.md)** - In-depth developer guide
- **[setenv.example](setenv.example)** - Configuration template with comments

## 🏗️ Project Structure

```
visa-termin-master/
├── lib/                      # Main Python package
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── utils.py             # Shared utilities
│   ├── extractors.py        # HTML extraction logic
│   ├── notifications.py     # Telegram notifications
│   └── appointment_handler.py # Main orchestrator
├── run_refactored.sh        # New entry point (recommended)
├── run.sh                   # Original script (legacy)
├── setenv                   # Configuration (not in repo)
├── setenv.example           # Configuration template
├── requirements.txt         # Python dependencies
└── log/                     # Log files
    └── log.txt
```

## 🔔 Notifications

### Telegram Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your chat ID by sending a message to your bot
3. Add token and chat ID to `.setenv`:

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="123456789"
```

## ⏰ Schedule with Cron

Check for appointments every 30 minutes during business hours:

```bash
# Add to crontab with: crontab -e
*/30 8-17 * * 1-5 cd /path/to/visa-termin-master && ./run_refactored.sh
```

## 🎯 Use as Python Module

```python
from lib.appointment_handler import AppointmentHandler

handler = AppointmentHandler("/path/to/project")
handler.run_full_workflow(auto_book=True)
```

## ⚙️ How It Works

1. **Fetch** - Downloads captcha page from consulate portal
2. **Solve** - Extracts the captcha image and solves it through the 2Captcha API
3. **Check** - Fetches available dates and checks against preferences
4. **Notify** - Sends Telegram notification if date is acceptable
5. **Book** (optional) - Automatically books the appointment

## 🛠️ Customization

### Change Date Filtering Logic

Edit `lib/config.py`:

```python
def is_acceptable_date(month: int, day: int) -> bool:
    # Example: June to August
    if 6 <= month <= 8:
        return True
    return False
```

### Add Email Notifications

See [DEVELOPER.md](DEVELOPER.md) for examples on extending the codebase.

## 🐛 Troubleshooting

### Check logs for errors
```bash
tail -f log/log.txt
grep ERROR log/log.txt
```

### Verify configuration
```bash
python3 -c "from lib import config; print(f'URL: {config.CONSULATE_BASE_URL}')"
```

### Test individual components
```bash
python3 lib/parse_response.py "$(pwd)"
python3 lib/extract_captcha.py "$(pwd)" captchapage.html appointment_captcha_month
```

## ⚠️ Important Notes

- ⚠️ **Test without auto-booking first** - Set `AUTO_BOOK=false` initially
- ⚠️ **Never commit `.setenv`** - Add to `.gitignore` if in git repo
- ⚠️ **Respect rate limits** - Don't check too frequently
- ⚠️ **Verify credentials** - Test the Telegram bot and check your 2Captcha balance

## 📝 License

See [LICENSE](LICENSE) file

---

## 📖 Additional Resources

- [German Visa Portal](https://vis.diplo.de/)
- [2Captcha API docs](https://2captcha.com/2captcha-api)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Version**: 2.0.0 (Refactored)
**Last Updated**: August 2026
