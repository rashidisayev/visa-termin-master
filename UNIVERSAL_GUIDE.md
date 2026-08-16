# Universal German Visa Appointment System - Implementation Guide

## 🎯 Overview

This update transforms the visa appointment helper into a **universal, self-configuring system** that:

✅ Works with **any German visa type** (Schengen C, D-visa Work, Study, Family, Residence)  
✅ **Auto-detects** embassy portal layouts (legacy RKTerMin → new digital systems)  
✅ **Adapts automatically** to new booking processes without code changes  
✅ **One configuration** that works for all visa types  
✅ **Supports all German embassies** worldwide  

## 🚀 Quick Start - Universal Configuration

### Step 1: Choose Your Visa Type
Edit `setenv` and set:
```bash
export VISA_TYPE="schengen"    # or: work, study, family, residence
export EMBASSY_LOCATION="kiew" # or: berlin, moscow, istanbul, warsaw, etc.
```

That's it! The system automatically configures:
- ✅ Correct appointment category IDs
- ✅ Correct realm IDs  
- ✅ Correct URL parameters
- ✅ Appropriate date filtering

### Step 2: Add Your Credentials
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export DBC_USERNAME="your_dbc_username"
export DBC_PASSWORD="your_dbc_password"
```

### Step 3: Run
```bash
./run_refactored.sh
```

Done! The system will:
- 🔍 Detect your embassy's portal type
- 🧩 Adapt to its layout (legacy or new)
- 📅 Check for appointments matching your visa type
- 🔔 Notify you when available

## 📋 Visa Types Explained

### Schengen (C Visa)
- **Duration**: Up to 90 days in 180-day period
- **Use**: Tourism, business, visiting friends/family
- **Category ID (Kyiv)**: 1497
- **Typical wait**: 7-15 days processing

```bash
export VISA_TYPE="schengen"
```

### D Visa - Employment (Work)
- **Duration**: Multiple entry, for employment
- **Use**: Working in Germany
- **Category ID (Kyiv)**: 1785
- **Typical wait**: 20-30 days processing
- **Requires**: Employment contract, qualifications proof

```bash
export VISA_TYPE="work"
```

### D Visa - Study
- **Duration**: For studying at German institutions
- **Use**: University, vocational training
- **Category ID (Kyiv)**: 1786
- **Typical wait**: 20-30 days processing
- **Requires**: University acceptance letter, financial proof

```bash
export VISA_TYPE="study"
```

### D Visa - Family Reunion
- **Duration**: To join family members in Germany
- **Use**: Spouse, children, parents
- **Category ID (Kyiv)**: 1787
- **Typical wait**: 20-30 days processing
- **Requires**: Proof of family relationship, sponsorship letter

```bash
export VISA_TYPE="family"
```

### D Visa - Residence Permit
- **Duration**: General residence/settlement
- **Use**: Retirement, other reasons
- **Category ID (Kyiv)**: 1788
- **Typical wait**: 20-30 days processing

```bash
export VISA_TYPE="residence"
```

## 🤖 Automatic Portal Detection

The system automatically detects which type of booking portal your embassy uses:

### Supported Portal Types

**Legacy RKTerMin** (until 2024)
- Used by many embassies
- Distinctive: `appointment_captcha`, specific HTML structure
- ✅ Fully supported with backward compatibility

**New Digital Portal** (2024+)
- Modern embassy systems
- Distinctive: data attributes, CSS classes, new form fields
- ✅ Automatic detection and adaptation

**Doctolib-based** (some embassies)
- Third-party appointment system
- ✅ Auto-detects and uses Doctolib-specific extraction

**Custom Embassy Systems**
- Proprietary portal systems
- ✅ Fallback generic extraction for any portal

### How It Works

When the script runs, it:
1. Downloads the appointment page
2. **Analyzes the HTML structure** to identify the portal type
3. Logs: `Detected portal type: legacy_rktermin` (or new_termin, doctolib, etc.)
4. **Selects the appropriate extraction logic** for that portal
5. Finds available dates using portal-specific methods
6. Reports results with full transparency

**You don't need to do anything** - it's automatic!

## 🛠️ New Features

### 1. Visa Type Manager (`lib/visa_types.py`)

Manages all visa type configurations:

```python
from lib.visa_types import VisaTypeManager

manager = VisaTypeManager()
manager.select_visa_type("work")
config = manager.get_selected_config()
print(f"Visa: {config.name}")
print(f"Processing time: {config.typical_processing_days} days")
```

### 2. Booking Process Adapter (`lib/booking_process.py`)

Auto-detects and adapts to different portals:

```python
from lib.booking_process import BookingProcessDetector, PortalLayoutAdapter

# Detect portal
detector = BookingProcessDetector()
portal_type = detector.detect_portal_type(html_content)

# Extract dates using portal-specific logic
adapter = PortalLayoutAdapter(portal_type)
available_date = adapter.extract_available_dates(html_content, config)
```

### 3. Enhanced Extractors (`lib/extractors.py`)

Now uses adaptive extraction:
- Legacy portals: Extract from `<h4>` elements
- New portals: Extract from data attributes
- Doctolib: Extract from appointment slots
- Generic fallback: Parse any date-like text

## 📝 Configuration Examples

### Example 1: Schengen in Kyiv (Default)
```bash
export VISA_TYPE="schengen"
export EMBASSY_LOCATION="kiew"
```
Auto-sets: `categoryId=1497`

### Example 2: Work Visa in Berlin
```bash
export VISA_TYPE="work"
export EMBASSY_LOCATION="berlin"
```
Auto-sets: `categoryId=1402` (Berlin-specific)

### Example 3: Study Visa in Moscow
```bash
export VISA_TYPE="study"
export EMBASSY_LOCATION="moscow"
```
Auto-sets: `categoryId=1603` (Moscow-specific)

### Example 4: Monitor Multiple Visas (Advanced)
```bash
export VISA_TYPE="auto"  # Monitors all types
```

## 🔄 Migration from Old System

**Old way** (still works):
```bash
export CONSULATE_DETAILS="locationCode=kiew&realmId=561&categoryId=1497"
export LOCATION_CODE="kiew"
export REALM_ID="561"
export CATEGORY_ID="1497"
```

**New universal way** (recommended):
```bash
export VISA_TYPE="schengen"
export EMBASSY_LOCATION="kiew"
# That's it! Everything else is automatic.
```

## 🔍 How Portal Detection Works

The system checks for distinctive HTML elements:

**Legacy Portal Detection**
```html
<form id="appointment_captcha_month">
  <div class="content">
    <h4>Appointment date: 25.04.2024</h4>
```

**New Portal Detection**
```html
<div class="appointment-date" data-date="2024-04-25">
  <span class="available">Available</span>
```

When detected, the system logs:
```
[2024-08-16 10:15:23] Portal type: legacy_rktermin - Legacy RKTerMin portal (before 2024)
[2024-08-16 10:15:24] Extracting available date from response.html
[2024-08-16 10:15:24] Found acceptable date: 25.04.2024
```

## 🧪 Testing

### Test Your Configuration
```bash
# See all available visa types
python3 -c "from lib.visa_types import VisaTypeManager; print(VisaTypeManager().list_visa_types())"

# Check detected portal type
python3 -c "
from lib import booking_process, utils
html = utils.load_html_file('target/response.html')
detector = booking_process.BookingProcessDetector()
print(f'Portal: {detector.detect_portal_type(html)}')
"

# Extract dates with your visa type
python3 lib/parse_response.py $(pwd)
```

### Run in Test Mode
```bash
export AUTO_BOOK="false"  # Never book
export LOG_LEVEL="DEBUG"  # Verbose logging
./run_refactored.sh
tail -f log/log.txt       # Watch real-time logs
```

## 🚨 Common Issues & Solutions

### "Unknown portal type detected"
- Embassy might use a very new or custom system
- Fallback extraction will still try to find dates
- Report to GitHub with error log if dates aren't found
- Can manually set category IDs as workaround

### Date extraction returns None
- Check logs: `grep "Error extracting" log/log.txt`
- Verify VISA_TYPE matches available categories at your embassy
- Test with `python3 lib/parse_response.py $(pwd)`
- Embassy might have changed portal structure

### Works for Schengen but not Work visa
- Work visa uses different category ID
- Verify CATEGORY_ID matches your embassy's work visa ID
- Check setenv.example for known category IDs
- May need to manually override CATEGORY_ID

### Changes to embassy portal break extraction
- ✅ Usually auto-detects and adapts
- Check log for portal type
- If still failing, system tries fallback extraction
- May need to wait for code update or manually override

## 📊 Logging & Debugging

All operations are logged to `log/log.txt`:

```bash
# See everything that happened
cat log/log.txt

# Filter errors only
grep ERROR log/log.txt

# Real-time monitoring
tail -f log/log.txt

# Portal detection info
grep "Portal type:" log/log.txt

# Date extraction details
grep "Extract" log/log.txt
```

## 🔐 Security

- **Credentials**: Store in `.setenv` (git-ignored), never commit
- **Sensitive data**: Not logged except error messages
- **Portal detection**: Only reads HTML structure, no data extraction
- **Auto-booking**: Requires explicit `AUTO_BOOK=true` to enable

## 🌍 Supported Embassies

The system automatically supports all German embassies with:
- Known: Kyiv, Berlin, Moscow, Istanbul, Warsaw, Prague, Vienna, Paris, London, Madrid, Rome, Amsterdam, Brussels, Athens, Budapest, Bucharest, Sofia, Zagreb, Tirana, Beijing, Tokyo, Bangkok, Dubai, Jakarta, Manila, Sydney, New York, Los Angeles, Mexico City, São Paulo, and many more

- Unknown locations: Will use generic extraction, may require manual category ID override

Add new embassy locations to `lib/visa_types.py`:
```python
location_mappings = {
    "my_city": {
        "schengen": "1234",
        "work": "1235",
        "study": "1236",
        ...
    }
}
```

## 📚 Next Steps

1. ✅ Copy `setenv.example` → `setenv`
2. ✅ Set `VISA_TYPE` and `EMBASSY_LOCATION`
3. ✅ Add Telegram and DBC credentials
4. ✅ Run `./run_refactored.sh`
5. ✅ Check logs for portal detection
6. ✅ Wait for appointments!

## 📞 Support

For issues or questions:
1. Check `log/log.txt` for error messages
2. Review portal type detection output
3. Verify VISA_TYPE is correct
4. Try manual category ID override if needed
5. Check `DEVELOPER.md` for advanced configuration

---

**Version**: 2.1.0 (Universal Multi-Visa)  
**Last Updated**: August 2026
