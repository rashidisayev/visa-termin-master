"""
Utility functions for visa appointment helper.
Shared functionality for HTML parsing, file I/O, logging, and HTTP operations.
"""
import os
import logging
import re
import base64
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

# Note: BeautifulSoup is imported lazily in functions that need it
# to avoid hard dependency at module import time


def setup_logger(log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup and return a configured logger.
    
    Args:
        log_file: Path to log file. If None, uses config.LOG_FILE
        
    Returns:
        Configured logger instance
    """
    log_file = log_file or config.LOG_FILE
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(config.LOGGING_FORMAT, config.LOGGING_DATE_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def load_html_file(filepath: str) -> Optional[Any]:
    """
    Load and parse an HTML file.
    
    Args:
        filepath: Path to HTML file
        
    Returns:
        BeautifulSoup object or None if file not found
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        from bs4 import BeautifulSoup
        with open(filepath, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Error loading HTML file {filepath}: {e}")
        return None


def save_file(filepath: str, content: bytes, mode: str = 'wb') -> bool:
    """
    Save content to a file.
    
    Args:
        filepath: Path to save file
        content: Content to save (bytes or str)
        mode: File write mode ('wb' for binary, 'w' for text)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        if mode == 'wb' and isinstance(content, str):
            content = content.encode('utf-8')
        
        with open(filepath, mode) as f:
            f.write(content)
        return True
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Error saving file {filepath}: {e}")
        return False


def find_captcha_form(html_content: Any, form_id: Optional[str] = None) -> Optional[Any]:
    """
    Locate the form that holds the captcha.

    Prefers an explicit id, but falls back to whichever form contains a
    <captcha> element. The fallback matters because the form id differs
    between steps and between visa categories (C and D), so nothing in the
    booking flow can rely on a hardcoded id.

    Args:
        html_content: BeautifulSoup HTML object
        form_id: Optional form id to look for first

    Returns:
        The form element, or None
    """
    if form_id:
        form = html_content.find("form", {"id": form_id})
        if form:
            return form

    for form in html_content.find_all("form"):
        if form.find("captcha"):
            return form

    return None


def extract_base64_image(html_content: Any, form_id: Optional[str], output_file: str) -> bool:
    """
    Extract base64 encoded image from HTML and save as JPG.

    Args:
        html_content: BeautifulSoup HTML object
        form_id: ID of the form containing the captcha, or None to autodetect
        output_file: Path to save the extracted image

    Returns:
        True if successful, False otherwise
    """
    logger = setup_logger()

    try:
        form = find_captcha_form(html_content, form_id)
        if not form:
            logger.error(f"No captcha form found (looked for id '{form_id}')")
            return False

        captcha_div = form.find("captcha")
        captcha_div = captcha_div.find("div") if captcha_div else None
        if not captcha_div or 'style' not in captcha_div.attrs:
            logger.error("Captcha element not found or missing style attribute")
            return False

        image_style = captcha_div['style']
        
        # Extract base64 string from CSS background.
        # The portal declares the MIME type inconsistently (it currently sends
        # 'image/png' for what are actually JPEG bytes), so accept any type and
        # let the decoded data speak for itself.
        match = re.match(
            r"background:\s*\w+\s+url\('data:image/(?:jpe?g|png|gif);base64,(.+?)'\)",
            image_style
        )
        if not match:
            logger.error("Failed to extract base64 image from style attribute")
            return False
        
        base64_img = match.group(1)
        
        # Decode and save
        jpg_data = base64.b64decode(base64_img.encode('utf-8'))
        return save_file(output_file, jpg_data, mode='wb')
        
    except Exception as e:
        logger.error(f"Error extracting base64 image: {e}")
        return False


def find_element(html_content: Any, tag: str, attrs: Dict[str, str]) -> Optional[Any]:
    """
    Find an HTML element by tag and attributes.
    
    Args:
        html_content: BeautifulSoup HTML object
        tag: HTML tag name
        attrs: Dictionary of attributes to match
        
    Returns:
        Found element or None
    """
    return html_content.find(tag, attrs)


def find_all_elements(html_content: Any, tag: str, attrs: Dict[str, str]) -> list:
    """
    Find all HTML elements matching tag and attributes.
    
    Args:
        html_content: BeautifulSoup HTML object
        tag: HTML tag name
        attrs: Dictionary of attributes to match
        
    Returns:
        List of found elements
    """
    return html_content.find_all(tag, attrs)


def read_file_content(filepath: str) -> Optional[str]:
    """
    Read and return file content as string.
    
    Args:
        filepath: Path to file
        
    Returns:
        File content or None if not found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Error reading file {filepath}: {e}")
        return None
