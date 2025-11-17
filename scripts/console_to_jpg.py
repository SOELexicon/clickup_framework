#!/usr/bin/env python3
"""
Convert console output to JPG image with black background.

This script is a CLI wrapper for the console_to_jpg utility function.

Usage:
    python scripts/console_to_jpg.py <input_file> <output_file>
    Or pipe input: command | python scripts/console_to_jpg.py - output.jpg
"""

import sys
import os
from pathlib import Path

# Use the utility function from the framework
try:
    from clickup_framework.utils.image_export import console_to_jpg
except ImportError as e:
    print(f"Error: Could not import console_to_jpg. {e}", file=sys.stderr)
    sys.exit(1)


# All functionality is now in clickup_framework.utils.image_export


def main():
    if len(sys.argv) < 3:
        print("Usage: python console_to_jpg.py <input_file|-> <output_file> [width] [bg_color]", file=sys.stderr)
        print("  Use '-' for input_file to read from stdin", file=sys.stderr)
        sys.exit(1)
    
    input_source = sys.argv[1]
    output_path = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
    bg_color = sys.argv[4] if len(sys.argv) > 4 else "black"
    
    # Read input
    if input_source == '-':
        text = sys.stdin.read()
    else:
        with open(input_source, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    
    # Use the utility function
    try:
        success = console_to_jpg(text, output_path, width, bg_color)
        if success:
            print(f"Image created: {output_path}")
        else:
            print(f"Error: Failed to create image", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error creating image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

