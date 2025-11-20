"""
Path utility functions for Mermaid diagram generation.

This module provides helper functions for path manipulation, normalization,
and common path operations used across Mermaid diagram generators.
"""

from pathlib import Path
from typing import List


def normalize_folder_path(path: Path, base_path: Path) -> str:
    """
    Normalize a folder path relative to a base path.

    Handles Windows and Unix path separators, converting them to forward slashes
    for consistent representation in diagrams.

    Args:
        path: The path to normalize
        base_path: The base path to make it relative to

    Returns:
        Normalized path string with forward slashes

    Examples:
        >>> normalize_folder_path(Path("C:/project/src"), Path("C:/project"))
        'src'
        >>> normalize_folder_path(Path("/home/user/project/lib"), Path("/home/user/project"))
        'lib'
    """
    try:
        rel_path = path.relative_to(base_path)
        return str(rel_path).replace('\\', '/')
    except ValueError:
        # Path is not relative to base_path
        return str(path).replace('\\', '/')


def find_common_ancestor(paths: List[Path]) -> Path:
    """
    Find the common ancestor path of multiple absolute paths.

    This function finds the deepest directory that is a parent to all given paths.
    If no common ancestor exists, returns the current working directory.

    Args:
        paths: List of absolute Path objects

    Returns:
        Path object representing the common ancestor directory

    Examples:
        >>> paths = [Path("/project/src/file1.py"), Path("/project/lib/file2.py")]
        >>> find_common_ancestor(paths)
        PosixPath('/project')

    Note:
        Extracted from mermaid_generators.py lines 473-489
    """
    if not paths:
        return Path.cwd()

    if len(paths) == 1:
        return paths[0].parent if paths[0].is_file() else paths[0]

    # Start with parts of first path
    common_parts = list(paths[0].parts)

    # Compare with all other paths
    for path in paths[1:]:
        path_parts = list(path.parts)
        # Find where they diverge
        for i, (a, b) in enumerate(zip(common_parts, path_parts)):
            if a != b:
                common_parts = common_parts[:i]
                break
        else:
            # One path is prefix of another
            common_parts = common_parts[:len(path_parts)]

    if common_parts:
        return Path(*common_parts)
    else:
        return Path.cwd()


def get_base_filename(path: Path) -> str:
    """
    Get the base filename, handling compound extensions.

    Special handling for compound extensions like .razor.cs, .razor.css
    where we want to strip both extensions to get the true base name.

    Args:
        path: Path object to extract base name from

    Returns:
        Base filename without extensions

    Examples:
        >>> get_base_filename(Path("Component.razor.cs"))
        'Component'
        >>> get_base_filename(Path("styles.razor.css"))
        'styles'
        >>> get_base_filename(Path("normal.py"))
        'normal'

    Note:
        Extracted from mermaid_generators.py lines 512-515
    """
    base_name = path.stem  # Gets filename without extension

    # Handle compound extensions like .razor.cs
    if base_name.endswith('.razor'):
        base_name = base_name[:-6]  # Remove '.razor' suffix

    return base_name


def simplify_folder_path(folder: str) -> str:
    """
    Simplify folder path for display in diagrams.

    Converts '.' to 'root' and normalizes path separators to forward slashes.
    Empty strings are also converted to 'root'.

    Args:
        folder: Folder path string to simplify

    Returns:
        Simplified folder path string

    Examples:
        >>> simplify_folder_path('.')
        'root'
        >>> simplify_folder_path('')
        'root'
        >>> simplify_folder_path('src\\utils')
        'src/utils'

    Note:
        Extracted from mermaid_generators.py lines 508-510
    """
    if folder == '.' or folder == '':
        return 'root'

    return folder.replace('\\', '/')
