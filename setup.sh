#!/bin/bash

################################################################################
# Setup Script for Visa Appointment Helper - Refactored
# Installs dependencies and configures the project
################################################################################

set -e

echo "================================"
echo "Visa Appointment Helper Setup"
echo "================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $python_version"

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 6) else 1)'; then
    echo "ERROR: Python 3.6 or higher is required"
    exit 1
fi

# Install pip if needed
echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Upgrade pip
echo "Upgrading pip..."
pip3 install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x run.sh
chmod +x run_refactored.sh
chmod +x setup.sh
if [ -f "lib/deathbycaptcha" ]; then
    chmod +x lib/deathbycaptcha
fi

# Create directories
echo "Creating necessary directories..."
mkdir -p target log

# Check for setenv
if [ ! -f "setenv" ]; then
    echo ""
    echo "⚠️  WARNING: setenv file not found!"
    echo "Please create a setenv file with your configuration."
    echo ""
    echo "Example:"
    echo "  export ROOT_FOLDER=\"$(pwd)\""
    echo "  export TELEGRAM_BOT_TOKEN=\"your_token_here\""
    echo "  export TELEGRAM_CHAT_ID=\"your_chat_id_here\""
    echo "  export DBC_USERNAME=\"your_dbc_username\""
    echo "  export DBC_PASSWORD=\"your_dbc_password\""
else
    echo "✓ setenv file found"
fi

# Verify library structure
echo "Verifying library structure..."
if [ -f "lib/__init__.py" ] && [ -f "lib/config.py" ] && [ -f "lib/utils.py" ]; then
    echo "✓ Library structure looks good"
else
    echo "⚠️  WARNING: Some library files may be missing"
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit ./setenv with your configuration"
echo "2. Run: ./run_refactored.sh"
echo "3. Check logs: tail -f log/log.txt"
echo ""
echo "For more details, see REFACTORING.md"
