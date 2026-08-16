#!/usr/bin/env python3
"""
CLI wrapper to extract available appointment date from response HTML.
Uses the refactored extractors module.
"""
import sys
import os

# Add parent directory to path to import lib modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import extractors, utils

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("NONE")
        sys.exit(0)
    
    root_folder = sys.argv[1]
    
    # Extract available date
    available_date = extractors.extract_available_date(root_folder)
    
    # Print result
    print("NONE" if available_date is None else available_date)
    
    sys.exit(0)
