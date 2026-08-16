#!/usr/bin/env python3
"""
Main appointment handler module for visa appointment automation.
Orchestrates the entire appointment checking and booking workflow.
"""
import sys
import os
import subprocess
import time
from typing import Optional, Dict, Any
from urllib.parse import unquote

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import config, utils, extractors, notifications, captcha_solver


class AppointmentHandler:
    """Handles the full appointment checking and booking workflow."""
    
    def __init__(self, root_folder: Optional[str] = None):
        """
        Initialize appointment handler.
        
        Args:
            root_folder: Root folder path, defaults to current directory
        """
        self.root_folder = root_folder or os.getcwd()
        self.logger = utils.setup_logger()
        # Solver behind the most recent solution, kept so a rejected captcha
        # can be reported back to 2Captcha for a refund.
        self.last_solver: Optional[captcha_solver.TwoCaptchaSolver] = None
        self.logger.info("=" * 60)
        self.logger.info("Visa Appointment Handler Initialized")
        self.logger.info("=" * 60)
    
    def fetch_captcha_page(self, cookies_file: str = "cookies") -> bool:
        """
        Fetch the captcha page from the consulate website.
        
        Args:
            cookies_file: Path to cookies file
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Step 1: Fetching captcha page...")
        
        cookies_path = os.path.join(self.root_folder, "target", cookies_file)
        output_file = os.path.join(self.root_folder, "target", "captchapage.html")
        
        url = f"{config.CONSULATE_BASE_URL}?{config.CONSULATE_DETAILS}"
        
        cmd = [
            "curl", "-v", "-L", "-s", "-S",
            "-A", config.USER_AGENT,
            "-b", cookies_path,
            "-c", cookies_path,
            "-o", output_file,
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"Captcha page saved to {output_file}")
                time.sleep(3)  # Wait for file to be written
                return True
            else:
                self.logger.error(f"Failed to fetch captcha page: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fetching captcha page: {e}")
            return False
    
    def solve_captcha(self, captcha_file: str, selector_id: str) -> Optional[str]:
        """
        Extract the captcha image from a saved page and solve it via 2Captcha.

        Args:
            captcha_file: HTML file containing captcha
            selector_id: CSS selector ID for captcha form

        Returns:
            Captcha solution or None if failed
        """
        self.logger.info(
            f"Step 2: Solving captcha from {captcha_file} via {config.CAPTCHA_PROVIDER}..."
        )

        if not extractors.extract_captcha_image(self.root_folder, captcha_file, selector_id):
            self.logger.error("Failed to extract captcha image")
            return None

        solver = captcha_solver.get_solver(logger=self.logger)
        if not solver:
            return None

        captcha_path = os.path.join(self.root_folder, "target", "captcha.jpg")
        solution = solver.solve_image(captcha_path)

        if solution:
            self.last_solver = solver
        else:
            self.last_solver = None

        return solution

    def report_bad_captcha(self) -> None:
        """
        Tell 2Captcha the last solution was wrong so the cost is refunded.
        Called when the portal rejects a solved captcha.
        """
        if config.CAPTCHA_REPORT_BAD and self.last_solver:
            self.last_solver.report_bad()
        self.last_solver = None

    def fetch_response_page(self, captcha_solution: str) -> bool:
        """
        Fetch the response page with available dates.
        
        Args:
            captcha_solution: Solved captcha text
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Step 3: Fetching response page with available dates...")

        cookies_path = os.path.join(self.root_folder, "target", "cookies")
        output_file = os.path.join(self.root_folder, "target", "response.html")

        # Post back to the form's own action URL: it carries the ;jsessionid
        # that ties this request to the session the captcha was issued in.
        form = extractors.extract_form_context(
            self.root_folder, "captchapage.html", config.CAPTCHA_SELECTOR_MONTH
        )
        if not form:
            self.logger.error("Could not read the captcha form context")
            return False

        fields = dict(form["fields"])
        fields["captchaText"] = captcha_solution
        fields.setdefault("locationCode", config.LOCATION_CODE)
        fields.setdefault("realmId", config.REALM_ID)
        fields.setdefault("categoryId", config.CATEGORY_ID)

        cmd = [
            "curl", "-X", "POST",
            "-v", "-L", "-s", "-S",
            "-A", config.USER_AGENT,
        ]
        for name, value in fields.items():
            cmd += ["--data-urlencode", f"{name}={value}"]
        # Struts dispatches on the submit button's name
        cmd += ["--data-urlencode", f"{config.SHOW_MONTH_ACTION}=Weiter"]
        cmd += [
            "-b", cookies_path,
            "-c", cookies_path,
            "-o", output_file,
            form["action"]
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Response page saved to {output_file}")
                return True
            else:
                self.logger.error(f"Failed to fetch response page: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fetching response page: {e}")
            return False
    
    def check_and_notify_available_date(self) -> Optional[str]:
        """
        Check for available appointment date and notify if found.
        
        Returns:
            Available date string or None if no acceptable date found
        """
        self.logger.info("Step 4: Checking for available appointment dates...")
        
        available_date = extractors.extract_available_date(self.root_folder)
        
        if available_date:
            self.logger.info(f"Available date found: {available_date}")
            notifications.notify_available_date(available_date)
            return available_date
        else:
            self.logger.info("No acceptable appointment date found")
            return None
    
    def _curl(self, url: str, output_file: str, post_fields: Optional[Dict[str, str]] = None) -> bool:
        """
        Fetch a portal URL through curl, reusing the session cookie jar.

        Args:
            url: Absolute URL to request
            output_file: Where to save the response body
            post_fields: When given, POST these url-encoded fields instead of GET

        Returns:
            True if curl exited cleanly
        """
        cookies_path = os.path.join(self.root_folder, "target", "cookies")

        cmd = ["curl", "-v", "-L", "-s", "-S", "-A", config.USER_AGENT]
        if post_fields is not None:
            cmd.append("-X")
            cmd.append("POST")
            for name, value in post_fields.items():
                cmd += ["--data-urlencode", f"{name}={value}"]
        cmd += ["-b", cookies_path, "-c", cookies_path, "-o", output_file, url]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error(f"Request failed ({url}): {result.stderr.strip()[:200]}")
            return False
        return True

    def fetch_month_view(self) -> bool:
        """
        Reach the month view: fetch the captcha page, solve it, and submit.

        Retries with a fresh captcha when the portal rejects the answer.
        Solvers misread these captchas often enough that a single failure
        would otherwise throw away a run - and possibly a free slot.

        Returns:
            True once the month view has been loaded
        """
        for attempt in range(1, config.CAPTCHA_MAX_ATTEMPTS + 1):
            if not self.fetch_captcha_page():
                return False

            solution = self.solve_captcha("captchapage.html", config.CAPTCHA_SELECTOR_MONTH)
            if not solution:
                self.logger.warning(f"No solution on attempt {attempt}/{config.CAPTCHA_MAX_ATTEMPTS}")
                continue

            if not self.fetch_response_page(solution):
                return False

            if not extractors.captcha_was_rejected(self.root_folder):
                return True

            # Wrong answer: report it for a refund and try a fresh captcha.
            self.logger.warning(
                f"Portal rejected the captcha (attempt {attempt}/{config.CAPTCHA_MAX_ATTEMPTS})"
            )
            self.report_bad_captcha()

        self.logger.error(f"Giving up after {config.CAPTCHA_MAX_ATTEMPTS} captcha attempts")
        return False

    def book_appointment(self, available_date: str) -> bool:
        """
        Book an appointment on the given date.

        Walks the portal's own links rather than rebuilding URLs, so the
        session survives every hop:

            month view -> appointment_showDay -> appointment_showForm -> submit

        Nothing here is specific to a visa category: the same flow serves
        Schengen (C) and national (D) appointments, and the submit action is
        read off the live form instead of being hardcoded.

        Args:
            available_date: Date to book, as DD.MM.YYYY

        Returns:
            True if the appointment was booked (or a dry run completed)
        """
        self.logger.info(f"Step 5: Booking appointment for {available_date}...")

        if not self._applicant_is_configured():
            return False

        # 5a. Follow the day link for this date from the month view.
        day_links = [
            url for url in extractors.extract_links(self.root_folder, "response.html", "appointment_showDay.do")
            if available_date in unquote(url)
        ]
        if not day_links:
            self.logger.error(f"No day link found for {available_date} on the month view")
            return False

        day_page = os.path.join(self.root_folder, "target", "appointmentschedulingpage.html")
        if not self._curl(day_links[0], day_page):
            return False

        # 5b. Pick a time slot on that day.
        slot_links = extractors.extract_links(
            self.root_folder, "appointmentschedulingpage.html", "appointment_showForm.do"
        )
        if not slot_links:
            self.logger.error(f"No bookable time slots offered on {available_date}")
            return False

        self.logger.info(f"{len(slot_links)} slot(s) offered; taking the first")

        # 5c-5e. Fill and submit the booking form. A misread captcha here would
        # lose the slot itself, so retry with a freshly loaded form each time.
        for attempt in range(1, config.CAPTCHA_MAX_ATTEMPTS + 1):
            form_page = os.path.join(self.root_folder, "target", "bookfinalappt.html")
            if not self._curl(slot_links[0], form_page):
                return False

            booking_time = extractors.extract_booking_time(self.root_folder, "bookfinalappt.html")
            self.logger.info(f"Booking time: {booking_time or 'unknown'}")

            solution = self.solve_captcha("bookfinalappt.html", None)
            if not solution:
                self.logger.warning(f"No booking captcha solution (attempt {attempt})")
                continue

            form = extractors.extract_form_context(self.root_folder, "bookfinalappt.html")
            if not form:
                self.logger.error("Could not read the booking form")
                return False

            submit = extractors.pick_submit_action(form["submits"])
            if not submit:
                self.logger.error(f"No submit button on the booking form: {form['submits']}")
                return False

            fields = self._fill_applicant_fields(form["fields"])
            fields["captchaText"] = solution
            fields[submit[0]] = submit[1] or "Submit"

            if config.BOOKING_DRY_RUN:
                self._log_dry_run(form["action"], fields, available_date, booking_time)
                return True

            self.logger.info(
                f"Submitting booking for {available_date} at {booking_time} via {submit[0]}"
            )
            done_page = os.path.join(self.root_folder, "target", "bookingdone.html")
            if not self._curl(form["action"], done_page, post_fields=fields):
                return False

            if not extractors.captcha_was_rejected(self.root_folder, "bookingdone.html"):
                self.logger.info("Appointment successfully booked!")
                notifications.notify_appointment_booked(available_date, booking_time or "")
                return True

            self.logger.warning(f"Booking captcha rejected (attempt {attempt})")
            self.report_bad_captcha()

        self.logger.error("Could not book: captcha rejected on every attempt")
        return False

    def _fill_applicant_fields(self, form_fields: Dict[str, str]) -> Dict[str, str]:
        """
        Fill the applicant's details into whatever the live form happens to ask for.

        Field names vary by embassy and visa category, so match loosely on the
        name rather than assuming a fixed set. Any field left empty is logged:
        that is how an unexpected required field (a passport number, a date of
        birth) shows up in a dry run instead of failing a real booking.

        Args:
            form_fields: Fields as read from the live form

        Returns:
            A new dict with the applicant's values filled in
        """
        fields = dict(form_fields)

        for name in list(fields):
            lowered = name.lower()

            if name in config.APPLICANT_EXTRA_FIELDS:
                fields[name] = config.APPLICANT_EXTRA_FIELDS[name]
                continue

            for hint, value in config.APPLICANT_FIELD_HINTS.items():
                if hint in lowered and value:
                    fields[name] = value
                    break

        # Anything the portal asked for that we could not fill.
        unfilled = [
            name for name, value in fields.items()
            if not value and name not in ("captchaText", "token", "rebooking")
        ]
        if unfilled:
            self.logger.warning(
                f"Form fields left empty: {', '.join(unfilled)} - "
                f"if the booking is rejected, set them via APPLICANT_EXTRA_FIELDS"
            )

        return fields

    def _applicant_is_configured(self) -> bool:
        """Check that the details the portal writes into the booking are present."""
        missing = [
            name for name, value in (
                ("APPLICANT_LASTNAME", config.APPLICANT_LASTNAME),
                ("APPLICANT_FIRSTNAME", config.APPLICANT_FIRSTNAME),
                ("APPLICANT_EMAIL", config.APPLICANT_EMAIL),
                ("APPLICANT_PASSPORT", config.APPLICANT_PASSPORT),
            ) if not value
        ]
        if missing:
            self.logger.error(f"Cannot book: {', '.join(missing)} not set")
            return False
        return True

    def _log_dry_run(self, url: str, fields: Dict[str, str], date: str, time_str: Optional[str]) -> None:
        """Report exactly what a real submission would have sent."""
        self.logger.warning("=" * 60)
        self.logger.warning("DRY RUN - the booking was NOT submitted")
        self.logger.warning(f"  date : {date} {time_str or ''}")
        self.logger.warning(f"  POST : {url}")
        for name, value in fields.items():
            shown = value if name != "captchaText" else f"{value} (solved)"
            self.logger.warning(f"    {name} = {shown}")
        self.logger.warning("Set BOOKING_DRY_RUN=false to book for real")
        self.logger.warning("=" * 60)
    
    def run_full_workflow(self, auto_book: bool = False) -> bool:
        """
        Run the full workflow: fetch, solve, check, and optionally book.
        
        Args:
            auto_book: Whether to automatically book if date is available
            
        Returns:
            True if workflow completed successfully
        """
        try:
            # Steps 1-3: reach the month view, retrying on a misread captcha
            if not self.fetch_month_view():
                return False

            # Step 4: Check for available dates
            available_date = self.check_and_notify_available_date()
            
            # Step 5: Auto-book if enabled and date available
            if available_date and (auto_book or config.AUTO_BOOK):
                self.book_appointment(available_date)

            self.logger.info("Workflow completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            notifications.notify_error(str(e))
            return False


def main():
    """Main entry point for command-line usage."""
    root_folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    auto_book = "--auto-book" in sys.argv
    
    handler = AppointmentHandler(root_folder)
    success = handler.run_full_workflow(auto_book=auto_book)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
