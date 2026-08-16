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


def _field_label(element) -> str:
    """
    Read the human label sitting in front of a form field.

    Embassies add their own fields with meaningless names - Baku asks for the
    passport number as "fields[0].content" - so the label is the only thing
    that identifies what a field is actually for.

    Args:
        element: The input/select/textarea element

    Returns:
        Normalised label text, lowercased, or "" if none was found
    """
    text = element.find_previous(
        string=lambda s: s and s.strip() and len(s.strip()) > 3
    )
    return " ".join(text.strip().split()).lower() if text else ""


def _absolute(href: str) -> str:
    """
    Resolve a portal href against the application root.

    The portal writes its links relative to /rktermin/ (e.g.
    "extern/appointment_showDay.do?...") even though the page itself is served
    from /rktermin/extern/, so resolving against the current page URL would
    yield /rktermin/extern/extern/... and 404. Form actions are absolute paths
    and resolve correctly either way.
    """
    return urljoin(config.HOST.rstrip("/") + "/", href)


def extract_links(
    root_folder: str,
    html_file: str,
    contains: str
) -> list:
    """
    Collect every link on a saved page whose href contains a substring.

    The booking flow navigates by following the portal's own links
    (appointment_showDay.do, appointment_showForm.do) rather than by
    reconstructing URLs, so the session and its parameters survive intact.

    Args:
        root_folder: Root folder path
        html_file: Name of the saved HTML file
        contains: Substring the href must contain

    Returns:
        De-duplicated list of absolute URLs, in page order
    """
    logger = utils.setup_logger()

    html_content = utils.load_html_file(os.path.join(root_folder, "target", html_file))
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_file}")
        return []

    urls = []
    for anchor in html_content.find_all("a", href=True):
        href = anchor["href"]
        if contains in href:
            absolute = _absolute(href)
            if absolute not in urls:
                urls.append(absolute)

    logger.info(f"Found {len(urls)} link(s) matching '{contains}' in {html_file}")
    return urls


def pick_submit_action(submits: list) -> Optional[tuple]:
    """
    Choose the submit button that advances the booking.

    Struts dispatches on the submit button's name, and that name differs
    between flows (appointment_addAppointment when booking fresh,
    appointment_rebookAppointment when rescheduling) and between portal
    versions. Rather than hardcode one, discard the buttons that clearly do
    not advance and take the most likely of the rest.

    Args:
        submits: List of (name, value) tuples from the form

    Returns:
        (name, value) of the chosen button, or None
    """
    skip = ("refreshcaptcha", "choose_category", "cancel", "abbrechen", "back", "zurueck")
    candidates = [(n, v) for n, v in submits if not any(s in n.lower() for s in skip)]

    if not candidates:
        return None

    for keyword in ("add", "book", "save", "confirm", "submit"):
        for name, value in candidates:
            if keyword in name.lower():
                return name, value

    return candidates[0]


def extract_form_context(
    root_folder: str,
    html_file: str,
    form_id: Optional[str] = None
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
        form_id: ID of the form to read, or None to use the form holding
            the captcha (ids differ between steps and visa categories)

    Returns:
        Dict with 'action' (absolute URL), 'fields' (dict) and 'submits'
        (list of (name, value) tuples), or None
    """
    logger = utils.setup_logger()

    html_path = os.path.join(root_folder, "target", html_file)
    html_content = utils.load_html_file(html_path)
    if not html_content:
        logger.error(f"Failed to load HTML file: {html_path}")
        return None

    form = utils.find_captcha_form(html_content, form_id)
    if not form:
        logger.error(f"No form found in {html_file} (looked for id '{form_id}')")
        return None

    action = form.get("action") or ""
    action_url = _absolute(action) if action else config.CONSULATE_BASE_URL

    # Carry every non-submit field forward exactly as the browser would,
    # and record the submit buttons so the caller can pick the dispatch one.
    fields = {}
    submits = []
    labels = {}
    options = {}
    for element in form.find_all(["input", "select", "textarea"]):
        name = element.get("name")
        if not name:
            continue
        if element.get("type") == "submit" or name.startswith("action:"):
            submits.append((name, element.get("value") or ""))
            continue

        fields[name] = element.get("value") or ""
        labels[name] = _field_label(element)

        # Embassies define their own fields with generic names like
        # "fields[0].content", so the label is the only thing that says what a
        # field means. Dropdown values are recorded for the same reason.
        if element.name == "select":
            fields[name] = ""
            options[name] = [
                (opt.get("value") or "", opt.get_text(strip=True))
                for opt in element.find_all("option")
            ]

    if "jsessionid" not in action_url:
        logger.warning("Form action carries no jsessionid - session may not persist")

    logger.info(
        f"Form '{form.get('id') or '?'}' posts to {action_url.split('?')[0]} "
        f"with {len(fields)} fields and {len(submits)} submit button(s)"
    )
    return {
        "action": action_url,
        "fields": fields,
        "submits": submits,
        "labels": labels,
        "options": options,
    }


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
