# Tab Completion Setup Script for ClickUp Framework (Windows PowerShell)
# This script enables tab completion for the 'cum' and 'clickup' commands in PowerShell

Write-Host "ClickUp Framework - Tab Completion Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host ""

# Function to check if argcomplete is installed
function Test-ArgcompleteInstalled {
    try {
        python -c "import argcomplete" 2>$null
        return $true
    } catch {
        return $false
    }
}

# Check if argcomplete is installed
if (-not (Test-ArgcompleteInstalled)) {
    Write-Host "ERROR: argcomplete is not installed." -ForegroundColor Red
    Write-Host "Please install the clickup-framework package with:"
    Write-Host "  pip install -e ."
    Write-Host "or install argcomplete separately:"
    Write-Host "  pip install argcomplete"
    exit 1
}

# Get PowerShell profile path
$profilePath = $PROFILE.CurrentUserAllHosts
if (-not $profilePath) {
    $profilePath = $PROFILE
}

Write-Host "PowerShell profile: $profilePath"
Write-Host ""

# Create profile directory if it doesn't exist
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "Created profile directory: $profileDir"
}

# Create profile file if it doesn't exist
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
    Write-Host "Created profile file: $profilePath"
}

# Check if completion is already configured
$profileContent = Get-Content $profilePath -ErrorAction SilentlyContinue
$cumConfigured = $profileContent | Select-String "register-python-argcomplete cum"
$clickupConfigured = $profileContent | Select-String "register-python-argcomplete clickup"

# Add completion configuration
$needsReload = $false

if (-not $cumConfigured) {
    Write-Host "Adding completion for 'cum' command..." -ForegroundColor Green
    Add-Content $profilePath "`n# ClickUp Framework tab completion"
    Add-Content $profilePath 'Register-ArgumentCompleter -Native -CommandName cum -ScriptBlock {'
    Add-Content $profilePath '    param($wordToComplete, $commandAst, $cursorPosition)'
    Add-Content $profilePath '    $env:_ARGCOMPLETE = 1'
    Add-Content $profilePath '    $env:_ARGCOMPLETE_SUPPRESS_SPACE = 1'
    Add-Content $profilePath '    $env:COMP_LINE = $commandAst.ToString()'
    Add-Content $profilePath '    $env:COMP_POINT = $cursorPosition'
    Add-Content $profilePath '    cum 2>&1 | ForEach-Object {'
    Add-Content $profilePath '        if ($_ -is [System.Management.Automation.ErrorRecord]) {'
    Add-Content $profilePath '            return'
    Add-Content $profilePath '        }'
    Add-Content $profilePath '        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)'
    Add-Content $profilePath '    }'
    Add-Content $profilePath '}'
    $needsReload = $true
} else {
    Write-Host "Tab completion for 'cum' is already configured" -ForegroundColor Yellow
}

if (-not $clickupConfigured) {
    Write-Host "Adding completion for 'clickup' command..." -ForegroundColor Green
    if (-not $cumConfigured) {
        # Only add header comment if we didn't add it above
        Add-Content $profilePath "`n"
    }
    Add-Content $profilePath 'Register-ArgumentCompleter -Native -CommandName clickup -ScriptBlock {'
    Add-Content $profilePath '    param($wordToComplete, $commandAst, $cursorPosition)'
    Add-Content $profilePath '    $env:_ARGCOMPLETE = 1'
    Add-Content $profilePath '    $env:_ARGCOMPLETE_SUPPRESS_SPACE = 1'
    Add-Content $profilePath '    $env:COMP_LINE = $commandAst.ToString()'
    Add-Content $profilePath '    $env:COMP_POINT = $cursorPosition'
    Add-Content $profilePath '    clickup 2>&1 | ForEach-Object {'
    Add-Content $profilePath '        if ($_ -is [System.Management.Automation.ErrorRecord]) {'
    Add-Content $profilePath '            return'
    Add-Content $profilePath '        }'
    Add-Content $profilePath '        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)'
    Add-Content $profilePath '    }'
    Add-Content $profilePath '}'
    $needsReload = $true
} else {
    Write-Host "Tab completion for 'clickup' is already configured" -ForegroundColor Yellow
}

Write-Host ""
if ($needsReload) {
    Write-Host "✓ PowerShell completion configured!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To enable tab completion in your current session, run:" -ForegroundColor Cyan
    Write-Host "  . $profilePath"
    Write-Host ""
    Write-Host "Or restart PowerShell to load the new configuration."
} else {
    Write-Host "✓ Tab completion is already configured!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Try it out:" -ForegroundColor Cyan
Write-Host "  cum <TAB>          # See all available commands"
Write-Host "  cum task_<TAB>     # See all task commands"
Write-Host "  cum hierarchy <TAB> # See completion for command arguments"
