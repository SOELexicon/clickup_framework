<#
╔══════════════════════════════════════════════════════════════════════════════╗
║ File System Monitor with ProcMon Integration                                  ║
║ Author: Craig | Version: 3.0.0 | Created: 2025                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    Advanced file system monitoring using Sysinternals Process Monitor (ProcMon)
    for accurate process tracking and detailed file operation information.

FEATURES:
    - Real-time process identification using ProcMon
    - Detailed process information (path, command line, user, company)
    - File operation details (size, attributes, result)
    - Automatic ProcMon download if not present
    - Enhanced filtering and output formatting
    - Process statistics and summaries

REQUIREMENTS:
    - Windows PowerShell 5.1+ or PowerShell 7+
    - Administrator privileges (for ProcMon)
    - Internet connection (for auto-download)
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$MonitorPath,

    [Parameter()]
    [switch]$SkipProcMonDownload,

    [Parameter()]
    [int]$BufferSize = 1000,

    [Parameter()]
    [switch]$ShowStackTrace
)

# Script configuration
$Script:Config = @{
    ProcMonUrl = "https://download.sysinternals.com/files/ProcessMonitor.zip"
    ProcMonPath = "$env:TEMP\ProcMon"
    ProcMonExe = "$env:TEMP\ProcMon\Procmon64.exe"
    ProcMonConfig = "$env:TEMP\ProcMon\FileMonitor.pmc"
    OutputPath = "$env:TEMP\ProcMon\capture.csv"
    BufferSize = $BufferSize
    ShowStackTrace = $ShowStackTrace
}

# State management
$Script:State = @{
    ANSISupported = $false
    MonitorPath = $MonitorPath
    ProcMonProcess = $null
    EventLog = [System.Collections.ArrayList]::new()
    ProcessCache = @{}
    Statistics = @{
        TotalEvents = 0
        EventTypes = @{}
        ProcessActivity = @{}
        FileTypes = @{}
    }
    MonitorActive = $false
    StartTime = $null
}

# Colors and symbols
$Script:Colors = @{}
$Script:Symbols = @{}

# Set console encoding
try {
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Ignore errors in non-console environments
}

function Test-IsAdministrator {
    <#
    .SYNOPSIS
        Checks if running with administrator privileges
    #>
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        return $false
    }
}

function Test-ANSISupport {
    <#
    .SYNOPSIS
        Detects terminal ANSI support
    #>
    try {
        if ($env:WT_SESSION -or $env:TERM_PROGRAM -eq 'vscode') {
            return $true
        }

        if ($PSVersionTable.PSVersion.Major -ge 7) {
            return $Host.UI.SupportsVirtualTerminal
        }

        # Try to enable VT processing on Windows 10+
        if ([System.Environment]::OSVersion.Version.Major -ge 10) {
            $signature = @'
                [DllImport("kernel32.dll", SetLastError = true)]
                public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint mode);
                [DllImport("kernel32.dll", SetLastError = true)]
                public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint mode);
                [DllImport("kernel32.dll", SetLastError = true)]
                public static extern IntPtr GetStdHandle(int handle);
'@
            $type = Add-Type -MemberDefinition $signature -Name ConsoleUtils -Namespace Win32 -PassThru -ErrorAction SilentlyContinue
            if ($type) {
                $handle = $type::GetStdHandle(-11) # STD_OUTPUT_HANDLE
                $mode = 0
                if ($type::GetConsoleMode($handle, [ref]$mode)) {
                    $ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                    $newMode = $mode -bor $ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    return $type::SetConsoleMode($handle, $newMode)
                }
            }
        }

        return $false
    }
    catch {
        return $false
    }
}

function Initialize-ColorScheme {
    <#
    .SYNOPSIS
        Initialize color codes
    #>
    $Script:State.ANSISupported = Test-ANSISupport

    if ($Script:State.ANSISupported) {
        $Script:Colors = @{
            Reset       = "`e[0m"
            Bold        = "`e[1m"
            Dim         = "`e[2m"
            Italic      = "`e[3m"
            Underline   = "`e[4m"

            # Foreground colors
            Black       = "`e[30m"
            Red         = "`e[91m"
            Green       = "`e[92m"
            Yellow      = "`e[93m"
            Blue        = "`e[94m"
            Magenta     = "`e[95m"
            Cyan        = "`e[96m"
            White       = "`e[97m"
            Gray        = "`e[90m"

            # Special combinations
            Success     = "`e[92m"
            Error       = "`e[91m"
            Warning     = "`e[93m"
            Info        = "`e[96m"
            Process     = "`e[95m"
            Path        = "`e[94m"
            Detail      = "`e[90m"
        }
    }
    else {
        # Empty strings for no ANSI support
        $Script:Colors = @{
            Reset = ""; Bold = ""; Dim = ""; Italic = ""; Underline = ""
            Black = ""; Red = ""; Green = ""; Yellow = ""
            Blue = ""; Magenta = ""; Cyan = ""; White = ""; Gray = ""
            Success = ""; Error = ""; Warning = ""; Info = ""
            Process = ""; Path = ""; Detail = ""
        }
    }
}

function Initialize-Symbols {
    <#
    .SYNOPSIS
        Initialize UTF-8 symbols
    #>
    $Script:Symbols = @{
        # File operations
        Read        = "📖"
        Write       = "✏️"
        Create      = "✨"
        Delete      = "🗑️"
        Rename      = "📝"
        QueryInfo   = "🔍"
        SetInfo     = "⚙️"

        # Status
        Success     = "✅"
        Error       = "❌"
        Warning     = "⚠️"
        Info        = "ℹ️"

        # Process
        Process     = "🔧"
        User        = "👤"
        System      = "💻"

        # UI
        Arrow       = "→"
        Bullet      = "•"
        LineH       = "─"
        LineV       = "│"
    }
}

function Install-ProcMon {
    <#
    .SYNOPSIS
        Downloads and extracts ProcMon if not present
    #>
    if (Test-Path $Script:Config.ProcMonExe) {
        Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) ProcMon found at: $($Script:Config.ProcMonExe)$($Script:Colors.Reset)"
        return $true
    }

    if ($SkipProcMonDownload) {
        Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) ProcMon not found and auto-download disabled$($Script:Colors.Reset)"
        return $false
    }

    Write-Host "$($Script:Colors.Warning)$($Script:Symbols.Warning) ProcMon not found. Downloading from Sysinternals...$($Script:Colors.Reset)"

    try {
        # Create directory
        if (!(Test-Path $Script:Config.ProcMonPath)) {
            New-Item -ItemType Directory -Path $Script:Config.ProcMonPath -Force | Out-Null
        }

        $zipPath = "$($Script:Config.ProcMonPath)\ProcessMonitor.zip"

        # Download
        Write-Host "$($Script:Colors.Info)   Downloading ProcessMonitor.zip...$($Script:Colors.Reset)"
        Invoke-WebRequest -Uri $Script:Config.ProcMonUrl -OutFile $zipPath -UseBasicParsing

        # Extract
        Write-Host "$($Script:Colors.Info)   Extracting...$($Script:Colors.Reset)"
        Expand-Archive -Path $zipPath -DestinationPath $Script:Config.ProcMonPath -Force

        # Clean up
        Remove-Item $zipPath -Force

        if (Test-Path $Script:Config.ProcMonExe) {
            Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) ProcMon installed successfully$($Script:Colors.Reset)"

            # Accept EULA
            & $Script:Config.ProcMonExe /AcceptEula /Terminate 2>$null

            return $true
        }
    }
    catch {
        Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) Failed to download ProcMon: $_$($Script:Colors.Reset)"
        return $false
    }

    return $false
}

function New-ProcMonConfig {
    <#
    .SYNOPSIS
        Creates ProcMon configuration file with filters
    #>
    param([string]$Path)

    # Create a basic PMC configuration XML
    $configXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<Procmon>
    <Options>
        <Columns>
            <Column>Process Name</Column>
            <Column>PID</Column>
            <Column>Operation</Column>
            <Column>Path</Column>
            <Column>Result</Column>
            <Column>Detail</Column>
            <Column>User</Column>
            <Column>Process Path</Column>
            <Column>Command Line</Column>
            <Column>Company</Column>
            <Column>Description</Column>
            <Column>Version</Column>
            <Column>Architecture</Column>
            <Column>Session</Column>
            <Column>Date &amp; Time</Column>
        </Columns>
    </Options>
    <Filter>
        <Rule>
            <Column>Path</Column>
            <Relation>begins with</Relation>
            <Value>$Path</Value>
            <Action>Include</Action>
        </Rule>
        <Rule>
            <Column>Operation</Column>
            <Relation>is</Relation>
            <Value>Process and Thread Activity</Value>
            <Action>Exclude</Action>
        </Rule>
        <Rule>
            <Column>Operation</Column>
            <Relation>is</Relation>
            <Value>Registry</Value>
            <Action>Exclude</Action>
        </Rule>
        <Rule>
            <Column>Process Name</Column>
            <Relation>is</Relation>
            <Value>Procmon64.exe</Value>
            <Action>Exclude</Action>
        </Rule>
        <Rule>
            <Column>Process Name</Column>
            <Relation>is</Relation>
            <Value>Procmon.exe</Value>
            <Action>Exclude</Action>
        </Rule>
        <Rule>
            <Column>Process Name</Column>
            <Relation>is</Relation>
            <Value>powershell.exe</Value>
            <Action>Exclude</Action>
        </Rule>
        <Rule>
            <Column>Process Name</Column>
            <Relation>is</Relation>
            <Value>pwsh.exe</Value>
            <Action>Exclude</Action>
        </Rule>
    </Filter>
</Procmon>
"@

    $configXml | Out-File -FilePath $Script:Config.ProcMonConfig -Encoding UTF8
}

function Start-ProcMon {
    <#
    .SYNOPSIS
        Starts ProcMon with appropriate parameters
    #>
    param([string]$Path)

    try {
        # Create configuration
        New-ProcMonConfig -Path $Path

        # Build ProcMon arguments
        $procmonArgs = @(
            "/AcceptEula"
            "/Quiet"
            "/Minimized"
            "/BackingFile", $Script:Config.OutputPath
            "/LoadConfig", $Script:Config.ProcMonConfig
        )

        Write-Host "$($Script:Colors.Info)$($Script:Symbols.Info) Starting ProcMon in background...$($Script:Colors.Reset)"

        # Start ProcMon
        $Script:State.ProcMonProcess = Start-Process -FilePath $Script:Config.ProcMonExe `
            -ArgumentList $procmonArgs `
            -WindowStyle Hidden `
            -PassThru

        Start-Sleep -Seconds 2  # Give ProcMon time to initialize

        if ($Script:State.ProcMonProcess -and !$Script:State.ProcMonProcess.HasExited) {
            Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) ProcMon started (PID: $($Script:State.ProcMonProcess.Id))$($Script:Colors.Reset)"
            return $true
        }
        else {
            Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) ProcMon failed to start$($Script:Colors.Reset)"
            return $false
        }
    }
    catch {
        Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) Error starting ProcMon: $_$($Script:Colors.Reset)"
        return $false
    }
}

function Stop-ProcMon {
    <#
    .SYNOPSIS
        Stops ProcMon and exports data
    #>
    try {
        if ($Script:State.ProcMonProcess -and !$Script:State.ProcMonProcess.HasExited) {
            Write-Host "$($Script:Colors.Warning)$($Script:Symbols.Warning) Stopping ProcMon...$($Script:Colors.Reset)"

            # Export to CSV first
            $csvPath = "$($Script:Config.ProcMonPath)\export.csv"
            & $Script:Config.ProcMonExe /OpenLog $Script:Config.OutputPath /SaveAs $csvPath /SaveAsCSV /Quiet 2>$null

            # Terminate ProcMon
            & $Script:Config.ProcMonExe /Terminate 2>$null
            Stop-Process -Id $Script:State.ProcMonProcess.Id -Force -ErrorAction SilentlyContinue

            Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) ProcMon stopped$($Script:Colors.Reset)"

            # Parse final CSV if exists
            if (Test-Path $csvPath) {
                Parse-ProcMonCSV -Path $csvPath -ShowSummary
                Remove-Item $csvPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
    catch {
        Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) Error stopping ProcMon: $_$($Script:Colors.Reset)"
    }

    # Cleanup temp files
    if (Test-Path $Script:Config.OutputPath) {
        Remove-Item $Script:Config.OutputPath -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $Script:Config.ProcMonConfig) {
        Remove-Item $Script:Config.ProcMonConfig -Force -ErrorAction SilentlyContinue
    }
}

function Parse-ProcMonCSV {
    <#
    .SYNOPSIS
        Parses ProcMon CSV output
    #>
    param(
        [string]$Path,
        [switch]$ShowSummary
    )

    if (!(Test-Path $Path)) {
        return
    }

    try {
        $csv = Import-Csv -Path $Path

        foreach ($event in $csv) {
            # Skip if not in our monitored path
            if ($event.Path -notlike "$($Script:State.MonitorPath)*") {
                continue
            }

            # Update statistics
            $Script:State.Statistics.TotalEvents++

            # Track by operation
            if (!$Script:State.Statistics.EventTypes[$event.Operation]) {
                $Script:State.Statistics.EventTypes[$event.Operation] = 0
            }
            $Script:State.Statistics.EventTypes[$event.Operation]++

            # Track by process
            $processKey = "$($event.'Process Name') [$($event.PID)]"
            if (!$Script:State.Statistics.ProcessActivity[$processKey]) {
                $Script:State.Statistics.ProcessActivity[$processKey] = @{
                    Count = 0
                    User = $event.User
                    Path = $event.'Image/Path'
                    Company = $event.Company
                }
            }
            $Script:State.Statistics.ProcessActivity[$processKey].Count++

            # Add to event log
            [void]$Script:State.EventLog.Add($event)
        }

        if ($ShowSummary) {
            Show-Statistics
        }
    }
    catch {
        Write-Host "$($Script:Colors.Error)Error parsing CSV: $_$($Script:Colors.Reset)"
    }
}

function Watch-FileSystem {
    <#
    .SYNOPSIS
        Real-time monitoring using FileSystemWatcher and ProcMon logs
    #>
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $Script:State.MonitorPath
    $watcher.IncludeSubdirectories = $true
    $watcher.EnableRaisingEvents = $true

    $action = {
        $path = $Event.SourceEventArgs.FullPath
        $changeType = $Event.SourceEventArgs.ChangeType
        $timestamp = Get-Date

        # Query ProcMon for recent events on this file
        $csvPath = "$($Script:Config.ProcMonPath)\temp_export.csv"

        # Export recent events
        & $Script:Config.ProcMonExe /OpenLog $Script:Config.OutputPath /SaveAs $csvPath /SaveAsCSV /Quiet 2>$null

        if (Test-Path $csvPath) {
            $events = Import-Csv -Path $csvPath -ErrorAction SilentlyContinue |
                      Where-Object { $_.Path -eq $path } |
                      Select-Object -Last 5

            if ($events) {
                foreach ($evt in $events) {
                    Format-ProcMonEvent -Event $evt -ChangeType $changeType
                }
            }
            else {
                # Fallback to simple output if no ProcMon data
                Format-SimpleEvent -Path $path -ChangeType $changeType -Timestamp $timestamp
            }

            Remove-Item $csvPath -Force -ErrorAction SilentlyContinue
        }
        else {
            Format-SimpleEvent -Path $path -ChangeType $changeType -Timestamp $timestamp
        }
    }

    # Register events
    Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Renamed" -Action {
        $oldPath = $Event.SourceEventArgs.OldFullPath
        $newPath = $Event.SourceEventArgs.FullPath
        Format-SimpleEvent -Path "$oldPath → $newPath" -ChangeType "Renamed" -Timestamp (Get-Date)
    } | Out-Null

    return $watcher
}

function Format-ProcMonEvent {
    <#
    .SYNOPSIS
        Formats ProcMon event for display
    #>
    param($Event, $ChangeType)

    $symbol = switch ($Event.Operation) {
        "CreateFile"     { $Script:Symbols.Create }
        "WriteFile"      { $Script:Symbols.Write }
        "ReadFile"       { $Script:Symbols.Read }
        "DeleteFile"     { $Script:Symbols.Delete }
        "QueryDirectory" { $Script:Symbols.QueryInfo }
        "SetDispositionInformationFile" { $Script:Symbols.Delete }
        default          { $Script:Symbols.Info }
    }

    $color = switch ($Event.Result) {
        "SUCCESS" { $Script:Colors.Green }
        "END OF FILE" { $Script:Colors.Yellow }
        "NAME NOT FOUND" { $Script:Colors.Red }
        default { $Script:Colors.White }
    }

    # Parse timestamp
    $timestamp = [DateTime]::Parse($Event.'Date & Time')

    # Build output
    Write-Host ""
    Write-Host "$($Script:Colors.Dim)[$($timestamp.ToString('HH:mm:ss.fff'))]$($Script:Colors.Reset) $color$symbol $($Event.Operation)$($Script:Colors.Reset)"
    Write-Host "  $($Script:Colors.Path)📁 Path:$($Script:Colors.Reset) $($Event.Path)"
    Write-Host "  $($Script:Colors.Process)$($Script:Symbols.Process) Process:$($Script:Colors.Reset) $($Event.'Process Name') [$($Script:Colors.Cyan)PID: $($Event.PID)$($Script:Colors.Reset)]"

    if ($Event.'Image/Path' -and $Event.'Image/Path' -ne '') {
        Write-Host "  $($Script:Colors.Gray)   Executable: $($Event.'Image/Path')$($Script:Colors.Reset)"
    }

    if ($Event.'Command Line' -and $Event.'Command Line' -ne '') {
        $cmdLine = $Event.'Command Line'
        if ($cmdLine.Length -gt 100) {
            $cmdLine = $cmdLine.Substring(0, 97) + "..."
        }
        Write-Host "  $($Script:Colors.Gray)   Command: $cmdLine$($Script:Colors.Reset)"
    }

    Write-Host "  $($Script:Colors.Info)$($Script:Symbols.User) User:$($Script:Colors.Reset) $($Event.User)"

    if ($Event.Company -and $Event.Company -ne '') {
        Write-Host "  $($Script:Colors.Gray)   Company: $($Event.Company)$($Script:Colors.Reset)"
    }

    if ($Event.Detail -and $Event.Detail -ne '') {
        $detail = $Event.Detail
        if ($detail.Length -gt 80) {
            $detail = $detail.Substring(0, 77) + "..."
        }
        Write-Host "  $($Script:Colors.Gray)   Details: $detail$($Script:Colors.Reset)"
    }

    Write-Host "  $($Script:Colors.Dim)   Result: $($Event.Result)$($Script:Colors.Reset)"

    if ($Script:Config.ShowStackTrace -and $Event.'Stack' -and $Event.'Stack' -ne '') {
        Write-Host "  $($Script:Colors.Gray)   Stack Trace:$($Script:Colors.Reset)"
        $stack = $Event.'Stack' -split "`n" | Select-Object -First 3
        foreach ($frame in $stack) {
            Write-Host "    $($Script:Colors.Gray)$frame$($Script:Colors.Reset)"
        }
    }

    # Update statistics
    $Script:State.Statistics.TotalEvents++
}

function Format-SimpleEvent {
    <#
    .SYNOPSIS
        Formats simple event without ProcMon data
    #>
    param($Path, $ChangeType, $Timestamp)

    $symbol = switch ($ChangeType) {
        "Created" { $Script:Symbols.Create }
        "Deleted" { $Script:Symbols.Delete }
        "Changed" { $Script:Symbols.Write }
        "Renamed" { $Script:Symbols.Rename }
        default   { $Script:Symbols.Info }
    }

    $color = switch ($ChangeType) {
        "Created" { $Script:Colors.Green }
        "Deleted" { $Script:Colors.Red }
        "Changed" { $Script:Colors.Yellow }
        "Renamed" { $Script:Colors.Blue }
        default   { $Script:Colors.White }
    }

    Write-Host "$($Script:Colors.Dim)[$($Timestamp.ToString('HH:mm:ss.fff'))]$($Script:Colors.Reset) $color$symbol $ChangeType$($Script:Colors.Reset): $($Script:Colors.Path)$Path$($Script:Colors.Reset)"
}

function Show-Banner {
    <#
    .SYNOPSIS
        Display startup banner
    #>
    Clear-Host

    $banner = @"
$($Script:Colors.Cyan)╔══════════════════════════════════════════════════════════════════════╗
║$($Script:Colors.Bold)$($Script:Colors.White)        FILE SYSTEM MONITOR with PROCMON INTEGRATION v3.0           $($Script:Colors.Reset)$($Script:Colors.Cyan)║
╠══════════════════════════════════════════════════════════════════════╣
║$($Script:Colors.Yellow) Enhanced Process Tracking using Sysinternals Process Monitor        $($Script:Colors.Cyan)║
╚══════════════════════════════════════════════════════════════════════╝$($Script:Colors.Reset)

"@
    Write-Host $banner

    # Show status
    Write-Host "$($Script:Symbols.Info) Terminal ANSI Support: $(if ($Script:State.ANSISupported) { "$($Script:Colors.Green)Enabled$($Script:Colors.Reset)" } else { "Disabled" })"
    Write-Host "$($Script:Symbols.Info) Administrator: $(if (Test-IsAdministrator) { "$($Script:Colors.Green)Yes$($Script:Colors.Reset)" } else { "$($Script:Colors.Warning)No (Limited)$($Script:Colors.Reset)" })"
    Write-Host ""
}

function Show-Statistics {
    <#
    .SYNOPSIS
        Display monitoring statistics
    #>
    Write-Host ""
    Write-Host "$($Script:Colors.Cyan)$($Script:Symbols.LineH * 70)$($Script:Colors.Reset)"
    Write-Host "$($Script:Colors.Cyan)MONITORING STATISTICS$($Script:Colors.Reset)"
    Write-Host "$($Script:Colors.Cyan)$($Script:Symbols.LineH * 70)$($Script:Colors.Reset)"

    if ($Script:State.StartTime) {
        $duration = (Get-Date) - $Script:State.StartTime
        Write-Host "Duration: $($duration.ToString('hh\:mm\:ss'))"
    }

    Write-Host "Total Events: $($Script:State.Statistics.TotalEvents)"
    Write-Host ""

    if ($Script:State.Statistics.EventTypes.Count -gt 0) {
        Write-Host "$($Script:Colors.Yellow)Operation Breakdown:$($Script:Colors.Reset)"
        $Script:State.Statistics.EventTypes.GetEnumerator() |
            Sort-Object Value -Descending |
            Select-Object -First 10 |
            ForEach-Object {
                Write-Host "  $($_.Key): $($_.Value)"
            }
        Write-Host ""
    }

    if ($Script:State.Statistics.ProcessActivity.Count -gt 0) {
        Write-Host "$($Script:Colors.Magenta)Top Processes:$($Script:Colors.Reset)"
        $Script:State.Statistics.ProcessActivity.GetEnumerator() |
            Sort-Object { $_.Value.Count } -Descending |
            Select-Object -First 10 |
            ForEach-Object {
                Write-Host "  $($Script:Symbols.Process) $($_.Key): $($_.Value.Count) events"
                if ($_.Value.Path) {
                    Write-Host "     Path: $($Script:Colors.Gray)$($_.Value.Path)$($Script:Colors.Reset)"
                }
                if ($_.Value.Company) {
                    Write-Host "     Company: $($Script:Colors.Gray)$($_.Value.Company)$($Script:Colors.Reset)"
                }
            }
    }

    Write-Host "$($Script:Colors.Cyan)$($Script:Symbols.LineH * 70)$($Script:Colors.Reset)"
}

function Show-FolderDialog {
    <#
    .SYNOPSIS
        Show folder selection dialog
    #>
    Add-Type -AssemblyName System.Windows.Forms

    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select folder to monitor"
    $dialog.ShowNewFolderButton = $false
    $dialog.RootFolder = [System.Environment+SpecialFolder]::MyComputer

    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $dialog.SelectedPath
    }

    return $null
}

function Start-Monitoring {
    <#
    .SYNOPSIS
        Main monitoring loop
    #>
    $Script:State.MonitorActive = $true
    $Script:State.StartTime = Get-Date

    Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) Monitoring: $($Script:State.MonitorPath)$($Script:Colors.Reset)"
    Write-Host "$($Script:Colors.Info)Press [Q] to quit, [S] for statistics, [C] to clear, [P] to pause/resume$($Script:Colors.Reset)"
    Write-Host "$($Script:Colors.Cyan)$($Script:Symbols.LineH * 70)$($Script:Colors.Reset)"

    # Start ProcMon
    if (!(Start-ProcMon -Path $Script:State.MonitorPath)) {
        Write-Host "$($Script:Colors.Error)Failed to start ProcMon. Exiting...$($Script:Colors.Reset)"
        return
    }

    # Start FileSystemWatcher
    $watcher = Watch-FileSystem

    # Main loop
    $paused = $false
    while ($Script:State.MonitorActive) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)

            switch ($key.Key) {
                'Q' {
                    $Script:State.MonitorActive = $false
                }
                'S' {
                    Show-Statistics
                }
                'C' {
                    Clear-Host
                    Show-Banner
                    Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) Monitoring: $($Script:State.MonitorPath)$($Script:Colors.Reset)"
                    Write-Host "$($Script:Colors.Cyan)$($Script:Symbols.LineH * 70)$($Script:Colors.Reset)"
                }
                'P' {
                    $paused = !$paused
                    $watcher.EnableRaisingEvents = !$paused
                    if ($paused) {
                        Write-Host "$($Script:Colors.Warning)$($Script:Symbols.Warning) Monitoring PAUSED$($Script:Colors.Reset)"
                    }
                    else {
                        Write-Host "$($Script:Colors.Success)$($Script:Symbols.Success) Monitoring RESUMED$($Script:Colors.Reset)"
                    }
                }
            }
        }

        Start-Sleep -Milliseconds 100
    }

    # Cleanup
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Get-EventSubscriber | Where-Object { $_.SourceObject -eq $watcher } | Unregister-Event
}

# Main execution
try {
    # Check admin
    if (!(Test-IsAdministrator)) {
        Write-Host "$($Script:Colors.Warning)Administrator privileges required for ProcMon$($Script:Colors.Reset)"
        Write-Host "Please run PowerShell as Administrator"
        Write-Host ""
        Write-Host "Press any key to exit..."
        [Console]::ReadKey($true) | Out-Null
        exit 1
    }

    # Initialize
    Initialize-ColorScheme
    Initialize-Symbols
    Show-Banner

    # Install ProcMon if needed
    if (!(Install-ProcMon)) {
        Write-Host "$($Script:Colors.Error)Cannot proceed without ProcMon$($Script:Colors.Reset)"
        Write-Host "Press any key to exit..."
        [Console]::ReadKey($true) | Out-Null
        exit 1
    }

    # Get monitor path
    if (!$Script:State.MonitorPath) {
        Write-Host "$($Script:Colors.Info)$($Script:Symbols.Info) Opening folder selection dialog...$($Script:Colors.Reset)"
        $Script:State.MonitorPath = Show-FolderDialog
    }

    if (!$Script:State.MonitorPath -or !(Test-Path $Script:State.MonitorPath)) {
        Write-Host "$($Script:Colors.Warning)No valid folder selected. Exiting.$($Script:Colors.Reset)"
        Write-Host "Press any key to exit..."
        [Console]::ReadKey($true) | Out-Null
        exit 0
    }

    # Start monitoring
    Start-Monitoring
}
catch {
    Write-Host "$($Script:Colors.Error)$($Script:Symbols.Error) Error: $_$($Script:Colors.Reset)"
    Write-Host "$($Script:Colors.Gray)$($_.ScriptStackTrace)$($Script:Colors.Reset)"
}
finally {
    # Cleanup
    Stop-ProcMon

    if ($Script:State.EventLog.Count -gt 0) {
        Show-Statistics
    }

    Write-Host ""
    Write-Host "$($Script:Colors.Success)Monitoring stopped. Total events: $($Script:State.Statistics.TotalEvents)$($Script:Colors.Reset)"

    # Reset console
    if ($Script:State.ANSISupported) {
        Write-Host $Script:Colors.Reset
    }
}