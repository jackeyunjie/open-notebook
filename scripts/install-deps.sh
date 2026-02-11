#!/bin/bash
# Install additional dependencies for Skill system
# This script runs on container startup to ensure all required packages are installed

echo "Checking and installing Skill system dependencies..."

# Check if APScheduler is installed
if ! /app/.venv/bin/python -c "import apscheduler" 2>/dev/null; then
    echo "Installing APScheduler..."
    /app/.venv/bin/pip install apscheduler tzlocal
fi

# Check if browser-use is installed
if ! /app/.venv/bin/python -c "import browser_use" 2>/dev/null; then
    echo "Installing browser-use..."
    /app/.venv/bin/pip install browser-use>=0.1.40
fi

echo "Dependency check complete!"
