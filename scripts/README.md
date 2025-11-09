# Display Component Scripts

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
