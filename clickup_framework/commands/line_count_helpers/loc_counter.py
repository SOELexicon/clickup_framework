"""
Line-of-code counting engine with recursive directory traversal.

This module provides the core line-counting functionality that recursively
traverses directories, identifies source files, and counts lines by type
(blank, comment, code) per language.

Variables:    COMMENT_PATTERNS
Classes:      LineCounter
"""

from pathlib import Path
from typing import Dict, Optional, Any
from .file_filter import FileFilter


# Comment patterns for different languages
COMMENT_PATTERNS = {
    'Python': {
        'single': '#',
        'multi_start': '"""',
        'multi_end': '"""',
    },
    'JavaScript': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'TypeScript': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'C#': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'Java': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'C++': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'C': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'Go': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'Rust': {
        'single': '//',
        'multi_start': '/*',
        'multi_end': '*/',
    },
    'HTML': {
        'single': None,
        'multi_start': '<!--',
        'multi_end': '-->',
    },
    'CSS': {
        'single': None,
        'multi_start': '/*',
        'multi_end': '*/',
    },
}


class LineCounter:
    """
    Count lines of code in source files with language detection.

    Purpose:    Recursively traverse directories and count lines (code, blank, comment)
    Usage:      Create instance, call count_files() to process directory tree
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: core line-counting engine
    """

    def __init__(self, max_depth: Optional[int] = None,
                 language_filter: Optional[str] = None):
        """
        Initialize LineCounter.

        Args:
            max_depth: Maximum directory depth to traverse (None = unlimited)
            language_filter: Only count files of this language (e.g., 'Python')
        """
        self.max_depth = max_depth
        self.file_filter = FileFilter(language_filter=language_filter)

    def count_files(self, path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Recursively count lines in all source files in a directory tree.

        Args:
            path: Root directory path to traverse

        Returns:
            Dictionary mapping file paths (as strings) to line counts:
            {
                'path/to/file.py': {
                    'total': 100,
                    'blank': 20,
                    'comment': 15,
                    'code': 65,
                    'language': 'Python'
                },
                ...
            }

        Note:
            - Files are identified by extension using FileFilter
            - Respects max_depth limit if set
            - Encoding errors are handled gracefully (file skipped)
            - Empty dictionary returned if path is invalid
        """
        results = {}
        path = Path(path)

        if not path.is_dir():
            return results

        self._traverse_directory(path, results, depth=0)
        return results

    def _traverse_directory(self, current_path: Path, results: Dict,
                            depth: int) -> None:
        """
        Recursively traverse directory and count files.

        Args:
            current_path: Current directory being processed
            results: Dictionary to accumulate results
            depth: Current traversal depth
        """
        # Check max_depth limit
        if self.max_depth is not None and depth >= self.max_depth:
            return

        try:
            entries = current_path.iterdir()
        except (PermissionError, OSError):
            # Gracefully skip inaccessible directories
            return

        for entry in entries:
            try:
                if entry.is_dir():
                    # Recurse into subdirectory
                    self._traverse_directory(entry, results, depth + 1)
                elif entry.is_file():
                    # Count this file if it should be included
                    if self.file_filter.should_include(entry):
                        file_counts = self.count_lines(entry)
                        if file_counts:
                            results[str(entry)] = file_counts
            except (PermissionError, OSError):
                # Skip files/dirs that can't be accessed
                continue

    def count_lines(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Count lines in a single file by type.

        Args:
            file_path: Path to the file to count

        Returns:
            Dictionary with keys:
            - 'total': Total number of lines
            - 'blank': Number of blank lines
            - 'comment': Number of comment lines
            - 'code': Number of code lines (total - blank - comment)
            - 'language': Detected programming language

            Returns None if file cannot be read or language is unknown.

        Algorithm:
            1. Detect language by file extension
            2. Read file with UTF-8 encoding (fallback to latin-1)
            3. Identify single-line and multi-line comments per language rules
            4. Count lines in each category
        """
        language = self.file_filter.get_language(file_path)
        if language is None:
            return None

        try:
            # Try UTF-8 first, fallback to latin-1 for legacy files
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = file_path.read_text(encoding='latin-1')
        except (OSError, IOError):
            # File can't be read (permission, etc.)
            return None

        lines = content.splitlines()
        total = len(lines)

        # Count blank and comment lines
        blank_count = 0
        comment_count = 0
        in_multiline_comment = False

        comment_config = COMMENT_PATTERNS.get(language, {})
        single_marker = comment_config.get('single')
        multi_start = comment_config.get('multi_start')
        multi_end = comment_config.get('multi_end')

        for line in lines:
            stripped = line.strip()

            # Count blank lines
            if not stripped:
                blank_count += 1
                continue

            # Track multiline comment state
            if multi_start and multi_end:
                if in_multiline_comment:
                    comment_count += 1
                    if multi_end in stripped:
                        in_multiline_comment = False
                    continue

                if multi_start in stripped:
                    comment_count += 1
                    if multi_end not in stripped:
                        in_multiline_comment = True
                    continue

            # Check for single-line comments
            if single_marker and stripped.startswith(single_marker):
                comment_count += 1
                continue

        code_count = total - blank_count - comment_count

        return {
            'total': total,
            'blank': blank_count,
            'comment': comment_count,
            'code': code_count,
            'language': language,
        }
