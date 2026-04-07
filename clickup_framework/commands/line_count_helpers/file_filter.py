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
    # .NET Core
    '.cs': 'C#',
    '.razor': 'C#',
    '.cshtml': 'C#',
    '.vb': 'VB.NET',
    '.fs': 'F#',
    '.fsx': 'F#',
    '.fsi': 'F#',

    # Web Frontend
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'SASS',
    '.less': 'LESS',
    '.vue': 'Vue',

    # Web Backend
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.erb': 'Ruby',
    '.py': 'Python',
    '.go': 'Go',
    '.rs': 'Rust',

    # Java/JVM
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.groovy': 'Groovy',
    '.gradle': 'Gradle',

    # Other Languages
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.c': 'C',
    '.h': 'C',
    '.hpp': 'C++',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
    '.pl': 'Perl',
    '.r': 'R',
    '.lua': 'Lua',
    '.clj': 'Clojure',
    '.cljs': 'Clojure',
    '.hs': 'Haskell',
    '.erl': 'Erlang',
    '.ex': 'Elixir',
    '.exs': 'Elixir',
    '.dart': 'Dart',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.zsh': 'Shell',
    '.fish': 'Shell',
    '.ps1': 'PowerShell',

    # Configuration & Data
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.config': 'XML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
    '.properties': 'Properties',
    '.gradle': 'Gradle',
    '.pom': 'Maven POM',
    '.env': 'Env',
    '.lock': 'Lock File',
    '.dockerfile': 'Dockerfile',

    # Documentation
    '.md': 'Markdown',
    '.rst': 'ReStructuredText',
    '.adoc': 'AsciiDoc',
    '.asciidoc': 'AsciiDoc',
    '.tex': 'LaTeX',
}

# Map languages to language groups for filtering
LANGUAGE_GROUPS = {
    # .NET Core
    'C#': '.NET Core',
    'VB.NET': '.NET Core',
    'F#': '.NET Core',

    # Web Frontend
    'JavaScript': 'Web Frontend',
    'TypeScript': 'Web Frontend',
    'HTML': 'Web Frontend',
    'CSS': 'Web Frontend',
    'SCSS': 'Web Frontend',
    'SASS': 'Web Frontend',
    'LESS': 'Web Frontend',
    'Vue': 'Web Frontend',

    # Web Backend
    'PHP': 'Web Backend',
    'Ruby': 'Web Backend',
    'Python': 'Web Backend',
    'Go': 'Web Backend',
    'Rust': 'Web Backend',

    # Java/JVM Ecosystem
    'Java': 'JVM Languages',
    'Kotlin': 'JVM Languages',
    'Scala': 'JVM Languages',
    'Groovy': 'JVM Languages',
    'Gradle': 'JVM Languages',

    # Systems Languages
    'C': 'Systems Languages',
    'C++': 'Systems Languages',
    'Objective-C': 'Systems Languages',
    'Objective-C++': 'Systems Languages',
    'Swift': 'Systems Languages',

    # Scripting & Data
    'Perl': 'Scripting',
    'Shell': 'Scripting',
    'PowerShell': 'Scripting',
    'R': 'Scripting',
    'Lua': 'Scripting',
    'SQL': 'Database',

    # Functional Languages
    'Clojure': 'Functional',
    'Haskell': 'Functional',
    'Erlang': 'Functional',
    'Elixir': 'Functional',

    # Other Languages
    'Dart': 'Other Languages',

    # Configuration & Data Files
    'JSON': 'Config/Data',
    'YAML': 'Config/Data',
    'XML': 'Config/Data',
    'TOML': 'Config/Data',
    'INI': 'Config/Data',
    'Config': 'Config/Data',
    'Properties': 'Config/Data',
    'Maven POM': 'Config/Data',
    'Env': 'Config/Data',
    'Lock File': 'Config/Data',
    'Dockerfile': 'Config/Data',

    # Documentation
    'Markdown': 'Documentation',
    'ReStructuredText': 'Documentation',
    'AsciiDoc': 'Documentation',
    'LaTeX': 'Documentation',
}

# Binary and compiled files to ignore
BINARY_EXTENSIONS = {
    # Compiled binaries
    '.dll', '.exe', '.pdb', '.o', '.so', '.a', '.dylib',
    '.elf', '.app', '.bin', '.out', '.com',
    # Python
    '.pyc', '.pyo', '.egg-info',
    # Java
    '.class', '.jar',
    # C/C++
    '.o', '.obj', '.lib', '.a', '.so', '.dylib',
    # Archive formats
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
    # Images & Media
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
    '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wav', '.mp3', '.m4a',
    # Office & PDFs
    '.pdf', '.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt',
}

# Directories to completely ignore
IGNORE_DIRS = {
    # Version control
    '.git', '.hg', '.svn', '.bzr',
    # Python
    '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.tox',
    'venv', 'env', '.eggs', 'egg-info',
    # Node.js
    'node_modules', 'npm-debug',
    # .NET
    'bin', 'obj', '.vs', 'packages', '.nuget', 'codex-obj',
    # Ruby
    'Gems', 'vendor', '.bundle',
    # Go
    'vendor', '.vendor',
    # Java
    'target', '.gradle',
    # Build & Distribution
    'dist', 'build', 'release', 'out', 'coverage',
    # Reports & Logs
    '.nyc_output', 'htmlcov', '.coverage', 'coverage',
    # IDE
    '.vscode', '.idea', '.eclipseme', '.vs',
    # OS
    '.DS_Store', 'Thumbs.db', '.AppleDouble',
    # Package managers
    'bower_components', 'components',
    # Docker
    '.docker',
    # Misc build/cache
    '.cache', '.tmp', 'tmp',
}

# Files to ignore (binary or large generated files)
IGNORE_FILES = {
    '.pdb', '.snap',
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
