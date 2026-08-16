#!/usr/bin/env python3
"""
CLI wrapper to extract booking time from appointment page.
Uses the refactored extractors module.
"""
import sys
import os

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import extractors, utils

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract_booking_time.py <root_folder> <html_file>")
        sys.exit(1)
    
    root_folder = sys.argv[1]
    booking_html_file = sys.argv[2]
    
    logger = utils.setup_logger()
    logger.info(f"Extracting booking time from {booking_html_file}")
    
    # Extract booking time
    booking_time = extractors.extract_booking_time(root_folder, booking_html_file)
    
    if booking_time:
        print(booking_time)
        sys.exit(0)
    else:
        sys.exit(1)