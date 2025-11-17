#!/bin/bash
# Alias Setup Script for ClickUp Framework
# This script enables convenient shell aliases for the 'cum' command

set -e

SHELL_NAME=$(basename "$SHELL")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "ClickUp Framework - Shell Alias Setup"
echo "======================================"
echo ""
echo "Detected shell: $SHELL_NAME"
echo ""

# Function to add aliases to bash
setup_bash() {
    BASH_RC="$HOME/.bashrc"

    # Check if already configured
    if grep -q "# ClickUp Framework aliases" "$BASH_RC" 2>/dev/null; then
        echo "ClickUp Framework aliases are already configured in $BASH_RC"
        echo ""
        echo "Configured aliases:"
        echo "  cud  - Quick shortcut for 'cum detail' (cum d)"
        echo "  cumd - Alternative for 'cum detail'"
    else
        echo "Adding alias configuration to $BASH_RC..."
        echo "" >> "$BASH_RC"
        echo "# ClickUp Framework aliases" >> "$BASH_RC"
        echo "alias cud='cum detail'" >> "$BASH_RC"
        echo "alias cumd='cum detail'" >> "$BASH_RC"
        echo ""
        echo "✓ Added aliases:"
        echo "  cud  - Quick shortcut for 'cum detail' (cum d)"
        echo "  cumd - Alternative for 'cum detail'"
    fi

    echo ""
    echo "✓ Bash aliases configured!"
    echo "Please run: source $BASH_RC"
    echo "Or restart your terminal to enable aliases."
}

# Function to add aliases to zsh
setup_zsh() {
    ZSH_RC="$HOME/.zshrc"

    # Check if already configured
    if grep -q "# ClickUp Framework aliases" "$ZSH_RC" 2>/dev/null; then
        echo "ClickUp Framework aliases are already configured in $ZSH_RC"
        echo ""
        echo "Configured aliases:"
        echo "  cud  - Quick shortcut for 'cum detail' (cum d)"
        echo "  cumd - Alternative for 'cum detail'"
    else
        echo "Adding alias configuration to $ZSH_RC..."
        echo "" >> "$ZSH_RC"
        echo "# ClickUp Framework aliases" >> "$ZSH_RC"
        echo "alias cud='cum detail'" >> "$ZSH_RC"
        echo "alias cumd='cum detail'" >> "$ZSH_RC"
        echo ""
        echo "✓ Added aliases:"
        echo "  cud  - Quick shortcut for 'cum detail' (cum d)"
        echo "  cumd - Alternative for 'cum detail'"
    fi

    echo ""
    echo "✓ Zsh aliases configured!"
    echo "Please run: source $ZSH_RC"
    echo "Or restart your terminal to enable aliases."
}

# Main execution
case "$SHELL_NAME" in
    bash)
        setup_bash
        ;;
    zsh)
        setup_zsh
        ;;
    *)
        echo "Unsupported shell: $SHELL_NAME"
        echo ""
        echo "Manual setup instructions:"
        echo ""
        echo "For bash, add this to your ~/.bashrc:"
        echo "  alias cud='cum detail'"
        echo "  alias cumd='cum detail'"
        echo ""
        echo "For zsh, add this to your ~/.zshrc:"
        echo "  alias cud='cum detail'"
        echo "  alias cumd='cum detail'"
        echo ""
        echo "For Windows PowerShell, add this to your profile:"
        echo "  Set-Alias cud 'cum detail'"
        echo "  Set-Alias cumd 'cum detail'"
        exit 1
        ;;
esac

echo ""
echo "Alias setup complete!"
echo ""
echo "Try it out:"
echo "  cud 86c6j1vr6       # View task details (short form)"
echo "  cumd current        # View current task details"
echo "  cud --help          # See detail command help"
echo ""
echo "Note: You can also use 'cum task <task_id>' as another alias for detail."
