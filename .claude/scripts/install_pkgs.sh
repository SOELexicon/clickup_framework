#!/bin/bash
# Session startup script for Claude Code
# Automatically installs clickup_framework package

echo "Installing clickup_framework package..."
pip install -e . --quiet

if [ $? -eq 0 ]; then
    echo "✓ clickup_framework installed successfully"
else
    echo "✗ Failed to install clickup_framework"
    exit 1
fi
