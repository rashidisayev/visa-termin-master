"""
HTML extraction module for visa appointment helper.
Provides functions to extract specific information from visa portal HTML pages.
Supports both legacy and new German embassy portal layouts.
"""
import os
from typing import Optional
from urllib.parse import urljoin
from . import config, utils, booking_process


def extract_captcha_image(
    root_folder: str,
    captcha_html_file: str,
    captcha_selector_id: str
) -> bool:
    """
    Extract captcha image from HTML page and save as JPG.
    
    Args:
        root_folder: Root folder path
        captcha_html_file: Name of HTML file containing captcha
        captcha_selector_id: ID selector for the captcha form
        
    Returns:
        True if successful, False otherwise
    """
    logger = utils.setup_logger()
    
    html_path = os.path.join(root_folder, "target", captcha_html_file)
    output_path = os.path.join(root_folder, "target", "captcha.jpg")
    
    logger.info(f"Extracting captcha from {captcha_html_file} using selector {captcha_selector_id}")
    
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return False
    
    success = utils.extract_base64_image(html_content, captcha_selector_id, output_path)
    
    if success:
        logger.info(f"Captcha image saved to {output_path}")
    
    return success


def extract_form_context(
    root_folder: str,
    html_file: str,
    form_id: str
) -> Optional[dict]:
    """
    Extract the submit target and hidden fields of a portal form.

    The RK-Termin portal is a Java/Struts application that keeps the session
    in a URL path parameter (``;jsessionid=...``) on the form's action, not
    only in a cookie. Posting to the bare ``.do`` URL lands in a different
    session, so the captcha can never validate. The form also dispatches on
    the submit button's name (``action:appointment_showMonth``), which has to
    be sent along with the hidden fields.

    Args:
        root_folder: Root folder path
        html_file: Name of the saved HTML file containing the form
        form_id: ID of the form to read

    Returns:
        Dict with 'action' (absolute URL) and 'fields' (dict), or None
    """
    logger = utils.setup_logger()

    html_path = os.path.join(root_folder, "target", html_file)
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return None

    form = utils.find_element(html_content, "form", {"id": form_id})
    if not form:
        logger.error(f"Form with id '{form_id}' not found in {html_file}")
        return None

    action = form.get("action") or ""
    action_url = urljoin(config.CONSULATE_BASE_URL, action) if action else config.CONSULATE_BASE_URL

    # Carry every non-submit field forward exactly as the browser would.
    fields = {}
    for element in form.find_all(["input", "select", "textarea"]):
        name = element.get("name")
        if not name or name.startswith("action:"):
            continue
        fields[name] = element.get("value") or ""

    if "jsessionid" not in action_url:
        logger.warning("Form action carries no jsessionid - session may not persist")

    logger.info(f"Form '{form_id}' posts to {action_url.split('?')[0]} with {len(fields)} fields")
    return {"action": action_url, "fields": fields}


def captcha_was_rejected(
    root_folder: str,
    response_html_file: str = "response.html"
) -> bool:
    """
    Check whether the portal rejected the submitted captcha solution.
    Used to report wrong solutions back to the solver for a refund.

    Args:
        root_folder: Root folder path
        response_html_file: Name of HTML file returned after submitting the captcha

    Returns:
        True if the page contains a captcha error message
    """
    html_path = os.path.join(root_folder, "target", response_html_file)

    content = utils.read_file_content(html_path)
    if not content:
        return False

    page_text = content.lower()
    return any(marker in page_text for marker in config.CAPTCHA_ERROR_MARKERS)


def extract_booking_time(
    root_folder: str,
    booking_html_file: str
) -> Optional[str]:
    """
    Extract booking time from appointment booking page.
    
    Args:
        root_folder: Root folder path
        booking_html_file: Name of HTML file containing booking info
        
    Returns:
        Booking time string or None if not found
    """
    logger = utils.setup_logger()
    
    html_path = os.path.join(root_folder, "target", booking_html_file)
    
    logger.info(f"Extracting booking time from {booking_html_file}")
    
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return None
    
    try:
        content_div = utils.find_element(html_content, "div", {"id": config.CONTENT_DIV_ID})
        if not content_div:
            logger.error("Content div not found in HTML")
            return None
        
        # Navigate to booking time element
        datetime_elem = content_div.find("div").find("fieldset").find_all("div")[1]
        booking_time = datetime_elem.text.strip()
        
        logger.info(f"Extracted booking time: {booking_time}")
        return booking_time
        
    except (AttributeError, IndexError) as e:
        logger.error(f"Error extracting booking time: {e}")
        return None


def extract_reschedule_url(
    root_folder: str,
    appointment_html_file: str
) -> Optional[str]:
    """
    Extract reschedule URL from appointment scheduling page.
    
    Args:
        root_folder: Root folder path
        appointment_html_file: Name of HTML file with appointment options
        
    Returns:
        URL string or None if not found
    """
    logger = utils.setup_logger()
    
    html_path = os.path.join(root_folder, "target", appointment_html_file)
    
    logger.info(f"Extracting reschedule URL from {appointment_html_file}")
    
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return None
    
    try:
        content_div = utils.find_element(html_content, "div", {"id": config.CONTENT_DIV_ID})
        if not content_div:
            logger.error("Content div not found in HTML")
            return None
        
        # Find all arrow links
        arrow_links = utils.find_all_elements(content_div, "a", {"class": config.ARROW_LINK_CLASS})
        
        if len(arrow_links) < 2:
            logger.error(f"Expected at least 2 arrow links, found {len(arrow_links)}")
            return None
        
        # First link is current month, second link is for rescheduling
        url = arrow_links[1].get("href")
        
        logger.info(f"Extracted reschedule URL: {url}")
        return url
        
    except (AttributeError, IndexError) as e:
        logger.error(f"Error extracting reschedule URL: {e}")
        return None


def extract_available_date(
    root_folder: str,
    response_html_file: str = "response.html"
) -> Optional[str]:
    """
    Extract available appointment date from response page.
    Auto-detects portal type and uses appropriate extraction logic.
    Uses the filtering logic from config to determine if date is acceptable.
    
    Args:
        root_folder: Root folder path
        response_html_file: Name of HTML file with available dates
        
    Returns:
        Available date string (format: DD.MM.YYYY) or None if no acceptable date found
    """
    logger = utils.setup_logger()
    
    html_path = os.path.join(root_folder, "target", response_html_file)
    
    logger.info(f"Extracting available date from {response_html_file}")
    
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return None
    
    try:
        # Detect portal type
        detector = booking_process.BookingProcessDetector()
        portal_type = detector.detect_portal_type(html_content)
        logger.info(f"Portal type: {portal_type} - {detector.get_portal_description()}")
        
        # Get layout-specific adapter
        adapter = booking_process.PortalLayoutAdapter(portal_type)
        
        # Extract dates using appropriate method
        available_date = adapter.extract_available_dates(html_content, config)
        
        if available_date:
            logger.info(f"Found acceptable date: {available_date}")
            return available_date
        else:
            logger.info("No acceptable date found in available appointments")
            return None
        
    except Exception as e:
        logger.error(f"Error extracting available date: {e}")
        return None
