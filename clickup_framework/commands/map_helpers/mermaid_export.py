"""Mermaid diagram export utilities (image formats via mmdc)."""

import sys
import subprocess
from clickup_framework.utils.colors import colorize, TextColor


def check_mmdc_available() -> bool:
    """Check if mermaid-cli (mmdc) is available."""
    try:
        result = subprocess.run(
            ['mmdc', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True  # Use shell on Windows to find mmdc
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def export_mermaid_to_image(markdown_file: str, output_file: str, image_format: str, use_color: bool = False) -> bool:
    """
    Export mermaid markdown to image using mmdc (mermaid-cli).

    Args:
        markdown_file: Input markdown file with mermaid diagram
        output_file: Output image file path
        image_format: Image format (png, svg, jpg)
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    if not check_mmdc_available():
        error_msg = "ERROR: mmdc (mermaid-cli) not found. Install with: npm install -g @mermaid-js/mermaid-cli"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        return False

    try:
        # Map jpg to jpeg for mmdc
        mmdc_format = 'jpeg' if image_format == 'jpg' else image_format

        cmd = [
            'mmdc',
            '-i', markdown_file,
            '-o', output_file,
            '-t', 'dark',  # Use dark theme
            '-b', 'transparent',  # Transparent background
            '-w', '4000',  # High width for better resolution
            '-H', '3000',  # High height
            '-s', '3'  # Scale factor for even higher quality
        ]

        if use_color:
            print(colorize(f"[PROGRESS] Converting to {image_format.upper()}...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Converting to {image_format.upper()}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True  # Use shell on Windows
        )

        if result.returncode == 0:
            if use_color:
                print(colorize(f"[SUCCESS] Image exported: {output_file}", TextColor.GREEN))
            else:
                print(f"[SUCCESS] Image exported: {output_file}")
            return True
        else:
            if use_color:
                print(colorize(f"[ERROR] mmdc failed: {result.stderr}", TextColor.RED), file=sys.stderr)
            else:
                print(f"[ERROR] mmdc failed: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to export image: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to export image: {e}", file=sys.stderr)
        return False
