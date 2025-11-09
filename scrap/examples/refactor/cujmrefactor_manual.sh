#!/bin/bash

# cujmrefactor_manual.sh - Script to run the refactored ClickUp JSON Manager CLI
# This script uses the real FileManager for testing with actual files

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="python3"

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: $PYTHON_CMD could not be found"
    exit 1
fi

# Add the parent directory to PYTHONPATH to ensure modules can be found
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# Set manual mode environment variable to use real FileManager
export MANUAL_TEST=1

# Execute the refactored main module with all provided arguments
"$PYTHON_CMD" -m refactor.main "$@"

# Return the actual exit code
exit $? 