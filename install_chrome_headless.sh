#!/bin/bash
#
# Install Chrome Headless Shell for Puppeteer/Mermaid CLI
#

set -e

echo "Installing Chrome Headless Shell for Puppeteer..."
echo ""

# Create cache directory
CACHE_DIR="$HOME/.cache/puppeteer"
mkdir -p "$CACHE_DIR"

# Determine platform
PLATFORM="linux"
ARCH="x64"

if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    ARCH="arm64"
fi

# Chrome version that Puppeteer 23.11.1 expects
CHROME_VERSION="131.0.6778.204"

echo "Platform: $PLATFORM"
echo "Architecture: $ARCH"
echo "Chrome version: $CHROME_VERSION"
echo ""

# Download URL
if [ "$PLATFORM" == "linux" ]; then
    DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-headless-shell-linux64.zip"
    TARGET_DIR="$CACHE_DIR/chrome-headless-shell/linux-${CHROME_VERSION}/chrome-headless-shell-linux64"
elif [ "$PLATFORM" == "mac" ]; then
    DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/mac-${ARCH}/chrome-headless-shell-mac-${ARCH}.zip"
    TARGET_DIR="$CACHE_DIR/chrome-headless-shell/mac-${CHROME_VERSION}/chrome-headless-shell-mac-${ARCH}"
fi

echo "Download URL: $DOWNLOAD_URL"
echo "Target directory: $TARGET_DIR"
echo ""

# Create target directory
mkdir -p "$TARGET_DIR"

# Download
TMP_FILE="/tmp/chrome-headless-shell.zip"
echo "Downloading..."
if command -v wget &> /dev/null; then
    wget -q --show-progress -O "$TMP_FILE" "$DOWNLOAD_URL"
elif command -v curl &> /dev/null; then
    curl -L -# -o "$TMP_FILE" "$DOWNLOAD_URL"
else
    echo "ERROR: wget or curl required"
    exit 1
fi

# Extract
echo "Extracting..."
unzip -q "$TMP_FILE" -d "$CACHE_DIR/tmp_extract"

# Move to target location
mv "$CACHE_DIR/tmp_extract"/* "$TARGET_DIR/" 2>/dev/null || mv "$CACHE_DIR/tmp_extract"/*/* "$TARGET_DIR/"

# Cleanup
rm -rf "$TMP_FILE" "$CACHE_DIR/tmp_extract"

# Make executable
chmod +x "$TARGET_DIR"/* 2>/dev/null || true

echo ""
echo "✓ Chrome Headless Shell installed successfully!"
echo ""
echo "Location: $TARGET_DIR"
echo ""
echo "Test with:"
echo "  mmdc -i test.mmd -o test.png"
