#!/bin/bash

# Generate screenshots from ANSI-colored text outputs
# Based on the provided script for converting CLI output to images

set -e

# Config
OUTPUT_DIR="outputs"
SCREENSHOT_DIR="screenshots"
WIDTH=1200

# Create screenshot directory
mkdir -p "$SCREENSHOT_DIR"

echo "🖼️  Generating screenshots from display outputs..."

# Check if required tools are installed
if ! command -v aha &> /dev/null; then
    echo "❌ Error: 'aha' is not installed. Install with: sudo apt-get install aha"
    exit 1
fi

if ! command -v wkhtmltoimage &> /dev/null; then
    echo "❌ Error: 'wkhtmltoimage' is not installed. Install with: sudo apt-get install wkhtmltopdf"
    exit 1
fi

# Process each output file
for txt_file in "$OUTPUT_DIR"/*.txt; do
    if [ ! -f "$txt_file" ]; then
        echo "⚠️  No output files found in $OUTPUT_DIR/"
        exit 1
    fi

    # Get base filename without extension
    basename=$(basename "$txt_file" .txt)

    html_file="$SCREENSHOT_DIR/${basename}.html"
    jpg_file="$SCREENSHOT_DIR/${basename}.jpg"

    echo "  Processing: $basename"

    # Convert ANSI to HTML
    cat "$txt_file" | aha --black > "$html_file"

    # Inject proper black background CSS and better formatting
    sed -i '/<\/head>/i \
<style>\
body, pre { \
  background-color: black !important; \
  color: white !important; \
  font-family: "Monaco", "Menlo", "Ubuntu Mono", "Consolas", "source-code-pro", monospace; \
  font-size: 14px; \
  line-height: 1.5; \
  padding: 20px; \
  margin: 0; \
}\
pre { \
  white-space: pre-wrap; \
  word-wrap: break-word; \
}\
</style>' "$html_file"

    # Convert HTML to JPG
    wkhtmltoimage --width "$WIDTH" --format jpg --quality 100 "$html_file" "$jpg_file" 2>/dev/null

    # Clean up HTML file (optional)
    # rm "$html_file"

    echo "    ✓ Created: $jpg_file"
done

echo ""
echo "✅ All screenshots generated in '$SCREENSHOT_DIR/' directory"
echo ""
echo "Screenshots created:"
ls -1 "$SCREENSHOT_DIR"/*.jpg 2>/dev/null | sed 's/^/  - /'
