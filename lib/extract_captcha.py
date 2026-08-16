#!/usr/bin/env python3
"""
CLI wrapper to extract captcha image from HTML page.
Uses the refactored extractors module.
"""
import sys
import os

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import extractors, utils

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: extract_captcha.py <root_folder> <html_file> <captcha_selector_id>")
        sys.exit(1)
    
    root_folder = sys.argv[1]
    captcha_file = sys.argv[2]
    captcha_selector_id = sys.argv[3]
    
    logger = utils.setup_logger()
    logger.info(f"Extracting captcha from {captcha_file} with selector {captcha_selector_id}")
    
    # Extract captcha image
    success = extractors.extract_captcha_image(root_folder, captcha_file, captcha_selector_id)
    
    sys.exit(0 if success else 1)
