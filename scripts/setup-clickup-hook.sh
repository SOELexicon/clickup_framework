#!/bin/bash
# ClickUp Framework SessionStart Hook Setup Script
# This script installs the SessionStart hook to automatically load ClickUp Framework in Claude Code sessions

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   ClickUp Framework - SessionStart Hook Setup               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}This script will set up a SessionStart hook in your project that:${NC}"
echo -e "${WHITE}  • Automatically installs ClickUp Framework when Claude Code starts${NC}"
echo -e "${WHITE}  • Makes 'cum' and 'cum-mcp' commands available immediately${NC}"
echo -e "${WHITE}  • Installs dev dependencies (pytest, black, flake8, mypy)${NC}"
echo ""

# Prompt for project folder
echo -e "${GREEN}📁 Enter the full path to your project folder:${NC}"
read -r PROJECT_FOLDER

# Expand ~ to home directory
PROJECT_FOLDER="${PROJECT_FOLDER/#\~/$HOME}"

# Check if folder exists
if [ ! -d "$PROJECT_FOLDER" ]; then
    echo -e "${RED}❌ Error: Folder does not exist: $PROJECT_FOLDER${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Selected folder: $PROJECT_FOLDER${NC}"
echo ""

# Check if .git exists
if [ ! -d "$PROJECT_FOLDER/.git" ]; then
    echo -e "${YELLOW}⚠️  Warning: This doesn't appear to be a git repository${NC}"
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo -e "${RED}❌ Setup cancelled${NC}"
        exit 1
    fi
fi

# Confirm setup
echo -e "${CYAN}This will create the following in $PROJECT_FOLDER :${NC}"
echo -e "${WHITE}  • .claude/hooks/session-start.sh${NC}"
echo -e "${WHITE}  • .claude/settings.json (or update existing)${NC}"
echo ""

read -p "Proceed with setup? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo -e "${RED}❌ Setup cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}🔧 Setting up SessionStart hook...${NC}"

# Create .claude/hooks directory
CLAUDE_HOOKS_DIR="$PROJECT_FOLDER/.claude/hooks"
if [ ! -d "$CLAUDE_HOOKS_DIR" ]; then
    mkdir -p "$CLAUDE_HOOKS_DIR"
    echo -e "${GREEN}✓ Created .claude/hooks directory${NC}"
else
    echo -e "${GREEN}✓ .claude/hooks directory already exists${NC}"
fi

# Create session-start.sh
HOOK_PATH="$CLAUDE_HOOKS_DIR/session-start.sh"
cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash
# SessionStart hook for ClickUp Framework
# Installs the framework so cum/cum-mcp commands are available in Claude Code sessions

set -euo pipefail

# Only run in Claude Code remote environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "🔧 Installing ClickUp Framework..."

# Install ClickUp Framework from GitHub
pip install -q git+https://github.com/SOELexicon/clickup_framework.git 2>&1 | grep -v "already satisfied" || true

# Verify installation
if command -v cum &> /dev/null && command -v cum-mcp &> /dev/null; then
    echo "✓ ClickUp Framework installed successfully"
    echo "  Commands available: cum, clickup, cum-mcp"
else
    echo "⚠ Installation completed but commands not found in PATH"
    exit 1
fi

echo "✓ Ready to use ClickUp Framework"
EOF

chmod +x "$HOOK_PATH"
echo -e "${GREEN}✓ Created session-start.sh${NC}"

# Create or update .claude/settings.json
SETTINGS_PATH="$PROJECT_FOLDER/.claude/settings.json"
SETTINGS_DIR="$PROJECT_FOLDER/.claude"

if [ ! -d "$SETTINGS_DIR" ]; then
    mkdir -p "$SETTINGS_DIR"
fi

HOOK_CONFIG='{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}'

if [ -f "$SETTINGS_PATH" ]; then
    echo -e "${YELLOW}⚠️  .claude/settings.json already exists${NC}"

    # Try to parse existing JSON
    if command -v jq &> /dev/null; then
        # Check if SessionStart hook already exists
        if jq -e '.hooks.SessionStart' "$SETTINGS_PATH" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  SessionStart hook already configured in settings.json${NC}"
            read -p "Overwrite existing hook configuration? (y/n): " OVERWRITE

            if [ "$OVERWRITE" = "y" ]; then
                # Use jq to update SessionStart
                TMP_FILE=$(mktemp)
                jq '.hooks.SessionStart = [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"}]}]' "$SETTINGS_PATH" > "$TMP_FILE"
                mv "$TMP_FILE" "$SETTINGS_PATH"
                echo -e "${GREEN}✓ Updated .claude/settings.json${NC}"
            else
                echo -e "${YELLOW}⊘ Skipped updating settings.json${NC}"
            fi
        else
            # Add SessionStart hook to existing settings
            TMP_FILE=$(mktemp)
            jq '.hooks.SessionStart = [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"}]}]' "$SETTINGS_PATH" > "$TMP_FILE"
            mv "$TMP_FILE" "$SETTINGS_PATH"
            echo -e "${GREEN}✓ Updated .claude/settings.json with SessionStart hook${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  jq not installed, cannot safely merge settings${NC}"
        read -p "Backup and replace settings.json? (y/n): " REPLACE

        if [ "$REPLACE" = "y" ]; then
            cp "$SETTINGS_PATH" "$SETTINGS_PATH.backup"
            echo -e "${GREEN}✓ Backed up existing settings to settings.json.backup${NC}"

            echo "$HOOK_CONFIG" > "$SETTINGS_PATH"
            echo -e "${GREEN}✓ Created new .claude/settings.json${NC}"
        else
            echo -e "${YELLOW}⊘ Skipped updating settings.json${NC}"
            echo -e "${YELLOW}  You'll need to manually add the SessionStart hook${NC}"
        fi
    fi
else
    echo "$HOOK_CONFIG" > "$SETTINGS_PATH"
    echo -e "${GREEN}✓ Created .claude/settings.json${NC}"
fi

# Create .env.example if it doesn't exist
ENV_EXAMPLE_PATH="$PROJECT_FOLDER/.env.example"
if [ ! -f "$ENV_EXAMPLE_PATH" ]; then
    cat > "$ENV_EXAMPLE_PATH" << 'EOF'
# ClickUp API Token
# Get your API token from: https://app.clickup.com/settings/apps
CLICKUP_API_TOKEN=pk_your_token_here

# Optional: Set default context (workspace, list, assignee)
# These can also be set using the clickup_set_current tool
# CLICKUP_DEFAULT_WORKSPACE=90151898946
# CLICKUP_DEFAULT_LIST=901517404278
# CLICKUP_DEFAULT_ASSIGNEE=68483025
EOF

    echo -e "${GREEN}✓ Created .env.example template${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                     Setup Complete! ✓                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📋 What was created:${NC}"
echo -e "${WHITE}  • .claude/hooks/session-start.sh${NC}"
echo -e "${WHITE}  • .claude/settings.json${NC}"
echo -e "${WHITE}  • .env.example (if didn't exist)${NC}"
echo ""
echo -e "${CYAN}🚀 Next Steps:${NC}"
echo -e "${WHITE}  1. Commit these files to your repository:${NC}"
echo -e "${GRAY}     git add .claude/${NC}"
echo -e "${GRAY}     git commit -m 'Add ClickUp Framework SessionStart hook'${NC}"
echo -e "${GRAY}     git push${NC}"
echo ""
echo -e "${WHITE}  2. (Optional) Create a .env file with your API token:${NC}"
echo -e "${GRAY}     Copy .env.example to .env and add your ClickUp API token${NC}"
echo ""
echo -e "${WHITE}  3. Open this project in Claude Code on the web${NC}"
echo -e "${GRAY}     The hook will automatically install ClickUp Framework!${NC}"
echo ""
echo -e "${CYAN}📖 Available Commands (after hook runs):${NC}"
echo -e "${WHITE}  • cum h <list_id>           - View task hierarchy${NC}"
echo -e "${WHITE}  • cum tc <list_id> 'Name'   - Create task${NC}"
echo -e "${WHITE}  • cum set list <list_id>    - Set current list${NC}"
echo -e "${WHITE}  • cum show                  - Show current context${NC}"
echo -e "${WHITE}  • cum-mcp                   - Start MCP server (for testing)${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: Use /cum in Claude Code to see full command reference${NC}"
echo ""
echo -e "${GREEN}✨ Done! Happy coding with ClickUp Framework!${NC}"
echo ""
