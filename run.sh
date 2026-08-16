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

if [ -z "$CONSULATE_BASE_URL" ]; then
    echo "ERROR: CONSULATE_BASE_URL not set in setenv"
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
    
    # Export variables for Python module
    export ROOT_FOLDER
    export CONSULATE_BASE_URL
    export RESCHEDULING_BASE_URL
    export BOOKING_BASE_URL
    export HOST
    export CONSULATE_DETAILS
    export LOCATION_CODE
    export REALM_ID
    export CATEGORY_ID
    export RESCHEDULING_TOKEN
    export TELEGRAM_BOT_TOKEN
    export TELEGRAM_CHAT_ID
    export DBC_USERNAME
    export DBC_PASSWORD
    
    # Determine auto-book mode
    AUTO_BOOK_FLAG=""
    if [ "$AUTO_BOOK" = "true" ] || [ "$AUTO_BOOK" = "1" ]; then
        AUTO_BOOK_FLAG="--auto-book"
    fi
    
    # Run Python handler
    python3 lib/appointment_handler.py "$ROOT_FOLDER" $AUTO_BOOK_FLAG
    RESULT=$?
    
    log "========================================"
    log "Visa Appointment Helper Finished (Exit Code: $RESULT)"
    log "========================================"
    
    return $RESULT
}

# Run main workflow
main "$@"
exit $?
