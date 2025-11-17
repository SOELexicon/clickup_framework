#!/bin/bash
# SessionStart hook for ClickUp Framework
# Installs the framework so cum/cum-mcp commands are available in Claude Code sessions

set -euo pipefail

# Only run in Claude Code remote environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "🔧 Installing ClickUp Framework..."

# Install the package in editable mode with dev dependencies
# This installs all dependencies from pyproject.toml including:
# - requests, python-dotenv, argcomplete, mcp (runtime deps)
# - pytest, black, flake8, mypy (dev deps)
pip install -q -e ".[dev]" 2>&1 | grep -v "already satisfied" || true

# Verify installation
if command -v cum &> /dev/null && command -v cum-mcp &> /dev/null; then
    echo "✓ ClickUp Framework installed successfully"
    echo "  Commands available: cum, clickup, cum-mcp"
else
    echo "⚠ Installation completed but commands not found in PATH"
    exit 1
fi

# Set PYTHONPATH for development
echo "export PYTHONPATH=\"\${PYTHONPATH:+\$PYTHONPATH:}.\"" >> "$CLAUDE_ENV_FILE"

# Install Mermaid CLI (mmdc) for diagram generation
if ! command -v mmdc &> /dev/null; then
    echo "📊 Installing Mermaid CLI for diagram support..."
    npm install -g @mermaid-js/mermaid-cli 2>&1 | grep -v "npm WARN" || true
    if command -v mmdc &> /dev/null; then
        echo "✓ Mermaid CLI installed successfully"
    else
        echo "⚠ Mermaid CLI installation failed (puppeteer issues in sandbox)"
        echo "  Diagram generation will be skipped"
    fi
fi

echo "✓ Ready to use ClickUp Framework"
