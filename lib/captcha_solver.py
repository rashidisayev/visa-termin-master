"""
Captcha solving via the 2Captcha API.

Replaces the previous DeathByCaptcha binary integration: instead of shelling out
to a native client and reading answer files off disk, the image is posted to the
2Captcha HTTP API and the answer is polled until it is ready.

The consulate captcha is a plain base64 JPG embedded in the page, so the
"normal captcha" (ImageToText) endpoints are all that is needed.
"""
import base64
import os
import time
from typing import Any, Dict, Optional

from . import config, utils

# Note: requests is imported lazily so the core modules stay importable
# without external dependencies (same convention as BeautifulSoup in utils).

# Result strings that mean "keep waiting" rather than "give up".
RETRYABLE_RESULTS = frozenset({
    "CAPCHA_NOT_READY",
    "CAPTCHA_NOT_READY",
    "ERROR_NO_SLOT_AVAILABLE",
})


class TwoCaptchaSolver:
    """Solves image captchas through the 2Captcha API."""

    def __init__(self, api_key: Optional[str] = None, logger: Optional[Any] = None):
        """
        Initialize the solver.

        Args:
            api_key: 2Captcha API key. Defaults to config.CAPTCHA_API_KEY
            logger: Logger instance. Defaults to the shared project logger
        """
        self.api_key = api_key if api_key is not None else config.CAPTCHA_API_KEY
        self.logger = logger or utils.setup_logger()
        self.last_captcha_id: Optional[str] = None

    def solve_image(self, image_path: str) -> Optional[str]:
        """
        Solve an image captcha.

        Args:
            image_path: Path to the captcha image on disk

        Returns:
            Captcha solution text, or None if it could not be solved
        """
        if not self.api_key:
            self.logger.error(
                "CAPTCHA_API_KEY is not set - get a key at https://2captcha.com/enterpage"
            )
            return None

        if not os.path.exists(image_path):
            self.logger.error(f"Captcha image not found: {image_path}")
            return None

        try:
            captcha_id = self._submit(image_path)
            if not captcha_id:
                return None

            self.last_captcha_id = captcha_id
            return self._poll_result(captcha_id)

        except Exception as e:
            self.logger.error(f"Error solving captcha via 2Captcha: {e}")
            return None

    def report_bad(self, captcha_id: Optional[str] = None) -> bool:
        """
        Report an incorrect solution so 2Captcha refunds it.

        Args:
            captcha_id: Captcha ID to report. Defaults to the last solved captcha

        Returns:
            True if the report was accepted
        """
        return self._report("reportbad", captcha_id)

    def report_good(self, captcha_id: Optional[str] = None) -> bool:
        """
        Confirm a correct solution (improves worker scoring).

        Args:
            captcha_id: Captcha ID to report. Defaults to the last solved captcha

        Returns:
            True if the report was accepted
        """
        return self._report("reportgood", captcha_id)

    def get_balance(self) -> Optional[float]:
        """
        Fetch the remaining account balance in USD.

        Returns:
            Balance as a float, or None if it could not be retrieved
        """
        try:
            data = self._get({"action": "getbalance"})
            if data.get("status") == 1:
                return float(data.get("request"))
            self.logger.error(f"Failed to fetch 2Captcha balance: {data}")
        except Exception as e:
            self.logger.error(f"Error fetching 2Captcha balance: {e}")
        return None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _submit(self, image_path: str) -> Optional[str]:
        """Upload the captcha image and return the 2Captcha task ID."""
        import requests

        with open(image_path, "rb") as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

        payload = {
            "key": self.api_key,
            "method": "base64",
            "body": image_b64,
            "json": 1,
            "phrase": 0,
            "regsense": 1 if config.CAPTCHA_CASE_SENSITIVE else 0,
            "numeric": config.CAPTCHA_NUMERIC,
            "calc": 0,
            "min_len": config.CAPTCHA_MIN_LENGTH,
            "max_len": config.CAPTCHA_MAX_LENGTH,
        }

        response = requests.post(
            config.CAPTCHA_API_URL,
            data=payload,
            timeout=config.CAPTCHA_HTTP_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 1 or not data.get("request"):
            self.logger.error(f"Captcha upload rejected by 2Captcha: {data}")
            return None

        captcha_id = data["request"]
        self.logger.info(f"Captcha uploaded to 2Captcha (id: {captcha_id})")
        return captcha_id

    def _poll_result(self, captcha_id: str) -> Optional[str]:
        """Poll for the answer until it is ready or the time budget runs out."""
        deadline = time.monotonic() + config.CAPTCHA_TIMEOUT

        # 2Captcha needs a few seconds before the first result is available.
        time.sleep(min(config.CAPTCHA_POLL_INTERVAL, config.CAPTCHA_TIMEOUT))

        while time.monotonic() < deadline:
            data = self._get({"action": "get", "id": captcha_id})
            result = data.get("request")

            if data.get("status") == 1 and result:
                self.logger.info(f"Captcha solved (id: {captcha_id}, answer: {result})")
                return result

            if result in RETRYABLE_RESULTS:
                time.sleep(config.CAPTCHA_POLL_INTERVAL)
                continue

            self.logger.error(f"2Captcha failed to solve captcha {captcha_id}: {data}")
            return None

        self.logger.error(
            f"Timed out after {config.CAPTCHA_TIMEOUT}s waiting for captcha {captcha_id}"
        )
        return None

    def _report(self, action: str, captcha_id: Optional[str]) -> bool:
        """Send a reportbad/reportgood call for a solved captcha."""
        captcha_id = captcha_id or self.last_captcha_id
        if not captcha_id:
            self.logger.warning(f"No captcha ID available to {action}")
            return False

        try:
            data = self._get({"action": action, "id": captcha_id})
            accepted = data.get("status") == 1
            if accepted:
                self.logger.info(f"Sent {action} for captcha {captcha_id}")
            else:
                self.logger.warning(f"{action} for captcha {captcha_id} rejected: {data}")
            return accepted
        except Exception as e:
            self.logger.error(f"Error sending {action} for captcha {captcha_id}: {e}")
            return False

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the 2Captcha result endpoint and return the decoded JSON."""
        import requests

        response = requests.get(
            config.CAPTCHA_RESULT_URL,
            params={"key": self.api_key, "json": 1, **params},
            timeout=config.CAPTCHA_HTTP_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()


def get_solver(logger: Optional[Any] = None) -> Optional[TwoCaptchaSolver]:
    """
    Build the solver for the configured provider.

    Args:
        logger: Logger instance passed through to the solver

    Returns:
        Solver instance, or None if the configured provider is unsupported
    """
    provider = config.CAPTCHA_PROVIDER.lower()

    if provider in ("2captcha", "twocaptcha"):
        return TwoCaptchaSolver(logger=logger)

    (logger or utils.setup_logger()).error(
        f"Unsupported CAPTCHA_PROVIDER '{config.CAPTCHA_PROVIDER}' (supported: 2captcha)"
    )
    return None
