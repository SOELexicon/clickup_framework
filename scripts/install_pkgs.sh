#!/bin/bash
# Session startup script for Claude Code
# Automatically installs clickup_framework package

echo "Installing clickup_framework package..."

pip install --upgrade --force-reinstall git+https://github.com/SOELexicon/clickup_framework.git

if [ $? -eq 0 ]; then
    echo "✓ clickup_framework installed successfully"
else
    echo "✗ Failed to install clickup_framework"
    exit 1
fi
