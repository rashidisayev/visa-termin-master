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
    
    def book_appointment(self, available_date: str, captcha_solution: str) -> bool:
        """
        Automatically book the appointment.
        
        Args:
            available_date: Date to book
            captcha_solution: Captcha solution for booking
            
        Returns:
            True if booking successful, False otherwise
        """
        self.logger.info(f"Step 5: Booking appointment for {available_date}...")
        
        cookies_path = os.path.join(self.root_folder, "target", "cookies")
        
        # Get appointment scheduling page
        url = f"{config.RESCHEDULING_BASE_URL}?{config.CONSULATE_DETAILS}&dateStr={available_date}&rebooking=true&token={config.RESCHEDULING_TOKEN}"
        output_file = os.path.join(self.root_folder, "target", "appointmentschedulingpage.html")
        
        cmd = [
            "curl", "-v", "-L", "-s", "-S",
            "-b", cookies_path,
            "-c", cookies_path,
            "-o", output_file,
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to fetch appointment page: {result.stderr}")
                return False
            
            # Extract reschedule URL
            resch_url = extractors.extract_reschedule_url(self.root_folder, "appointmentschedulingpage.html")
            if not resch_url:
                self.logger.error("Failed to extract reschedule URL")
                return False
            
            full_url = f"{config.HOST}/{resch_url}"
            self.logger.info(f"Reschedule URL: {full_url}")
            
            # Get final booking page
            output_file = os.path.join(self.root_folder, "target", "bookfinalappt.html")
            cmd = [
                "curl", "-v", "-L", "-s", "-S",
                "-b", cookies_path,
                "-c", cookies_path,
                "-o", output_file,
                full_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to fetch final booking page: {result.stderr}")
                return False
            
            # Extract booking time
            booking_time = extractors.extract_booking_time(self.root_folder, "bookfinalappt.html")
            if not booking_time:
                self.logger.error("Failed to extract booking time")
                return False
            
            self.logger.info(f"Booking time: {booking_time}")
            
            # Solve captcha for booking
            solution = self.solve_captcha("bookfinalappt.html", config.REBOOK_CAPTCHA_SELECTOR)
            if not solution:
                self.logger.error("Failed to solve booking captcha")
                return False
            
            # Submit booking
            self.logger.info(f"Submitting appointment booking for {available_date} at {booking_time}")
            
            cmd = [
                "curl", "-X", "POST",
                "-v", "-L", "-s", "-S",
                "-F", "request_locale=en",
                "-F", f"captchaText={solution}",
                "-F", f"locationCode={config.LOCATION_CODE}",
                "-F", f"realmId={config.REALM_ID}",
                "-F", f"categoryId={config.CATEGORY_ID}",
                "-F", f"date={available_date}",
                "-F", f"dateStr={available_date}",
                "-F", "rebooking=true",
                "-F", f"token={config.RESCHEDULING_TOKEN}",
                "-F", "action:appointment_rebookAppointment=Submit",
                "-b", cookies_path,
                "-c", cookies_path,
                "-o", os.path.join(self.root_folder, "target", "bookingdone.html"),
                config.BOOKING_BASE_URL
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("Appointment successfully booked!")
                notifications.notify_appointment_booked(available_date, booking_time)
                return True
            else:
                self.logger.error(f"Failed to submit booking: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error booking appointment: {e}")
            notifications.notify_error(str(e))
            return False
    
    def run_full_workflow(self, auto_book: bool = False) -> bool:
        """
        Run the full workflow: fetch, solve, check, and optionally book.
        
        Args:
            auto_book: Whether to automatically book if date is available
            
        Returns:
            True if workflow completed successfully
        """
        try:
            # Step 1: Fetch captcha page
            if not self.fetch_captcha_page():
                return False
            
            # Step 2: Solve captcha
            captcha_solution = self.solve_captcha(
                "captchapage.html",
                config.CAPTCHA_SELECTOR_MONTH
            )
            if not captcha_solution:
                return False
            
            # Step 3: Fetch response page
            if not self.fetch_response_page(captcha_solution):
                return False

            # The portal rejects wrong captcha solutions - report those back to
            # 2Captcha so they are refunded, and stop this run.
            if extractors.captcha_was_rejected(self.root_folder):
                self.logger.error("Portal rejected the captcha solution")
                self.report_bad_captcha()
                return False

            # Step 4: Check for available dates
            available_date = self.check_and_notify_available_date()
            
            # Step 5: Auto-book if enabled and date available
            if auto_book and available_date:
                self.book_appointment(available_date, captcha_solution)
            
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
