"""
Tests for the fresh-booking flow.

The portal only exposes a booking form when a slot is actually free, which is
rare, so these tests drive the flow with fixtures shaped like the real pages
(same <captcha> markup, same ;jsessionid action, same Struts submit names).
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import config, extractors, utils  # noqa: E402

JSESSION = "ABC123DEF456"
BASE = "https://service2.diplo.de/rktermin/extern"

MONTH_PAGE = f"""
<html><body><div id="content">
  <a class="arrow" href="extern/appointment_showDay.do?locationCode=test&realmId=1&categoryId=2&dateStr=03.09.2026&openingPeriodId=99">03.09.2026</a>
  <a class="arrow" href="extern/appointment_showDay.do?locationCode=test&realmId=1&categoryId=2&dateStr=17.12.2026&openingPeriodId=98">17.12.2026</a>
</div></body></html>
"""

DAY_PAGE = f"""
<html><body><div id="content">
  <a href="extern/appointment_showForm.do?locationCode=test&realmId=1&categoryId=2&dateStr=03.09.2026&timeStr=09%3A15">09:15</a>
  <a href="extern/appointment_showForm.do?locationCode=test&realmId=1&categoryId=2&dateStr=03.09.2026&timeStr=10%3A45">10:45</a>
</div></body></html>
"""

# Mirrors the live form: captcha inside <captcha><div style="...">, action
# carrying ;jsessionid, and Struts action: submit buttons.
BOOKING_FORM = f"""
<html><body><div id="content"><div><fieldset>
<div>ignored</div><div>03.09.2026 09:15</div>
<form id="appointment_newAppointmentForm"
      action="/rktermin/extern/appointment_showForm.do;jsessionid={JSESSION}" method="post">
  <div><captcha><div style="background:white url('data:image/png;base64,{'QUJD' * 4}') no-repeat scroll left top;width:350px;height:50px;"></div></captcha></div>
  <input type="text" name="captchaText" value=""/>
  <input type="hidden" name="locationCode" value="test"/>
  <input type="hidden" name="realmId" value="1"/>
  <input type="hidden" name="categoryId" value="2"/>
  <input type="hidden" name="dateStr" value="03.09.2026"/>
  <input type="hidden" name="openingPeriodId" value="99"/>
  <input type="text" name="lastname" value=""/>
  <input type="text" name="firstname" value=""/>
  <input type="text" name="email" value=""/>
  <input type="text" name="passportNumber" value=""/>
  <input type="submit" name="action:appointment_refreshCaptcha" value="Neues Bild laden"/>
  <input type="submit" name="action:appointment_addAppointment" value="Termin buchen"/>
  <input type="submit" name="action:choose_category" value="Abbrechen"/>
</form>
</fieldset></div></div></body></html>
"""


from contextlib import contextmanager


@contextmanager
def applicant(**overrides):
    """Patch the applicant details the booking requires."""
    values = {
        "APPLICANT_LASTNAME": "Isayev",
        "APPLICANT_FIRSTNAME": "Rashid",
        "APPLICANT_EMAIL": "r@example.com",
        "APPLICANT_PASSPORT": "C01548134",
    }
    values.update(overrides)
    patches = [patch.object(config, k, v) for k, v in values.items()]
    hints = dict(config.APPLICANT_FIELD_HINTS)
    hints.update({
        "lastname": values["APPLICANT_LASTNAME"], "surname": values["APPLICANT_LASTNAME"],
        "firstname": values["APPLICANT_FIRSTNAME"], "givenname": values["APPLICANT_FIRSTNAME"],
        "email": values["APPLICANT_EMAIL"],
        "passport": values["APPLICANT_PASSPORT"], "passno": values["APPLICANT_PASSPORT"],
    })
    patches.append(patch.object(config, "APPLICANT_FIELD_HINTS", hints))
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in patches:
            p.stop()


@pytest.fixture
def booking_config():
    """Applicant details present, as they must be for any booking."""
    with applicant():
        yield


@pytest.fixture
def target(tmp_path):
    """A root folder with target/ populated like a real run."""
    t = tmp_path / "target"
    t.mkdir()
    (t / "response.html").write_text(MONTH_PAGE, encoding="utf-8")
    (t / "appointmentschedulingpage.html").write_text(DAY_PAGE, encoding="utf-8")
    (t / "bookfinalappt.html").write_text(BOOKING_FORM, encoding="utf-8")
    return tmp_path


class TestFormDiscovery:
    def test_finds_captcha_form_without_knowing_its_id(self, target):
        ctx = extractors.extract_form_context(str(target), "bookfinalappt.html")
        assert ctx is not None
        assert ctx["action"] == f"{BASE}/appointment_showForm.do;jsessionid={JSESSION}"

    def test_carries_every_hidden_field(self, target):
        fields = extractors.extract_form_context(str(target), "bookfinalappt.html")["fields"]
        for name in ("locationCode", "realmId", "categoryId", "dateStr", "openingPeriodId"):
            assert name in fields
        # submit buttons must not leak into the field set
        assert not any(k.startswith("action:") for k in fields)

    def test_picks_the_booking_submit_not_cancel_or_refresh(self, target):
        submits = extractors.extract_form_context(str(target), "bookfinalappt.html")["submits"]
        assert extractors.pick_submit_action(submits) == (
            "action:appointment_addAppointment", "Termin buchen",
        )

    def test_pick_submit_handles_rebooking_flow(self):
        assert extractors.pick_submit_action([
            ("action:appointment_refreshCaptcha", "x"),
            ("action:appointment_rebookAppointment", "Submit"),
        ]) == ("action:appointment_rebookAppointment", "Submit")

    def test_pick_submit_returns_none_when_only_cancels(self):
        assert extractors.pick_submit_action([("action:choose_category", "Abbrechen")]) is None


class TestLinkFollowing:
    def test_finds_day_links(self, target):
        links = extractors.extract_links(str(target), "response.html", "appointment_showDay.do")
        assert len(links) == 2
        assert all(l.startswith(f"{BASE}/appointment_showDay.do") for l in links)

    def test_finds_slot_links(self, target):
        links = extractors.extract_links(str(target), "appointmentschedulingpage.html", "appointment_showForm.do")
        assert len(links) == 2


class TestDateWindow:
    def test_rejects_dates_before_earliest(self):
        with patch.object(config, "EARLIEST_DATE", "01.09.2026"), \
             patch.object(config, "LATEST_DATE", ""), patch.object(config, "ACCEPTED_WEEKDAYS", []):
            assert config.is_acceptable_date(8, 15, 2026) is False
            assert config.is_acceptable_date(9, 3, 2026) is True

    def test_rejects_dates_after_latest(self):
        with patch.object(config, "EARLIEST_DATE", "01.01.2026"), \
             patch.object(config, "LATEST_DATE", "31.10.2026"), patch.object(config, "ACCEPTED_WEEKDAYS", []):
            assert config.is_acceptable_date(12, 17, 2026) is False

    def test_year_is_not_ignored(self):
        """The old implementation matched on month/day alone."""
        with patch.object(config, "EARLIEST_DATE", "01.01.2026"), \
             patch.object(config, "LATEST_DATE", "31.12.2026"), patch.object(config, "ACCEPTED_WEEKDAYS", []):
            assert config.is_acceptable_date(9, 3, 2026) is True
            assert config.is_acceptable_date(9, 3, 2028) is False

    def test_weekday_filter(self):
        # 03.09.2026 is a Thursday (weekday 3)
        with patch.object(config, "EARLIEST_DATE", "01.01.2026"), \
             patch.object(config, "LATEST_DATE", ""), patch.object(config, "ACCEPTED_WEEKDAYS", [0, 1]):
            assert config.is_acceptable_date(9, 3, 2026) is False
        with patch.object(config, "EARLIEST_DATE", "01.01.2026"), \
             patch.object(config, "LATEST_DATE", ""), patch.object(config, "ACCEPTED_WEEKDAYS", [3]):
            assert config.is_acceptable_date(9, 3, 2026) is True

    def test_invalid_date_is_rejected(self):
        assert config.is_acceptable_date(2, 31, 2026) is False


class TestTargets:
    def test_parses_c_and_d_targets(self):
        import os
        with patch.dict(os.environ, {"VISA_TARGETS": "kiew:561:1497,kiew:562:1785"}):
            targets = config._parse_targets()
        assert targets == [
            {"locationCode": "kiew", "realmId": "561", "categoryId": "1497"},
            {"locationCode": "kiew", "realmId": "562", "categoryId": "1785"},
        ]

    def test_ignores_malformed_entries(self):
        import os
        with patch.dict(os.environ, {"VISA_TARGETS": "kiew:561,bad,kual:502:1761"}):
            targets = config._parse_targets()
        assert targets == [{"locationCode": "kual", "realmId": "502", "categoryId": "1761"}]


class TestBookingFlow:
    def _handler(self, target):
        from lib.appointment_handler import AppointmentHandler
        return AppointmentHandler(root_folder=str(target))

    def test_dry_run_does_not_submit(self, target, booking_config):
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", True), \
             patch.object(h, "_curl", return_value=True) as curl, \
             patch.object(h, "solve_captcha", return_value="ab12cd"):
            assert h.book_appointment("03.09.2026") is True

        # two GETs (day page, slot page) and never a POST
        assert curl.call_count == 2
        assert all(c.kwargs.get("post_fields") is None for c in curl.call_args_list)

    def test_real_booking_posts_expected_payload(self, target, booking_config):
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", False), \
             patch.object(h, "_curl", return_value=True) as curl, \
             patch.object(h, "solve_captcha", return_value="ab12cd"), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", return_value=False), \
             patch("lib.appointment_handler.notifications.notify_appointment_booked"):
            assert h.book_appointment("03.09.2026") is True

        post = curl.call_args_list[-1]
        url, fields = post.args[0], post.kwargs["post_fields"]
        assert f";jsessionid={JSESSION}" in url          # session preserved
        assert fields["action:appointment_addAppointment"] == "Termin buchen"
        assert fields["captchaText"] == "ab12cd"
        assert fields["lastname"] == "Isayev"
        assert fields["email"] == "r@example.com"
        assert fields["dateStr"] == "03.09.2026"

    def test_fills_passport_number(self, target, booking_config):
        """The Kyiv confirmation mail shows the form records a passport number."""
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", False), \
             patch.object(h, "_curl", return_value=True) as curl, \
             patch.object(h, "solve_captcha", return_value="ab12cd"), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", return_value=False), \
             patch("lib.appointment_handler.notifications.notify_appointment_booked"):
            assert h.book_appointment("03.09.2026") is True

        fields = curl.call_args_list[-1].kwargs["post_fields"]
        assert fields["passportNumber"] == "C01548134"
        assert fields["firstname"] == "Rashid"

    def test_extra_fields_cover_unknown_form_inputs(self, target, booking_config):
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", False), \
             patch.object(config, "APPLICANT_EXTRA_FIELDS", {"passportNumber": "OVERRIDE1"}), \
             patch.object(h, "_curl", return_value=True) as curl, \
             patch.object(h, "solve_captcha", return_value="ab12cd"), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", return_value=False), \
             patch("lib.appointment_handler.notifications.notify_appointment_booked"):
            assert h.book_appointment("03.09.2026") is True

        assert curl.call_args_list[-1].kwargs["post_fields"]["passportNumber"] == "OVERRIDE1"

    def test_refuses_to_book_without_passport(self, target):
        h = self._handler(target)
        with applicant(APPLICANT_PASSPORT=""), patch.object(h, "_curl") as curl:
            assert h.book_appointment("03.09.2026") is False
            curl.assert_not_called()

    def test_refuses_to_book_without_applicant_details(self, target):
        h = self._handler(target)
        with patch.object(h, "_curl") as curl:
            assert h.book_appointment("03.09.2026") is False
            curl.assert_not_called()

    def test_stops_when_date_has_no_day_link(self, target, booking_config):
        h = self._handler(target)
        with patch.object(h, "_curl") as curl:
            assert h.book_appointment("01.01.2030") is False
            curl.assert_not_called()

    def test_gives_up_after_max_attempts_reporting_each_miss(self, target, booking_config):
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", False), \
             patch.object(config, "CAPTCHA_MAX_ATTEMPTS", 3), \
             patch.object(h, "_curl", return_value=True), \
             patch.object(h, "solve_captcha", return_value="wrong"), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", return_value=True), \
             patch.object(h, "report_bad_captcha") as report:
            assert h.book_appointment("03.09.2026") is False
            assert report.call_count == 3  # every miss refunded

    def test_books_on_second_attempt_after_a_misread(self, target, booking_config):
        """A single bad captcha must not cost the slot."""
        h = self._handler(target)
        with patch.object(config, "BOOKING_DRY_RUN", False), \
             patch.object(config, "CAPTCHA_MAX_ATTEMPTS", 3), \
             patch.object(h, "_curl", return_value=True), \
             patch.object(h, "solve_captcha", side_effect=["wrong", "right"]), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", side_effect=[True, False]), \
             patch("lib.appointment_handler.notifications.notify_appointment_booked") as notify, \
             patch.object(h, "report_bad_captcha"):
            assert h.book_appointment("03.09.2026") is True
            notify.assert_called_once()


class TestMonthViewRetry:
    def _handler(self, target):
        from lib.appointment_handler import AppointmentHandler
        return AppointmentHandler(root_folder=str(target))

    def test_retries_until_captcha_accepted(self, target):
        h = self._handler(target)
        with patch.object(config, "CAPTCHA_MAX_ATTEMPTS", 3), \
             patch.object(h, "fetch_captcha_page", return_value=True), \
             patch.object(h, "solve_captcha", side_effect=["a", "b", "c"]), \
             patch.object(h, "fetch_response_page", return_value=True), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected",
                   side_effect=[True, False]), \
             patch.object(h, "report_bad_captcha") as report:
            assert h.fetch_month_view() is True
            assert report.call_count == 1

    def test_gives_up_after_max_attempts(self, target):
        h = self._handler(target)
        with patch.object(config, "CAPTCHA_MAX_ATTEMPTS", 2), \
             patch.object(h, "fetch_captcha_page", return_value=True), \
             patch.object(h, "solve_captcha", return_value="x"), \
             patch.object(h, "fetch_response_page", return_value=True), \
             patch("lib.appointment_handler.extractors.captcha_was_rejected", return_value=True), \
             patch.object(h, "report_bad_captcha"):
            assert h.fetch_month_view() is False


# Shaped like the live Baku national-visa form: the applicant's passport,
# birth date, purpose and phone are embassy-defined fields with meaningless
# names, each paired with hidden definitionId/index companions.
BAKU_FORM = f"""
<html><body><div id="content"><div><fieldset><div>x</div><div>18.08.2026 08:30</div>
<form id="appointment_newAppointmentForm"
      action="/rktermin/extern/appointment_showForm.do" method="post">
  <div><captcha><div style="background:white url('data:image/png;base64,{'QUJD' * 4}')"></div></captcha></div>
  <p>Nachname:</p><input type="text" name="lastname" value=""/>
  <p>Vorname:</p><input type="text" name="firstname" value=""/>
  <p>E-Mail:</p><input type="text" name="email" value=""/>
  <p>E-Mail wiederholen:</p><input type="text" name="emailrepeat" value=""/>
  <p>Xarici Pasportun n&#601;mr&#601;si/Reisepass-Nr./Passport No:</p>
  <input type="text" name="fields[0].content" value=""/>
  <input type="hidden" name="fields[0].definitionId" value="672"/>
  <input type="hidden" name="fields[0].index" value="0"/>
  <p>Geburtsdatum / Do&#287;um tarixi / Date of Birth:</p>
  <input type="text" name="fields1content" value=""/>
  <input type="hidden" name="fields[1].definitionId" value="697"/>
  <input type="hidden" name="fields[1].index" value="1"/>
  <p>S&#601;f&#601;rin m&#601;qs&#601;di / Reisezweck / Purpose of the Journey:</p>
  <select name="fields[2].content">
    <option value=""></option>
    <option value="Ail&#601; birl&#601;&#351;m&#601;si / Familienzusammenf&uuml;hrung / family reunion">Ail&#601; birl&#601;&#351;m&#601;si / Familienzusammenf&uuml;hrung / family reunion</option>
    <option value="Au pair">Au pair</option>
  </select>
  <input type="hidden" name="fields[2].definitionId" value="682"/>
  <input type="hidden" name="fields[2].index" value="2"/>
  <p>Telefonnummer / telefon n&#246;mr&#601;si / Telephone No:</p>
  <input type="text" name="fields[3].content" value=""/>
  <input type="hidden" name="fields[3].definitionId" value="718"/>
  <input type="hidden" name="fields[3].index" value="3"/>
  <input type="text" name="captchaText" value=""/>
  <input type="submit" name="action:appointment_addAppointment" value="Speichern"/>
</form></fieldset></div></div></body></html>
"""


class TestEmbassyDefinedFields:
    """Baku names the applicant's fields "fields[0].content" etc; only the
    label says what they are."""

    @pytest.fixture
    def baku(self, tmp_path):
        t = tmp_path / "target"
        t.mkdir()
        (t / "response.html").write_text(MONTH_PAGE, encoding="utf-8")
        (t / "appointmentschedulingpage.html").write_text(DAY_PAGE, encoding="utf-8")
        (t / "bookfinalappt.html").write_text(BAKU_FORM, encoding="utf-8")
        return tmp_path

    def _fill(self, baku, **over):
        from lib.appointment_handler import AppointmentHandler
        form = extractors.extract_form_context(str(baku), "bookfinalappt.html")
        with applicant(), \
             patch.object(config, "APPLICANT_BIRTHDATE", over.get("birth", "23.08.1991")), \
             patch.object(config, "APPLICANT_PHONE", over.get("phone", "+994 50 123 4567")), \
             patch.object(config, "APPLICANT_PURPOSE", over.get("purpose", "family reunion")), \
             patch.object(config, "APPLICANT_EXTRA_FIELDS", {}):
            hints = dict(config.APPLICANT_FIELD_HINTS)
            hints.update({
                "pasport": "C01548134", "reisepass": "C01548134",
                "geburtsdatum": over.get("birth", "23.08.1991"),
                "date of birth": over.get("birth", "23.08.1991"),
                "telefon": over.get("phone", "+994 50 123 4567"),
                "telephone": over.get("phone", "+994 50 123 4567"),
            })
            with patch.object(config, "APPLICANT_FIELD_HINTS", hints):
                h = AppointmentHandler(root_folder=str(baku))
                return h._fill_applicant_fields(form)

    def test_passport_found_by_label_not_name(self, baku):
        assert self._fill(baku)["fields[0].content"] == "C01548134"

    def test_birthdate_found_by_label(self, baku):
        assert self._fill(baku)["fields1content"] == "23.08.1991"

    def test_phone_found_by_label(self, baku):
        assert self._fill(baku)["fields[3].content"] == "+994 50 123 4567"

    def test_hidden_companions_are_never_overwritten(self, baku):
        """definitionId/index share the visible field's label and must survive."""
        f = self._fill(baku)
        assert f["fields[0].definitionId"] == "672"
        assert f["fields[0].index"] == "0"
        assert f["fields[3].definitionId"] == "718"
        assert f["fields[3].index"] == "3"

    def test_purpose_dropdown_selects_family_reunion(self, baku):
        chosen = self._fill(baku)["fields[2].content"]
        assert "family reunion" in chosen
        assert chosen.startswith("Ail")

    def test_unmatched_purpose_leaves_dropdown_empty(self, baku):
        assert self._fill(baku, purpose="studying astrophysics")["fields[2].content"] == ""

    def test_email_repeat_is_filled_too(self, baku):
        f = self._fill(baku)
        assert f["email"] == f["emailrepeat"] == "r@example.com"

    def test_submit_action_discovered_from_live_markup(self, baku):
        form = extractors.extract_form_context(str(baku), "bookfinalappt.html")
        assert extractors.pick_submit_action(form["submits"]) == (
            "action:appointment_addAppointment", "Speichern",
        )


class TestCaptchaFormAutodetect:
    def test_extracts_image_without_form_id(self, target, tmp_path):
        html = utils.load_html_file(str(target / "target" / "bookfinalappt.html"))
        out = str(tmp_path / "out.jpg")
        assert utils.extract_base64_image(html, None, out) is True
        assert Path(out).read_bytes() == b"ABC" * 4
