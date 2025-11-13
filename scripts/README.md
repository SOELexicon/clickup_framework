# ClickUp Framework Scripts

Utility scripts for ClickUp Framework development and documentation.

---

## Documentation Import

### `import_cli_docs.sh`

Import the CLI command reference documentation to ClickUp Docs in bulk.

**Usage:**
```bash
# Import to current/default workspace
./scripts/import_cli_docs.sh

# Import to specific workspace
./scripts/import_cli_docs.sh 90151898946

# Custom doc name
./scripts/import_cli_docs.sh --doc-name "CLI Reference v2.0"

# Check prerequisites without importing
./scripts/import_cli_docs.sh --check

# Show help
./scripts/import_cli_docs.sh --help
```

**Requirements:**
- ClickUp Framework installed (`cum` command available)
- `CLICKUP_API_TOKEN` environment variable set
- Workspace ID (provided, in context, or via `CLICKUP_DEFAULT_WORKSPACE`)

**What it does:**
1. Validates prerequisites (cum command, API token, docs directory)
2. Sets workspace context
3. Imports all markdown files from `docs/cli/` directory
4. Creates a single ClickUp Doc with all pages
5. Returns the Doc ID for reference

**Output:**
- Creates ClickUp Doc with 8 pages:
  - Index (main page with all shortcodes)
  - View Commands
  - Task Management Commands
  - Comment Management Commands
  - Docs Management Commands
  - Context Management Commands
  - Configuration Commands
  - Advanced Commands
- Saves Doc ID to `.last_imported_doc_id` file

**Options:**
- `-h, --help` - Show help message
- `-d, --doc-name NAME` - Custom doc name (default: "CLI Command Reference")
- `-n, --nested` - Use nested directory structure
- `-c, --check` - Check prerequisites only

**Example workflow:**
```bash
# Check everything is ready
./scripts/import_cli_docs.sh --check

# Import to workspace
./scripts/import_cli_docs.sh 90151898946

# View the imported doc
DOC_ID=$(cat .last_imported_doc_id)
cum doc_get current $DOC_ID
```

---

## Test Failure Reporting

### `report_test_failures_to_clickup.py`

Parse test results and create ClickUp bug report tasks only for test failures.

**Usage:**
```bash
# Run after tests to report failures
python scripts/report_test_failures_to_clickup.py
```

**Requirements:**
- ClickUp Framework installed
- `CLICKUP_API_TOKEN` environment variable set
- Test report file (default: `test_report.json`)

**What it does:**
1. Parses pytest JSON report (`test_report.json`)
2. Extracts failed/errored tests
3. Identifies the command and args from test nodeid
4. Creates bug report tasks in ClickUp with:
   - Test failure details
   - Command and args that failed
   - Error traceback
   - Reproduction steps
   - Investigation checklist
5. Tags bugs with: `bug`, `test-failure`, `cmd-{command}`, branch name
6. Avoids creating duplicate bug reports

**Environment variables:**
- `CLICKUP_API_TOKEN` - ClickUp API token (required)
- `CLICKUP_BUG_LIST_ID` - List ID for bug reports (default: "901517412318")
- `GITHUB_REPOSITORY` - Repository name (for GitHub Actions)
- `GITHUB_REF_NAME` - Branch name (for GitHub Actions)
- `GITHUB_SHA` - Commit hash (for GitHub Actions)
- `TEST_REPORT_PATH` - Path to test report JSON (default: "test_report.json")

**Example output:**
```
📋 Test Failure Report to ClickUp
================================================================================
Repository: clickup_framework
Branch: main
Commit: abc12345
Report: test_report.json

🔍 Parsing test results...
⚠️  Found 2 test failure(s)

Processing: tests/commands/test_hierarchy.py::test_hierarchy_with_invalid_id
  Command: hierarchy
  Args: with invalid id
  Outcome: failed
  ✓ Bug task created: 86c6xyz123
    URL: https://app.clickup.com/t/86c6xyz123

SUMMARY
================================================================================
Test failures found: 2
Bug tasks created: 2
Bug tasks skipped (already exist): 0
```

**Integration with CI/CD:**

The script is automatically run by GitHub Actions when tests fail. See `.github/workflows/ci.yml`:

```yaml
- name: Report Test Failures to ClickUp
  if: failure()  # Only run if tests failed
  env:
    CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
    CLICKUP_BUG_LIST_ID: ${{ secrets.CLICKUP_BUG_LIST_ID }}
  run: |
    python scripts/report_test_failures_to_clickup.py
```

**Bug task format:**

Each bug task includes:
- 🐛 Emoji prefix
- Test nodeid
- Command and args
- Error traceback
- Reproduction steps
- Investigation checklist
- Auto-tagged with command and branch

**Archived Scripts:**

See `scripts/archive/` for deprecated scripts:
- `post_commits_to_clickup.py` - Replaced by test failure reporting system

---

## Display Component Scripts

Scripts for generating visual examples and screenshots of the display components.

## Scripts

### `generate_display_examples.py`

Generates example outputs from the display components using sample task data.

**Usage:**
```bash
python scripts/generate_display_examples.py
```

**Output:**
- Creates `outputs/` directory with `.txt` files containing ANSI-colored output
- Generates 8 different examples:
  1. Minimal view
  2. Summary view
  3. Detailed view with descriptions
  4. Container hierarchy
  5. Filtered view (in progress tasks)
  6. Full view with all options
  7. Task statistics
  8. Flat view

**Environment:**
- Set `FORCE_COLOR=1` to ensure colors are rendered even when not in a TTY

### `generate_screenshots.sh`

Converts ANSI-colored text outputs to JPG screenshots.

**Usage:**
```bash
./scripts/generate_screenshots.sh
```

**Requirements:**
- `aha` - ANSI HTML Adapter for converting ANSI to HTML
  ```bash
  sudo apt-get install aha
  ```
- `wkhtmltoimage` - Convert HTML to images
  ```bash
  sudo apt-get install wkhtmltopdf
  ```

**Output:**
- Creates `screenshots/` directory with `.jpg` images
- Also creates intermediate `.html` files for debugging

## Workflow Integration

These scripts are automatically run by the GitHub Actions workflow:

`.github/workflows/test-and-screenshot.yml`

The workflow:
1. Runs all component tests
2. Generates display examples
3. Converts to screenshots
4. Uploads as artifacts
5. Comments on PRs with screenshot previews

## Local Usage

To generate screenshots locally:

```bash
# Install dependencies
pip install -e .

# Install system tools
sudo apt-get install aha wkhtmltopdf

# Generate examples
FORCE_COLOR=1 python scripts/generate_display_examples.py

# Generate screenshots
./scripts/generate_screenshots.sh

# View results
ls -l screenshots/
```

## Customization

To add new examples:

1. Edit `generate_display_examples.py`
2. Add new sample data or formatting options
3. Call `save_output()` with a new filename
4. Run the script to generate the output
5. Run `generate_screenshots.sh` to create the image

## Output Format

Screenshots are generated at 1200px width with:
- Black background
- White text
- Monospace font
- High quality JPG (quality 100)
- ANSI colors preserved via HTML conversion

---

# SessionStart Hook Setup Scripts

These scripts automate the process of adding a SessionStart hook to any project, which will automatically install ClickUp Framework when you open the project in Claude Code on the web.

## For Windows Users

**`setup-clickup-hook.ps1`** - PowerShell script with GUI folder picker

### Usage:

1. **Open PowerShell** (not PowerShell ISE)
2. **Run the script:**
   ```powershell
   .\scripts\setup-clickup-hook.ps1
   ```
3. **Follow the prompts:**
   - Select your project folder in the GUI dialog
   - Confirm the setup
   - Script creates `.claude/hooks/` and `.claude/settings.json`

### Features:
- ✅ GUI folder picker dialog
- ✅ Automatically backs up existing settings.json
- ✅ Color-coded output
- ✅ Creates .env.example template

## For Linux/macOS Users

**`setup-clickup-hook.sh`** - Bash script with terminal interface

### Usage:

1. **Run the script:**
   ```bash
   ./scripts/setup-clickup-hook.sh
   ```
2. **Follow the prompts:**
   - Enter the full path to your project folder
   - Confirm the setup

### Features:
- ✅ Smart JSON merging (if `jq` is installed)
- ✅ Automatic backup of existing settings
- ✅ Color-coded terminal output

## What Gets Created

Both scripts create:
```
your-project/
├── .claude/
│   ├── hooks/
│   │   └── session-start.sh    # Installs ClickUp Framework
│   └── settings.json            # Hook configuration
└── .env.example                 # Environment template (optional)
```

## After Running

1. **Commit the changes:**
   ```bash
   git add .claude/
   git commit -m "Add ClickUp Framework SessionStart hook"
   git push
   ```

2. **Use in Claude Code:**
   - Open project in Claude Code on the web
   - Hook automatically installs ClickUp Framework
   - Commands `cum`, `clickup`, `cum-mcp` become available

See the full documentation in the scripts for more details.
