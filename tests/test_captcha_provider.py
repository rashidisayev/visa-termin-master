"""
Tests for the 2Captcha-based captcha solving path.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import captcha_solver, config  # noqa: E402


def _json_response(payload):
    """Build a mock requests response returning the given JSON payload."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


@pytest.fixture
def captcha_image(tmp_path):
    """A throwaway captcha image on disk."""
    image = tmp_path / "captcha.jpg"
    image.write_bytes(b"\xff\xd8\xff\xe0 fake jpeg bytes")
    return str(image)


@pytest.fixture(autouse=True)
def no_sleep():
    """Skip the polling delays so tests run instantly."""
    with patch("lib.captcha_solver.time.sleep"):
        yield


class TestConfig:
    def test_defaults_to_2captcha(self):
        assert config.CAPTCHA_PROVIDER == "2captcha"
        assert config.CAPTCHA_API_URL == "https://2captcha.com/in.php"
        assert config.CAPTCHA_RESULT_URL == "https://2captcha.com/res.php"
        assert config.CAPTCHA_TIMEOUT == 120

    def test_no_deathbycaptcha_settings_remain(self):
        for removed in ("DBC_USERNAME", "DBC_PASSWORD", "DBC_BINARY_PATH"):
            assert not hasattr(config, removed)

    def test_get_solver_returns_two_captcha_solver(self):
        assert isinstance(captcha_solver.get_solver(), captcha_solver.TwoCaptchaSolver)

    def test_get_solver_rejects_unknown_provider(self):
        with patch.object(config, "CAPTCHA_PROVIDER", "deathbycaptcha"):
            assert captcha_solver.get_solver() is None


class TestSolveImage:
    def test_uploads_image_and_returns_answer(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")

        with patch("requests.post", return_value=_json_response({"status": 1, "request": "42"})) as post, \
             patch("requests.get", return_value=_json_response({"status": 1, "request": "AB12CD"})) as get:
            assert solver.solve_image(captcha_image) == "AB12CD"

        payload = post.call_args.kwargs["data"]
        assert post.call_args.args[0] == config.CAPTCHA_API_URL
        assert payload["key"] == "test-key"
        assert payload["method"] == "base64"
        assert payload["body"]  # base64 of the image
        assert get.call_args.kwargs["params"]["id"] == "42"
        assert solver.last_captcha_id == "42"

    def test_polls_until_solution_is_ready(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")
        responses = [
            _json_response({"status": 0, "request": "CAPCHA_NOT_READY"}),
            _json_response({"status": 0, "request": "CAPCHA_NOT_READY"}),
            _json_response({"status": 1, "request": "SOLVED"}),
        ]

        with patch("requests.post", return_value=_json_response({"status": 1, "request": "42"})), \
             patch("requests.get", side_effect=responses) as get:
            assert solver.solve_image(captcha_image) == "SOLVED"
            assert get.call_count == 3

    def test_returns_none_on_upload_error(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="bad-key")

        with patch("requests.post", return_value=_json_response({"status": 0, "request": "ERROR_WRONG_USER_KEY"})), \
             patch("requests.get") as get:
            assert solver.solve_image(captcha_image) is None
            get.assert_not_called()

    def test_returns_none_when_captcha_unsolvable(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")

        with patch("requests.post", return_value=_json_response({"status": 1, "request": "42"})), \
             patch("requests.get", return_value=_json_response({"status": 0, "request": "ERROR_CAPTCHA_UNSOLVABLE"})) as get:
            assert solver.solve_image(captcha_image) is None
            assert get.call_count == 1  # gives up instead of polling on

    def test_returns_none_without_api_key(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="")

        with patch("requests.post") as post:
            assert solver.solve_image(captcha_image) is None
            post.assert_not_called()

    def test_returns_none_when_image_missing(self, tmp_path):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")

        with patch("requests.post") as post:
            assert solver.solve_image(str(tmp_path / "nope.jpg")) is None
            post.assert_not_called()

    def test_survives_network_error(self, captcha_image):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")

        with patch("requests.post", side_effect=OSError("connection reset")):
            assert solver.solve_image(captcha_image) is None


class TestReporting:
    def test_report_bad_uses_last_captcha_id(self):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")
        solver.last_captcha_id = "42"

        with patch("requests.get", return_value=_json_response({"status": 1, "request": "OK_REPORT_RECORDED"})) as get:
            assert solver.report_bad() is True

        params = get.call_args.kwargs["params"]
        assert params["action"] == "reportbad"
        assert params["id"] == "42"

    def test_report_bad_without_id_is_a_noop(self):
        solver = captcha_solver.TwoCaptchaSolver(api_key="test-key")

        with patch("requests.get") as get:
            assert solver.report_bad() is False
            get.assert_not_called()


class TestAppointmentHandlerIntegration:
    def test_solve_captcha_delegates_to_solver(self, tmp_path):
        from lib.appointment_handler import AppointmentHandler

        handler = AppointmentHandler(root_folder=str(tmp_path))
        solver = MagicMock()
        solver.solve_image.return_value = "AB12CD"

        with patch("lib.appointment_handler.extractors.extract_captcha_image", return_value=True), \
             patch("lib.appointment_handler.captcha_solver.get_solver", return_value=solver):
            result = handler.solve_captcha("captchapage.html", "appointment_captcha_month")

        assert result == "AB12CD"
        assert solver.solve_image.call_args.args[0].endswith("target/captcha.jpg")
        assert handler.last_solver is solver

    def test_solve_captcha_returns_none_when_extraction_fails(self, tmp_path):
        from lib.appointment_handler import AppointmentHandler

        handler = AppointmentHandler(root_folder=str(tmp_path))

        with patch("lib.appointment_handler.extractors.extract_captcha_image", return_value=False), \
             patch("lib.appointment_handler.captcha_solver.get_solver") as get_solver:
            assert handler.solve_captcha("captchapage.html", "appointment_captcha_month") is None
            get_solver.assert_not_called()

    def test_rejected_captcha_is_reported(self, tmp_path):
        from lib.appointment_handler import AppointmentHandler

        handler = AppointmentHandler(root_folder=str(tmp_path))
        solver = MagicMock()
        handler.last_solver = solver

        handler.report_bad_captcha()

        solver.report_bad.assert_called_once()
        assert handler.last_solver is None

    @pytest.mark.parametrize("message", [
        # Exact wording returned by the live RK-Termin portal
        "Der eingegebene Text ist falsch",
        "The entered text was wrong",
    ])
    def test_captcha_rejection_detected_in_response_page(self, tmp_path, message):
        from lib import extractors

        target = tmp_path / "target"
        target.mkdir()
        (target / "response.html").write_text(
            f"<html><body><div class='error'>{message}</div></body></html>",
            encoding="utf-8",
        )

        assert extractors.captcha_was_rejected(str(tmp_path)) is True

    def test_valid_response_page_is_not_flagged(self, tmp_path):
        from lib import extractors

        target = tmp_path / "target"
        target.mkdir()
        (target / "response.html").write_text(
            "<html><body>Termin am 25.03.2026</body></html>", encoding="utf-8"
        )

        assert extractors.captcha_was_rejected(str(tmp_path)) is False
