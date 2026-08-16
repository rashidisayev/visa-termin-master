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


def extract_base64_image(html_content: Any, form_id: str, output_file: str) -> bool:
    """
    Extract base64 encoded image from HTML and save as JPG.
    
    Args:
        html_content: BeautifulSoup HTML object
        form_id: ID of the form containing the captcha
        output_file: Path to save the extracted image
        
    Returns:
        True if successful, False otherwise
    """
    logger = setup_logger()
    
    try:
        form = html_content.find("form", {"id": form_id})
        if not form:
            logger.error(f"Form with id '{form_id}' not found")
            return False
        
        # Navigate to the image style attribute
        captcha_div = form.find("div").find("captcha").find("div")
        if not captcha_div or 'style' not in captcha_div.attrs:
            logger.error("Captcha element not found or missing style attribute")
            return False
        
        image_style = captcha_div['style']
        
        # Extract base64 string from CSS background
        match = re.match(r"background:white url\('data:image/jpg;base64,(.+?)'\).*", image_style)
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
