@echo off
REM ============================================================================
REM generate_codemap.bat - Generate ctags code map for .NET/Python projects
REM 
REM Usage:
REM   generate_codemap.bat              - Generate full tags
REM   generate_codemap.bat --python     - Python only
REM   generate_codemap.bat --csharp     - C# only
REM   generate_codemap.bat --all-langs  - All supported languages
REM   generate_codemap.bat --stats      - Generate statistics only
REM
REM Requires: Universal ctags (built with libjansson for JSON support)
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set OUTPUT_FILE=.tags.json
set DOCS_DIR=docs\codemap
set TIMESTAMP=%date:~-4%-%date:~-10,2%-%date:~-7,2% %time:~0,2%:%time:~3,2%:%time:~6,2%

REM Parse arguments
set FILTER=all
if "%1"=="--python" set FILTER=python
if "%1"=="--csharp" set FILTER=csharp
if "%1"=="--all-langs" set FILTER=all
if "%1"=="--stats" goto :stats_only
if "%1"=="--help" goto :show_help

REM Check ctags is available
where ctags >nul 2>&1
if errorlevel 1 (
    echo ERROR: ctags not found. Install with: choco install universal-ctags
    echo        or download from: https://github.com/universal-ctags/ctags-win32/releases
    exit /b 1
)

echo.
echo ============================================================================
echo Universal ctags Code Map Generator
echo ============================================================================
echo.
echo [INFO] Filter: %FILTER%
echo [INFO] Output: %OUTPUT_FILE%
echo [INFO] Generated: %TIMESTAMP%
echo.

REM Build ctags command based on filter
set CTAGS_CMD=ctags --output-format=json --quiet --exclude=.venv --exclude=node_modules --exclude=bin --exclude=obj -R .

if "%FILTER%"=="python" (
    set CTAGS_CMD=%CTAGS_CMD% --languages=Python
    echo [INFO] Python symbols only
)

if "%FILTER%"=="csharp" (
    set CTAGS_CMD=%CTAGS_CMD% --languages=C#
    echo [INFO] C# symbols only
)

if "%FILTER%"=="all" (
    echo [INFO] All supported languages
)

echo.
echo [PROGRESS] Generating tags...
%CTAGS_CMD% > %OUTPUT_FILE% 2>ctags_errors.log

if errorlevel 1 (
    echo.
    echo [WARNING] ctags completed with warnings (exit code %errorlevel%)
    if exist ctags_errors.log (
        type ctags_errors.log | findstr /V "^$" > nul
        if not errorlevel 1 (
            echo [ERRORS] See ctags_errors.log
        )
    )
) else (
    echo [SUCCESS] Tags generated successfully
)

REM Count tags
for /f %%a in ('find /c /v "dummy" %OUTPUT_FILE%') do set LINE_COUNT=%%a
echo [INFO] Total lines: %LINE_COUNT%

REM Create docs directory
if not exist "%DOCS_DIR%" mkdir "%DOCS_DIR%"

REM Generate JSON statistics
echo [PROGRESS] Generating statistics...
python generate_codemap_stats.py "%TIMESTAMP%"

if errorlevel 1 (
    echo [ERROR] Statistics generation failed
    exit /b 1
)

REM Generate summary markdown
echo [PROGRESS] Generating summary markdown...
(
    echo # Code Map Summary
    echo.
    echo Generated: %TIMESTAMP%
    echo.
    echo ## Quick Stats
    echo.
    echo | more +1 docs\codemap\statistics.json
    echo.
    echo ## Usage
    echo.
    echo ### Python
    echo ```bash
    echo python ctags_parser.py %OUTPUT_FILE% show src/module.py
    echo python ctags_parser.py %OUTPUT_FILE% filter Python class
    echo ```
    echo.
    echo ### PowerShell
    echo ```powershell
    echo Import-Module CtagsMapper.psm1
    echo $parser = New-CtagsParser '%OUTPUT_FILE%'
    echo Show-SymbolTree -Parser $parser -FilePath 'src/Service.cs'
    echo ```
    echo.
) > "%DOCS_DIR%\README.md"

echo [SUCCESS] Summary: %DOCS_DIR%\README.md
echo.
echo ============================================================================
echo [COMPLETE] Code map generated successfully
echo ============================================================================
echo.
echo Files:
echo   - %OUTPUT_FILE% (JSON tags)
echo   - %DOCS_DIR%\statistics.json (metrics)
echo   - %DOCS_DIR%\README.md (summary)
echo.
goto :end

:stats_only
echo [INFO] Statistics only mode
python show_codemap_stats.py
goto :end

:show_help
echo.
echo Universal ctags Code Map Generator for Windows
echo.
echo Usage:
echo   %~n0              Generate full code map (all languages)
echo   %~n0 --python     Python symbols only
echo   %~n0 --csharp     C# symbols only
echo   %~n0 --all-langs  All supported languages
echo   %~n0 --stats      Show statistics only
echo   %~n0 --help       Show this help
echo.
echo Outputs:
echo   .tags.json            - ctags JSON output
echo   docs/codemap/         - Generated documentation
echo.
echo Requirements:
echo   - Universal ctags (with JSON support)
echo   - Python 3.x (for statistics)
echo.
echo Install ctags:
echo   choco install universal-ctags
echo   or download: https://github.com/universal-ctags/ctags-win32/releases
echo.
goto :end

:end
endlocal
exit /b %ERRORLEVEL%
