"""
File filtering and language detection for line counting.

This module provides utilities to filter files based on language support and
ignore patterns, and to detect programming languages by file extension.

Variables:    LANGUAGE_EXTENSIONS, BINARY_EXTENSIONS, IGNORE_DIRS, IGNORE_FILES
Classes:      FileFilter
"""

from pathlib import Path
from typing import Optional


# Map file extensions to programming languages
LANGUAGE_EXTENSIONS = {
    '.cs': 'C#',
    '.razor': 'C#',
    '.cshtml': 'C#',
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JavaScript',
    '.tsx': 'TypeScript',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.go': 'Go',
    '.rs': 'Rust',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C',
    '.hpp': 'C++',
}

# Map languages to language groups for filtering
LANGUAGE_GROUPS = {
    'C#': '.NET Core',
    'YAML': '.NET Core',
    'JSON': '.NET Core',
    'Python': 'Python',
    'JavaScript': 'JavaScript/TypeScript',
    'TypeScript': 'JavaScript/TypeScript',
    'HTML': 'Web Frontend',
    'CSS': 'Web Frontend',
    'Go': 'Go',
    'Rust': 'Rust',
    'Java': 'Java',
    'C++': 'C/C++',
    'C': 'C/C++',
}

# Binary and compiled files to ignore
BINARY_EXTENSIONS = {
    '.dll', '.exe', '.pdb', '.o', '.so', '.a', '.dylib',
    '.pyc', '.pyo', '.egg-info', '.class', '.jar',
}

# Directories to completely ignore
IGNORE_DIRS = {
    '.git', '.venv', '__pycache__', 'node_modules', 'bin', 'obj',
    'dist', '.pytest_cache', '.mypy_cache', '.tox', '.eggs',
    'venv', 'env', 'build', 'htmlcov', 'egg-info',
}

# Config files that are binary or compiled
IGNORE_FILES = {
    '.config', '.pdb',
}


class FileFilter:
    """
    Filter files by language support and ignore patterns.

    Purpose:    Determine which files should be counted and detect their language
    Usage:      Create instance, call should_include() to filter files
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: file filtering and language detection
    """

    def __init__(self, language_filter: Optional[str] = None):
        """
        Initialize FileFilter.

        Args:
            language_filter: Optional language to filter by (e.g., 'Python').
                           If set, only files of this language are included.
        """
        self.language_filter = language_filter

    def should_include(self, file_path: Path) -> bool:
        """
        Determine if a file should be included in line counting.

        Args:
            file_path: Path object to check

        Returns:
            True if file should be counted, False otherwise

        Logic:
            - Returns False for binary/compiled files
            - Returns False for ignored directories
            - Returns False if language_filter is set and file language doesn't match
            - Returns True for supported source code languages
        """
        # Check if in ignored directory
        for part in file_path.parts:
            if part in IGNORE_DIRS:
                return False

        # Get file extension (lowercase)
        ext = file_path.suffix.lower()

        # Reject binary and config files
        if ext in BINARY_EXTENSIONS or ext in IGNORE_FILES:
            return False

        # Only include files with recognized language extensions
        if ext not in LANGUAGE_EXTENSIONS:
            return False

        # If language filter is set, check if this file matches
        if self.language_filter is not None:
            file_language = self.get_language(file_path)
            if file_language != self.language_filter:
                return False

        return True

    def get_language(self, file_path: Path) -> Optional[str]:
        """
        Detect programming language by file extension.

        Args:
            file_path: Path object to analyze

        Returns:
            Language name (e.g., 'Python', 'JavaScript') or None if unknown
        """
        ext = file_path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(ext)
