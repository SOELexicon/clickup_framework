"""
TreeBuilder class for scanning directory structures and building file trees.

This module provides the TreeBuilder class that handles directory scanning,
tree population with functions, and tree validation for Mermaid diagram generation.

Extracted from mermaid_generators.py lines 339-402, 528-574, 581-596.
"""

from pathlib import Path
from typing import Dict, Set, Optional, Any
from collections import defaultdict


class TreeBuilder:
    """
    Builder class for scanning directory structures and populating function trees.

    This class handles:
    - Recursive directory scanning with depth limits
    - Exclusion of non-code directories
    - Detection of code files by extension
    - Population of directory trees with collected functions
    - Validation of tree nodes for function presence
    """

    # Default code file extensions to detect
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs',
        '.cpp', '.c', '.h', '.go', '.rb', '.php'
    }

    # Default directories to exclude from scanning
    DEFAULT_EXCLUDE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'dist', 'build', '.pytest_cache', '.mypy_cache', 'htmlcov',
        '.tox', 'eggs', '.eggs', 'lib', 'lib64', 'parts', 'sdist',
        'var', 'wheels', '*.egg-info', '.installed.cfg', '*.egg'
    }

    def __init__(
        self,
        base_path: str,
        max_depth: int = 5,
        exclude_dirs: Optional[Set[str]] = None
    ):
        """
        Initialize TreeBuilder.

        Args:
            base_path: Root directory to scan from
            max_depth: Maximum depth to scan recursively (default: 5)
            exclude_dirs: Set of directory names to exclude (default: DEFAULT_EXCLUDE_DIRS)
        """
        self.base_path = Path(base_path)
        self.max_depth = max_depth
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else self.DEFAULT_EXCLUDE_DIRS.copy()

    def scan_directory_structure(self) -> Dict[str, Any]:
        """
        Scan filesystem directory structure to build a directory tree.

        Recursively scans directories up to max_depth, excluding specified directories,
        and marks directories that contain code files.

        Returns:
            Nested dictionary representing directory tree structure with keys:
            - '__files__': Dict of files in this directory
            - '__subdirs__': Dict of subdirectories
            - '__has_code__': Boolean flag indicating if directory has code files

        Note:
            Extracted from mermaid_generators.py lines 339-402
        """
        def scan_dir(current_path: Path, depth: int = 0) -> Optional[Dict[str, Any]]:
            """Recursively scan directory and build tree."""
            if depth >= self.max_depth:
                return None

            # Get relative path from base
            try:
                rel_path = current_path.relative_to(self.base_path)
                parts = list(rel_path.parts) if str(rel_path) != '.' else []
            except ValueError:
                return None

            result = {
                '__files__': {},
                '__subdirs__': {},
                '__has_code__': False
            }

            try:
                entries = list(current_path.iterdir())
            except PermissionError:
                # Handle permission errors gracefully
                return None

            # Check for code files in this directory
            has_code_files = any(
                entry.is_file() and entry.suffix in self.CODE_EXTENSIONS
                for entry in entries
            )
            result['__has_code__'] = has_code_files

            # Scan subdirectories
            for entry in entries:
                if entry.is_dir() and entry.name not in self.exclude_dirs:
                    subdir_result = scan_dir(entry, depth + 1)
                    if subdir_result and (subdir_result['__has_code__'] or subdir_result['__subdirs__']):
                        result['__subdirs__'][entry.name] = subdir_result
                        # Mark parent as having code if child has code
                        result['__has_code__'] = True

            return result

        root_result = scan_dir(self.base_path, 0)
        return root_result if root_result else {
            '__files__': {},
            '__subdirs__': {},
            '__has_code__': False
        }

    def populate_tree_with_functions(
        self,
        dir_tree: Dict[str, Any],
        functions_by_folder: Dict[str, Dict[str, Dict[str, list]]]
    ) -> Dict[str, Any]:
        """
        Populate the scanned directory tree with collected functions.

        Matches functions to their locations in the directory tree based on folder paths.
        Functions are organized as: folder -> file -> class -> [functions]

        Args:
            dir_tree: Scanned directory structure from scan_directory_structure()
            functions_by_folder: Collected functions grouped by folder->file->class

        Returns:
            The populated directory tree

        Note:
            Extracted from mermaid_generators.py lines 529-574
        """
        base_path_str = str(self.base_path)

        # For each folder with functions, find its location in the tree
        for folder_path, files_dict in functions_by_folder.items():
            # Normalize folder path
            if folder_path == 'root':
                # Functions in root go at tree root
                if '__files__' not in dir_tree:
                    dir_tree['__files__'] = {}
                dir_tree['__files__'].update(files_dict)
                continue

            # Split folder path into parts
            parts = folder_path.replace('\\', '/').split('/')

            # Navigate to the correct location in tree
            current = dir_tree
            for part in parts:
                if part == '.' or part == '':
                    continue

                # Look in subdirs
                subdirs = current.get('__subdirs__', {})
                if part in subdirs:
                    current = subdirs[part]
                else:
                    # Directory not in scanned tree, skip these functions
                    break
            else:
                # Successfully navigated to directory, add files
                if '__files__' not in current:
                    current['__files__'] = {}
                current['__files__'].update(files_dict)

        return dir_tree

    def has_functions_in_tree(self, tree_node: Dict[str, Any]) -> bool:
        """
        Check if a tree node or its children have any functions.

        Recursively checks if the current node has files with functions,
        or if any subdirectory has functions.

        Args:
            tree_node: A node in the directory tree structure

        Returns:
            True if node or any descendant has functions, False otherwise

        Note:
            Extracted from mermaid_generators.py lines 581-596
        """
        files_dict = tree_node.get('__files__', {})
        if files_dict:
            # Check if any file has any class with functions
            for file_classes in files_dict.values():
                if any(file_classes.values()):
                    return True

        # Check subdirectories recursively
        subdirs = tree_node.get('__subdirs__', {})
        for subdir_node in subdirs.values():
            if self.has_functions_in_tree(subdir_node):
                return True

        return False
