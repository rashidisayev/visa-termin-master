#!/bin/bash

################################################################################
# Visa Appointment Helper - Main Script
# Refactored for clarity and maintainability
# 
# This script coordinates the visa appointment checking workflow.
# Configuration should be set in ./setenv file or environment variables.
################################################################################

set -e  # Exit on error

# Load configuration
if [ ! -f "./setenv" ]; then
    echo "ERROR: setenv file not found. Please create it in the root directory."
    exit 1
fi

source ./setenv

# Validate required environment variables
if [ -z "$ROOT_FOLDER" ]; then
    echo "ERROR: ROOT_FOLDER not set in setenv"
    exit 1
fi

# CONSULATE_BASE_URL is optional - it defaults to the live portal.
# What actually has to be set is which appointment to watch, and the solver key.
if [ -z "$VISA_TARGETS" ] && { [ -z "$LOCATION_CODE" ] || [ -z "$REALM_ID" ] || [ -z "$CATEGORY_ID" ]; }; then
    echo "ERROR: set LOCATION_CODE, REALM_ID and CATEGORY_ID (or VISA_TARGETS) in setenv"
    exit 1
fi

if [ -z "$CAPTCHA_API_KEY" ]; then
    echo "ERROR: CAPTCHA_API_KEY not set in setenv (get one at https://2captcha.com)"
    exit 1
fi

cd "$ROOT_FOLDER"

# Set up logging
LOG_FILE="$ROOT_FOLDER/log/log.txt"
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Error handler
handle_error() {
    local line_number=$1
    log "ERROR: Script failed at line $line_number"
    exit 1
}

trap 'handle_error ${LINENO}' ERR

# Main workflow
main() {
    log "========================================"
    log "Visa Appointment Helper Started"
    log "========================================"
    
    # Clean up previous artifacts
    log "Cleaning up previous target artifacts..."
    rm -rf target
    mkdir -p target
    
    # Run the Python appointment handler
    log "Running appointment checking workflow..."
    
    # setenv already exports everything it sets, so the Python module sees it.
    # Only ROOT_FOLDER is re-exported here in case it was set on the command line.
    export ROOT_FOLDER

    # Determine auto-book mode
    AUTO_BOOK_FLAG=""
    if [ "$AUTO_BOOK" = "true" ] || [ "$AUTO_BOOK" = "1" ]; then
        AUTO_BOOK_FLAG="--auto-book"
    fi

    # Run Python handler. Guarded by "if" so that a non-zero exit does not trip
    # "set -e" before the result can be captured and logged.
    if python3 lib/appointment_handler.py "$ROOT_FOLDER" $AUTO_BOOK_FLAG; then
        RESULT=0
    else
        RESULT=$?
    fi

    log "========================================"
    log "Visa Appointment Helper Finished (Exit Code: $RESULT)"
    log "========================================"
    
    return $RESULT
}

# Run main workflow
main "$@"
exit $?
