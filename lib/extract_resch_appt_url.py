#!/usr/bin/env python3
"""
CLI wrapper to extract reschedule appointment URL from page.
Uses the refactored extractors module.
"""
import sys
import os

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import extractors, utils

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract_resch_appt_url.py <root_folder> <html_file>")
        sys.exit(1)
    
    root_folder = sys.argv[1]
    html_page_name = sys.argv[2]
    
    logger = utils.setup_logger()
    logger.info(f"Extracting reschedule URL from {html_page_name}")
    
    # Extract reschedule URL
    url = extractors.extract_reschedule_url(root_folder, html_page_name)
    
    if url:
        print(url)
        sys.exit(0)
    else:
        sys.exit(1)

