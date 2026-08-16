# visa-appointment-helper

🎫 Monitors the German Foreign Office appointment portal (RK-Termin) for free visa
appointments, solves the captcha via 2Captcha, notifies you on Telegram — and can
book the slot automatically.

Works for **both Schengen (C) and national (D)** visas. Nothing is hardcoded to a
visa type: you point it at an embassy and category, and it drives the portal's own
forms.

---

## ⚖️ What this is for

This is a **personal help tool**. It was written for applicants who struggle to
fill in the appointment form correctly, or who cannot realistically sit and
refresh a portal for weeks hoping to catch one of very few free slots.

**It is not for sale, and commercial use is not permitted** — this is a licence
condition, not just a request: see [License](#-license). Do not use it to run a
paid booking service, resell appointments, or otherwise profit from access to
public appointment slots. Appointments at German missions are free of charge,
and slots taken to be sold on are slots denied to people who need them.

Please also:

- Book only appointments you genuinely intend to keep, using **real** details
- Cancel via the link in the confirmation mail if your plans change
- Run it on a sensible schedule — this is a public service, not a load target

This project is not affiliated with, endorsed by, or connected to the German
Federal Foreign Office or any German mission. It is provided as is, with no
warranty, and you are responsible for how you use it.

---

## ✨ What it does

- ✅ Checks any German embassy + visa category you configure
- ✅ Solves the portal captcha through the 2Captcha API, retrying on misreads
- ✅ Filters by a date window you set (not a hardcoded month)
- ✅ Sends a Telegram message when a matching date appears
- ✅ Books the appointment automatically, with a dry-run mode first
- ✅ Reports wrong captcha solutions back to 2Captcha for a refund

## 📋 Requirements

- Python 3.6+
- `beautifulsoup4`, `requests` (see [requirements.txt](requirements.txt))
- A **2Captcha** account with balance — roughly $1 per 1000 captchas, and one
  check costs one captcha
- Optional: a Telegram bot token and chat ID for notifications

## 🚀 Quick start

```bash
./setup.sh                 # installs dependencies, creates directories
cp setenv.example setenv   # then edit setenv (see below)
./run.sh                   # one check
tail -f log/log.txt        # watch what it does
```

`setenv` is gitignored — your API key and personal details stay out of the repo.

## 🔧 Configuration

Everything lives in `setenv`. The three IDs below are the only ones that select
your appointment; find them by clicking through the portal in a browser and
reading the final URL:

```
https://service2.diplo.de/rktermin/extern/choose_realmList.do?locationCode=XXXX
   → ...?locationCode=kual&realmId=502&categoryId=1761
```

### Which appointment

```bash
export LOCATION_CODE="kual"    # embassy code
export REALM_ID="502"          # visa section — differs between C and D
export CATEGORY_ID="1761"      # the specific category

# Or watch several at once, e.g. a C and a D category together:
# export VISA_TARGETS="kiew:561:1497,kiew:562:1785"
```

### Which dates

```bash
export EARLIEST_DATE=""        # DD.MM.YYYY, blank = today
export LATEST_DATE=""          # DD.MM.YYYY, blank = no limit
# export ACCEPTED_WEEKDAYS="0,1,2,3,4"   # 0=Mon .. 6=Sun
```

### Captcha solving

```bash
export CAPTCHA_API_KEY="your_2captcha_key"
export CAPTCHA_MAX_ATTEMPTS="3"   # solvers miss ~1 in 4; retry rather than lose a slot
```

### Notifications (optional)

```bash
export TELEGRAM_BOT_TOKEN="..."   # create with @BotFather
export TELEGRAM_CHAT_ID="..."
```

See [setenv.example](setenv.example) for every option with comments.

## 📅 Auto-booking

> **A successful booking is a real appointment at a real consulate.** There is no
> test mode on the portal. The mission blocks the applicant's passport number
> after a no-show, so only book appointments you intend to keep or cancel.

```bash
export APPLICANT_LASTNAME=""
export APPLICANT_FIRSTNAME=""
export APPLICANT_EMAIL=""      # confirmation + cancellation link arrive here
export APPLICANT_PASSPORT=""   # real number: printed on the confirmation, checked at the door

export AUTO_BOOK="true"
export BOOKING_DRY_RUN="true"  # ← leave this on until a dry run succeeds
```

**Always dry-run first.** With `BOOKING_DRY_RUN="true"` the tool walks the entire
live flow — opens the day, picks a slot, solves the booking captcha, builds the
exact POST body — then stops without submitting and logs precisely what it would
have sent. Read that log, confirm the name, passport, date and time, then set
`BOOKING_DRY_RUN="false"`.

If a dry run warns that some fields were left empty, that category asks for
something extra. Supply it:

```bash
export APPLICANT_EXTRA_FIELDS="birthDate=01.01.1990,phone=+4915112345678"
```

### The confirmation mail matters

The portal mails a confirmation that contains the **only** cancellation link:

```
cancellation_form.do?reference=kiew_11358600&token=<token>
```

Keep access to `APPLICANT_EMAIL`. Without that link you cannot cancel, and a
no-show blocks the passport number from booking again.

## ⚙️ How it works

1. **Fetch** — loads the month page for your category
2. **Solve** — extracts the captcha image and solves it via 2Captcha
3. **Submit** — posts back to the form's own action URL, preserving the session
4. **Check** — parses offered dates and applies your date window
5. **Notify** — sends a Telegram message
6. **Book** *(optional)* — follows the portal's links:
   `appointment_showDay` → `appointment_showForm` → submit

Steps 3 and 6 read the form's action, hidden fields and submit-button name off
the live page rather than hardcoding them. That is what lets the same code serve
different embassies and both visa types.

## ⏰ Run it on a schedule

Most embassies have no free slots most of the time, so this is meant to run
repeatedly:

```bash
# every 30 minutes during business hours
*/30 8-17 * * 1-5 cd /path/to/visa-termin-master && ./run.sh
```

Each run costs one captcha solve (a few hundredths of a cent). Don't run it every
few seconds — you'll burn balance and hammer a government service.

## 🎯 Use as a Python module

```python
from lib.appointment_handler import AppointmentHandler

handler = AppointmentHandler("/path/to/project")
handler.run_full_workflow(auto_book=True)
```

## 🏗️ Project structure

```
visa-termin-master/
├── lib/
│   ├── config.py              # all settings, read from the environment
│   ├── captcha_solver.py      # 2Captcha API client
│   ├── appointment_handler.py # workflow orchestration + booking
│   ├── extractors.py          # form/link discovery from live pages
│   ├── booking_process.py     # portal detection + date parsing
│   ├── utils.py               # HTML, logging, file helpers
│   ├── notifications.py       # Telegram
│   └── visa_types.py          # visa metadata (see Known limitations)
├── tests/                     # pytest suite
├── run.sh                     # entry point
├── setup.sh                   # dependency install
├── setenv.example             # configuration template
└── log/log.txt
```

## 🐛 Troubleshooting

```bash
tail -f log/log.txt
grep ERROR log/log.txt
```

**Check your resolved configuration:**
```bash
python3 -c "from lib import config; print(config.CONSULATE_BASE_URL, config.VISA_TARGETS)"
```

**Check your 2Captcha balance:**
```bash
python3 -c "from lib import captcha_solver; print(captcha_solver.get_solver().get_balance())"
```

**Run the tests:**
```bash
python3 -m pytest tests/ -q
```

| Symptom | Cause |
|---|---|
| `CAPTCHA_API_KEY is not set` | No key in `setenv` |
| `ERROR_ZERO_BALANCE` | Top up 2Captcha |
| `Portal rejected the captcha` repeatedly | Normal at ~1 in 4; raise `CAPTCHA_MAX_ATTEMPTS` |
| `403 Forbidden` | The portal blocks unknown clients; `USER_AGENT` must look like a browser |
| `No acceptable date found` | Usually genuine — most embassies have no free slots |
| `Form fields left empty: ...` | That category wants extra fields; use `APPLICANT_EXTRA_FIELDS` |

## ⚠️ Known limitations

- **Only the current month is checked.** The portal shows one month with
  prev/next arrows, and the tool does not follow them. If your embassy releases
  slots months ahead, they will not be seen even with a wide `LATEST_DATE`.
- **The booking POST has not been exercised against a live form**, because that
  requires an embassy with a genuinely free slot. Every step before the submit is
  verified live; the submit itself is covered by tests using fixtures shaped like
  the real pages. Dry-run mode exists for exactly this reason.
- **`visa_types.py` is not wired into anything.** `VISA_TYPE` and
  `EMBASSY_LOCATION` do not auto-configure category IDs — set
  `LOCATION_CODE`/`REALM_ID`/`CATEGORY_ID` explicitly.
- **Telegram send reports success from curl's exit code**, without reading the
  API response, so a revoked token can look like a delivered message.

## ⚠️ Before you use it

- Set `AUTO_BOOK=false` (or keep `BOOKING_DRY_RUN=true`) until you trust it
- Never commit `setenv` — it is gitignored, keep it that way
- Book only appointments you intend to keep, and cancel via the link if plans
  change. Deliberate misuse can get the applicant barred from the system.

## 📚 Documentation

- **[setenv.example](setenv.example)** — every setting, commented
- **[DEVELOPER.md](DEVELOPER.md)** — developer guide
- **[REFACTORING.md](REFACTORING.md)** — architecture notes

## 📖 Resources

- [German visa appointment portal](https://service2.diplo.de/rktermin/extern/)
- [2Captcha API](https://2captcha.com/2captcha-api)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 📝 License

**[PolyForm Noncommercial License 1.0.0](LICENSE)** — free to use, modify and
share for any **noncommercial** purpose. Commercial use is not permitted.

That includes running it as part of a paid service, reselling appointments
obtained with it, or charging for access to it or its output. Personal use,
hobby projects, research, education, and use by charities, public bodies and
similar organisations are all permitted.

This project began in 2019 as a fork of an MIT-licensed project; all of that
code has since been replaced. See [NOTICE](NOTICE) for the origin and the
upstream attribution.

---

**Last updated**: August 2026
