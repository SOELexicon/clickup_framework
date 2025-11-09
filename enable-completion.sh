#!/bin/bash
# Tab Completion Setup Script for ClickUp Framework
# This script enables tab completion for the 'cum' and 'clickup' commands

set -e

SHELL_NAME=$(basename "$SHELL")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "ClickUp Framework - Tab Completion Setup"
echo "=========================================="
echo ""
echo "Detected shell: $SHELL_NAME"
echo ""

# Function to check if argcomplete is installed
check_argcomplete() {
    if ! python3 -c "import argcomplete" 2>/dev/null; then
        echo "ERROR: argcomplete is not installed."
        echo "Please install the clickup-framework package with:"
        echo "  pip install -e ."
        echo "or install argcomplete separately:"
        echo "  pip install argcomplete"
        exit 1
    fi
}

# Function to add completion to bash
setup_bash() {
    BASH_RC="$HOME/.bashrc"

    # Check if already configured
    if grep -q "register-python-argcomplete cum" "$BASH_RC" 2>/dev/null; then
        echo "Tab completion for 'cum' is already configured in $BASH_RC"
    else
        echo "Adding completion configuration to $BASH_RC..."
        echo "" >> "$BASH_RC"
        echo "# ClickUp Framework tab completion" >> "$BASH_RC"
        echo 'eval "$(register-python-argcomplete cum)"' >> "$BASH_RC"
        echo "Added completion for 'cum' command"
    fi

    if grep -q "register-python-argcomplete clickup" "$BASH_RC" 2>/dev/null; then
        echo "Tab completion for 'clickup' is already configured in $BASH_RC"
    else
        echo 'eval "$(register-python-argcomplete clickup)"' >> "$BASH_RC"
        echo "Added completion for 'clickup' command"
    fi

    echo ""
    echo "✓ Bash completion configured!"
    echo "Please run: source $BASH_RC"
    echo "Or restart your terminal to enable tab completion."
}

# Function to add completion to zsh
setup_zsh() {
    ZSH_RC="$HOME/.zshrc"

    # Check if already configured
    if grep -q "register-python-argcomplete cum" "$ZSH_RC" 2>/dev/null; then
        echo "Tab completion for 'cum' is already configured in $ZSH_RC"
    else
        echo "Adding completion configuration to $ZSH_RC..."
        echo "" >> "$ZSH_RC"
        echo "# ClickUp Framework tab completion" >> "$ZSH_RC"
        echo "autoload -U bashcompinit" >> "$ZSH_RC"
        echo "bashcompinit" >> "$ZSH_RC"
        echo 'eval "$(register-python-argcomplete cum)"' >> "$ZSH_RC"
        echo "Added completion for 'cum' command"
    fi

    if grep -q "register-python-argcomplete clickup" "$ZSH_RC" 2>/dev/null; then
        echo "Tab completion for 'clickup' is already configured in $ZSH_RC"
    else
        echo 'eval "$(register-python-argcomplete clickup)"' >> "$ZSH_RC"
        echo "Added completion for 'clickup' command"
    fi

    echo ""
    echo "✓ Zsh completion configured!"
    echo "Please run: source $ZSH_RC"
    echo "Or restart your terminal to enable tab completion."
}

# Main execution
check_argcomplete

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
        echo "For bash, add this to your ~/.bashrc:"
        echo '  eval "$(register-python-argcomplete cum)"'
        echo '  eval "$(register-python-argcomplete clickup)"'
        echo ""
        echo "For zsh, add this to your ~/.zshrc:"
        echo "  autoload -U bashcompinit"
        echo "  bashcompinit"
        echo '  eval "$(register-python-argcomplete cum)"'
        echo '  eval "$(register-python-argcomplete clickup)"'
        exit 1
        ;;
esac

echo ""
echo "Tab completion setup complete!"
echo ""
echo "Try it out:"
echo "  cum <TAB>          # See all available commands"
echo "  cum task_<TAB>     # See all task commands"
echo "  cum hierarchy <TAB> # See completion for command arguments"
