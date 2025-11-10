"""
ClickUp Framework CLI entry point.

This allows the package to be run as:
    python -m clickup_framework <command> <args>
"""

import sys
import io

# Configure stdout and stderr to use UTF-8 encoding on Windows
# This prevents UnicodeEncodeError when using Unicode characters (✓, ├─, └─, │, etc.)
if hasattr(sys.stdout, 'reconfigure'):
    # Python 3.7+: Use reconfigure method
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
else:
    # Fallback for older Python versions
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from clickup_framework.cli import main

if __name__ == '__main__':
    main()
