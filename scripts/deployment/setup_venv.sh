#!/bin/bash
# Setup script for creating admin users - Creates virtual environment

echo "========================================="
echo "ClaimPlane Virtual Environment Setup"
echo "========================================="
echo ""

# Check if python3-venv is installed
if ! dpkg -l | grep -q python3.12-venv; then
    echo "Installing python3-venv package..."
    sudo apt install -y python3.12-venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install python3-venv"
        echo "Please run: sudo apt install -y python3.12-venv"
        exit 1
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv_scripts

# Activate and install dependencies
echo "Installing minimal dependencies for scripts..."
source venv_scripts/bin/activate
pip install --upgrade pip
pip install -r requirements-scripts.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To use it:"
echo "  1. Activate: source venv_scripts/bin/activate"
echo "  2. Run script: python scripts/create_admin_user.py"
echo "  3. Deactivate: deactivate"
echo ""
