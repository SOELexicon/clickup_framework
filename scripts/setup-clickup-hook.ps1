# ClickUp Framework SessionStart Hook Setup Script
# This script installs the SessionStart hook to automatically load ClickUp Framework in Claude Code sessions

Add-Type -AssemblyName System.Windows.Forms

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ClickUp Framework - SessionStart Hook Setup               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will set up a SessionStart hook in your project that:" -ForegroundColor Yellow
Write-Host "  • Automatically installs ClickUp Framework when Claude Code starts" -ForegroundColor White
Write-Host "  • Makes 'cum' and 'cum-mcp' commands available immediately" -ForegroundColor White
Write-Host "  • Installs dev dependencies (pytest, black, flake8, mypy)" -ForegroundColor White
Write-Host ""

# Show folder browser dialog
Write-Host "📁 Select the project folder where you want to add the hook..." -ForegroundColor Green
Start-Sleep -Milliseconds 500

$folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowser.Description = "Select the project folder to set up ClickUp Framework SessionStart hook"
$folderBrowser.ShowNewFolderButton = $false

$result = $folderBrowser.ShowDialog()

if ($result -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host ""
    Write-Host "❌ Cancelled by user" -ForegroundColor Red
    exit 1
}

$projectFolder = $folderBrowser.SelectedPath
Write-Host ""
Write-Host "✓ Selected folder: $projectFolder" -ForegroundColor Green
Write-Host ""

# Check if .git exists
if (-Not (Test-Path "$projectFolder/.git")) {
    Write-Host "⚠️  Warning: This doesn't appear to be a git repository" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "❌ Setup cancelled" -ForegroundColor Red
        exit 1
    }
}

# Confirm setup
Write-Host "This will create the following in $projectFolder :" -ForegroundColor Cyan
Write-Host "  • .claude/hooks/session-start.sh" -ForegroundColor White
Write-Host "  • .claude/settings.json (or update existing)" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed with setup? (y/n)"
if ($confirm -ne "y") {
    Write-Host "❌ Setup cancelled" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Setting up SessionStart hook..." -ForegroundColor Cyan

# Create .claude/hooks directory
$claudeHooksDir = "$projectFolder/.claude/hooks"
if (-Not (Test-Path $claudeHooksDir)) {
    New-Item -ItemType Directory -Path $claudeHooksDir -Force | Out-Null
    Write-Host "✓ Created .claude/hooks directory" -ForegroundColor Green
} else {
    Write-Host "✓ .claude/hooks directory already exists" -ForegroundColor Green
}

# Create session-start.sh
$hookScript = @'
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
'@

$hookPath = "$claudeHooksDir/session-start.sh"
Set-Content -Path $hookPath -Value $hookScript -NoNewline -Encoding UTF8
Write-Host "✓ Created session-start.sh" -ForegroundColor Green

# Create or update .claude/settings.json
$settingsPath = "$projectFolder/.claude/settings.json"
$settingsDir = "$projectFolder/.claude"

if (-Not (Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
}

$hookConfig = @{
    hooks = @{
        SessionStart = @(
            @{
                hooks = @(
                    @{
                        type = "command"
                        command = "`$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
                    }
                )
            }
        )
    }
}

if (Test-Path $settingsPath) {
    Write-Host "⚠️  .claude/settings.json already exists" -ForegroundColor Yellow

    try {
        $existingSettings = Get-Content $settingsPath -Raw | ConvertFrom-Json

        # Check if hooks already configured
        if ($existingSettings.hooks -and $existingSettings.hooks.SessionStart) {
            Write-Host "⚠️  SessionStart hook already configured in settings.json" -ForegroundColor Yellow
            $overwrite = Read-Host "Overwrite existing hook configuration? (y/n)"

            if ($overwrite -eq "y") {
                $existingSettings.hooks.SessionStart = $hookConfig.hooks.SessionStart
                $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
                Write-Host "✓ Updated .claude/settings.json" -ForegroundColor Green
            } else {
                Write-Host "⊘ Skipped updating settings.json" -ForegroundColor Yellow
            }
        } else {
            # Add hooks section if it doesn't exist
            if (-Not $existingSettings.hooks) {
                $existingSettings | Add-Member -NotePropertyName "hooks" -NotePropertyValue $hookConfig.hooks
            } else {
                $existingSettings.hooks | Add-Member -NotePropertyName "SessionStart" -NotePropertyValue $hookConfig.hooks.SessionStart
            }
            $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
            Write-Host "✓ Updated .claude/settings.json with SessionStart hook" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Error parsing existing settings.json: $_" -ForegroundColor Red
        $createNew = Read-Host "Create new settings.json? (existing will be backed up) (y/n)"

        if ($createNew -eq "y") {
            $backupPath = "$settingsPath.backup"
            Copy-Item $settingsPath $backupPath
            Write-Host "✓ Backed up existing settings to settings.json.backup" -ForegroundColor Green

            $hookConfig | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
            Write-Host "✓ Created new .claude/settings.json" -ForegroundColor Green
        } else {
            Write-Host "⊘ Skipped updating settings.json" -ForegroundColor Yellow
        }
    }
} else {
    $hookConfig | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "✓ Created .claude/settings.json" -ForegroundColor Green
}

# Create .env.example if it doesn't exist
$envExamplePath = "$projectFolder/.env.example"
if (-Not (Test-Path $envExamplePath)) {
    $envExample = @'
# ClickUp API Token
# Get your API token from: https://app.clickup.com/settings/apps
CLICKUP_API_TOKEN=pk_your_token_here

# Optional: Set default context (workspace, list, assignee)
# These can also be set using the clickup_set_current tool
# CLICKUP_DEFAULT_WORKSPACE=90151898946
# CLICKUP_DEFAULT_LIST=901517404278
# CLICKUP_DEFAULT_ASSIGNEE=68483025
'@

    Set-Content -Path $envExamplePath -Value $envExample -Encoding UTF8
    Write-Host "✓ Created .env.example template" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                     Setup Complete! ✓                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What was created:" -ForegroundColor Cyan
Write-Host "  • .claude/hooks/session-start.sh" -ForegroundColor White
Write-Host "  • .claude/settings.json" -ForegroundColor White
Write-Host "  • .env.example (if didn't exist)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Keep .claude/ local to this machine:" -ForegroundColor White
Write-Host "     Do not commit local assistant configuration with the CLI" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. (Optional) Create a .env file with your API token:" -ForegroundColor White
Write-Host "     Copy .env.example to .env and add your ClickUp API token" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Open this project in Claude Code on the web" -ForegroundColor White
Write-Host "     The hook will automatically install ClickUp Framework!" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Available Commands (after hook runs):" -ForegroundColor Cyan
Write-Host "  • cum h <list_id>           - View task hierarchy" -ForegroundColor White
Write-Host "  • cum tc <list_id> 'Name'   - Create task" -ForegroundColor White
Write-Host "  • cum set list <list_id>    - Set current list" -ForegroundColor White
Write-Host "  • cum show                  - Show current context" -ForegroundColor White
Write-Host "  • cum-mcp                   - Start MCP server (for testing)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Use /cum in Claude Code to see full command reference" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to open the folder
$openFolder = Read-Host "Open project folder in Explorer? (y/n)"
if ($openFolder -eq "y") {
    Start-Process explorer.exe $projectFolder
}

Write-Host ""
Write-Host "✨ Done! Happy coding with ClickUp Framework!" -ForegroundColor Green
Write-Host ""
