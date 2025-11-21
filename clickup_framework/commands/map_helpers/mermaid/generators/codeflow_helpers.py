"""Pure utility functions for code flow diagram generation.

This module contains standalone utility functions extracted from TreeBuilder
for better testability and reusability. All functions are pure (no side effects)
and can be used independently.

Extracted from TreeBuilder (tree_builder.py) methods:
- has_functions_in_tree (lines 181-210)
- populate_tree_with_functions (lines 124-179)

Classes:
- SubgraphGenerator: Encapsulates stateful subgraph generation logic
- DirectoryTreeBuilder: Simplified wrapper around TreeBuilder for code flow diagrams
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from pathlib import Path
from ..builders.tree_builder import TreeBuilder


def has_functions_in_tree(tree_node: Dict[str, Any]) -> bool:
    """Check if a tree node or its children have any functions.

    Recursively checks if the current node has files with functions,
    or if any subdirectory has functions. This is a pure function
    with no side effects.

    Args:
        tree_node: A node in the directory tree structure with keys:
            - '__files__': Dict mapping file names to class dicts
            - '__subdirs__': Dict mapping directory names to tree nodes
            Each class dict maps class names to lists of functions

    Returns:
        True if node or any descendant has functions, False otherwise

    Examples:
        >>> # Tree node with functions
        >>> node = {
        ...     '__files__': {'module.py': {'MyClass': ['func1', 'func2']}},
        ...     '__subdirs__': {}
        ... }
        >>> has_functions_in_tree(node)
        True

        >>> # Tree node without functions
        >>> node = {'__files__': {}, '__subdirs__': {}}
        >>> has_functions_in_tree(node)
        False

        >>> # Tree node with nested functions
        >>> node = {
        ...     '__files__': {},
        ...     '__subdirs__': {
        ...         'subdir': {
        ...             '__files__': {'test.py': {'TestClass': ['test_func']}},
        ...             '__subdirs__': {}
        ...         }
        ...     }
        ... }
        >>> has_functions_in_tree(node)
        True

    Note:
        Extracted from TreeBuilder.has_functions_in_tree (tree_builder.py lines 181-210)
    """
    # Check if current node has files with functions
    files_dict = tree_node.get('__files__', {})
    if files_dict:
        # Check if any file has any class with functions
        for file_classes in files_dict.values():
            if any(file_classes.values()):
                return True

    # Check subdirectories recursively
    subdirs = tree_node.get('__subdirs__', {})
    for subdir_node in subdirs.values():
        if has_functions_in_tree(subdir_node):
            return True

    return False


def populate_tree_with_functions(
    dir_tree: Dict[str, Any],
    functions_by_folder: Dict[str, Dict[str, Dict[str, List[str]]]]
) -> Dict[str, Any]:
    """Populate a directory tree with collected functions.

    Matches functions to their locations in the directory tree based on folder paths.
    Functions are organized as: folder -> file -> class -> [functions].
    This is a pure function that modifies and returns the input tree.

    Args:
        dir_tree: Scanned directory structure with keys:
            - '__files__': Dict of files in this directory
            - '__subdirs__': Dict of subdirectories
        functions_by_folder: Collected functions grouped by:
            folder path -> file base name -> class name -> list of function names
            Special folder path 'root' indicates functions at the tree root

    Returns:
        The populated directory tree (same object as dir_tree, modified in place)

    Examples:
        >>> # Basic example with root functions
        >>> tree = {'__files__': {}, '__subdirs__': {}}
        >>> functions = {'root': {'module': {'MyClass': ['func1', 'func2']}}}
        >>> result = populate_tree_with_functions(tree, functions)
        >>> result['__files__']
        {'module': {'MyClass': ['func1', 'func2']}}

        >>> # Example with nested directory
        >>> tree = {
        ...     '__files__': {},
        ...     '__subdirs__': {
        ...         'src': {'__files__': {}, '__subdirs__': {}}
        ...     }
        ... }
        >>> functions = {'src': {'main': {'App': ['run']}}}
        >>> result = populate_tree_with_functions(tree, functions)
        >>> result['__subdirs__']['src']['__files__']
        {'main': {'App': ['run']}}

        >>> # Example with multi-level path
        >>> tree = {
        ...     '__files__': {},
        ...     '__subdirs__': {
        ...         'src': {
        ...             '__files__': {},
        ...             '__subdirs__': {
        ...                 'utils': {'__files__': {}, '__subdirs__': {}}
        ...             }
        ...         }
        ...     }
        ... }
        >>> functions = {'src/utils': {'helpers': {'Helper': ['help']}}}
        >>> result = populate_tree_with_functions(tree, functions)
        >>> result['__subdirs__']['src']['__subdirs__']['utils']['__files__']
        {'helpers': {'Helper': ['help']}}

    Note:
        Extracted from TreeBuilder.populate_tree_with_functions (tree_builder.py lines 124-179)
        Modified to be a pure function by removing dependency on self.base_path
    """
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


class SubgraphGenerator:
    """Encapsulates stateful subgraph generation logic for code flow diagrams.

    This class manages the generation of nested Mermaid subgraphs representing
    directory structure, files, classes, and their functions. It maintains
    state through counters and an output buffer, making the logic more testable
    than the original nested functions with nonlocal variables.

    Extracted from CodeFlowGenerator nested functions (code_flow_generator.py):
    - generate_nested_subgraphs (lines 181-215)
    - generate_file_subgraphs (lines 217-262)

    Attributes:
        node_manager: Manages node ID generation and lookup
        label_formatter: Formats node labels for functions
        collected_symbols: Dictionary mapping function names to their metadata
        max_functions_per_class: Maximum number of functions to display per class
        lines: Accumulated output lines for the diagram
        subgraph_count: Counter for directory subgraph IDs
        file_sg_count: Counter for file subgraph IDs

    Example:
        >>> # Create generator with dependencies
        >>> generator = SubgraphGenerator(
        ...     node_manager=node_mgr,
        ...     label_formatter=formatter,
        ...     collected_symbols=symbols,
        ...     max_functions_per_class=10
        ... )
        >>>
        >>> # Generate subgraphs
        >>> generator.generate_nested_subgraphs(directory_tree)
        >>>
        >>> # Get results
        >>> lines = generator.get_lines()
        >>> sg_count, file_count = generator.get_counts()

    Note:
        This class replaces nonlocal variables with instance state for better
        testability. The output format exactly matches the original nested
        functions.
    """

    def __init__(
        self,
        node_manager: Any,
        label_formatter: Any,
        collected_symbols: Dict[str, Dict[str, Any]],
        max_functions_per_class: int = 10
    ):
        """Initialize SubgraphGenerator with dependencies.

        Args:
            node_manager: Object with get_node_id(func_name) method
            label_formatter: Object with format_function_label(name, symbol) method
            collected_symbols: Dict mapping function names to their metadata
            max_functions_per_class: Maximum functions to show per class (default: 10)
        """
        self.node_manager = node_manager
        self.label_formatter = label_formatter
        self.collected_symbols = collected_symbols
        self.max_functions_per_class = max_functions_per_class

        # State variables (replaces nonlocal from original nested functions)
        self.lines: List[str] = []
        self.subgraph_count: int = 0
        self.file_sg_count: int = 0

    def generate_nested_subgraphs(
        self,
        tree: Dict[str, Any],
        depth: int = 0,
        path_parts: List[str] = None,
        skip_root: bool = True
    ) -> None:
        """Generate nested directory subgraphs recursively.

        Creates hierarchical Mermaid subgraphs for directories, containing
        file subgraphs and nested subdirectory subgraphs. Skips empty
        directories that contain no functions.

        Args:
            tree: Directory tree node with '__files__' and '__subdirs__' keys
            depth: Current nesting depth (default: 0)
            path_parts: Path components from root (default: None, becomes [])
            skip_root: If True, skip creating subgraph for root level (default: True)

        Side Effects:
            - Appends lines to self.lines
            - Increments self.subgraph_count for each directory subgraph
            - Calls generate_file_subgraphs for file processing

        Example:
            >>> tree = {
            ...     '__files__': {'main.py': {'Main': ['run', 'init']}},
            ...     '__subdirs__': {
            ...         'utils': {
            ...             '__files__': {'helpers.py': {'Helper': ['help']}},
            ...             '__subdirs__': {}
            ...         }
            ...     }
            ... }
            >>> generator.generate_nested_subgraphs(tree)
            >>> # Generates subgraphs for root files and utils directory

        Note:
            Extracted from CodeFlowGenerator.generate_nested_subgraphs
            (code_flow_generator.py lines 181-215)
        """
        if path_parts is None:
            path_parts = []

        # Handle root level
        if skip_root and depth == 0:
            files_dict = tree.get('__files__', {})
            if files_dict:
                self.generate_file_subgraphs(files_dict, depth)

            subdirs = tree.get('__subdirs__', {})
            self.generate_nested_subgraphs(subdirs, depth, path_parts, skip_root=False)
            return

        # Process each directory
        for dir_name in sorted(tree.keys()):
            node = tree[dir_name]

            # Skip directories without functions
            if not has_functions_in_tree(node):
                continue

            files_dict = node.get('__files__', {})
            subdirs = node.get('__subdirs__', {})

            # Create directory subgraph
            folder_sg_id = f"SG{self.subgraph_count}"
            self.subgraph_count += 1

            indent = "    " * (depth + 1)
            display_name = f"DIR: {dir_name}"
            self.lines.append(f"{indent}subgraph {folder_sg_id}[\"{display_name}\"]")

            # Process files in this directory
            if files_dict:
                self.generate_file_subgraphs(files_dict, depth + 1)

            # Recursively process subdirectories
            if subdirs:
                self.generate_nested_subgraphs(
                    subdirs,
                    depth + 1,
                    path_parts + [dir_name],
                    skip_root=False
                )

            # Close directory subgraph
            indent = "    " * (depth + 1)
            self.lines.append(f"{indent}end")
            self.lines.append("")

    def generate_file_subgraphs(
        self,
        files_dict: Dict[str, Dict[str, List[str]]],
        depth: int
    ) -> None:
        """Generate file subgraphs with classes and functions.

        Creates Mermaid subgraphs for each file, containing class subgraphs
        (if multiple classes) and function nodes. Respects max_functions_per_class
        limit and skips empty files.

        Args:
            files_dict: Dict mapping file names to class dicts
                Format: {file_name: {class_name: [func1, func2, ...]}}
            depth: Current nesting depth for indentation

        Side Effects:
            - Appends lines to self.lines
            - Increments self.file_sg_count for each file subgraph
            - Creates function nodes using node_manager and label_formatter

        Example:
            >>> files = {
            ...     'service.py': {
            ...         'UserService': ['create_user', 'delete_user'],
            ...         'AdminService': ['grant_access', 'revoke_access']
            ...     }
            ... }
            >>> generator.generate_file_subgraphs(files, depth=1)
            >>> # Generates file subgraph with class subgraphs

        Note:
            Extracted from CodeFlowGenerator.generate_file_subgraphs
            (code_flow_generator.py lines 217-262)
        """
        for base_file_name, classes_dict in sorted(files_dict.items()):
            if not classes_dict:
                continue

            # Create file subgraph
            file_sg_id = f"FSG{self.file_sg_count}"
            self.file_sg_count += 1

            file_indent = "    " * (depth + 1)
            self.lines.append(
                f"{file_indent}subgraph {file_sg_id}[\"FILE: {base_file_name}\"]"
            )

            # Determine if we need class subgraphs
            has_multiple_classes = len([
                c for c in classes_dict.keys()
                if not c.startswith('module_')
            ]) > 1
            class_sg_count = 0

            # Process each class in the file
            for class_name, funcs in sorted(classes_dict.items()):
                if not funcs:
                    continue

                # Create class subgraph if multiple non-module classes
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_sg_id = f"CSG{self.file_sg_count}_{class_sg_count}"
                    class_sg_count += 1
                    class_display = class_name.replace('module_', '')
                    class_indent = "    " * (depth + 2)
                    self.lines.append(
                        f"{class_indent}subgraph {class_sg_id}[\"CLASS: {class_display}\"]"
                    )
                    node_indent = "    " * (depth + 3)
                else:
                    node_indent = "    " * (depth + 2)

                # Add function nodes (up to limit)
                for func_name in funcs[:self.max_functions_per_class]:
                    node_id = self.node_manager.get_node_id(func_name)
                    if not node_id:
                        continue

                    symbol = self.collected_symbols.get(func_name, {})
                    label = self.label_formatter.format_function_label(func_name, symbol)
                    self.lines.append(f"{node_indent}{node_id}[\"{label}\"]")

                # Close class subgraph if we opened one
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_indent = "    " * (depth + 2)
                    self.lines.append(f"{class_indent}end")

            # Close file subgraph
            file_indent = "    " * (depth + 1)
            self.lines.append(f"{file_indent}end")

    def get_lines(self) -> List[str]:
        """Get the accumulated output lines.

        Returns:
            List of Mermaid diagram lines generated by subgraph methods

        Example:
            >>> lines = generator.get_lines()
            >>> for line in lines:
            ...     print(line)
        """
        return self.lines

    def get_counts(self) -> Tuple[int, int]:
        """Get the final subgraph counters.

        Returns:
            Tuple of (subgraph_count, file_sg_count) for tracking
            number of directory and file subgraphs generated

        Example:
            >>> sg_count, file_count = generator.get_counts()
            >>> print(f"Generated {sg_count} dir and {file_count} file subgraphs")
        """
        return (self.subgraph_count, self.file_sg_count)


class DirectoryTreeBuilder:
    """Simplified wrapper around TreeBuilder for code flow diagram generation.

    This class provides a simpler API for directory tree operations used
    specifically by CodeFlowGenerator. It delegates to the full-featured
    TreeBuilder class while exposing only the methods needed for diagram
    generation.

    Wraps TreeBuilder (builders/tree_builder.py) with simplified method names:
    - scan() instead of scan_directory_structure()
    - populate_with_functions() instead of populate_tree_with_functions()

    Attributes:
        base_path: Root directory to scan from
        max_depth: Maximum depth to scan recursively
        exclude_dirs: Set of directory names to exclude from scanning
        _tree_builder: Internal TreeBuilder instance

    Example:
        >>> builder = DirectoryTreeBuilder('/path/to/code', max_depth=3)
        >>> dir_tree = builder.scan()
        >>> builder.populate_with_functions(dir_tree, functions_by_folder)
        >>> # Use the populated tree for diagram generation

    Note:
        This is a simplified wrapper designed for use with CodeFlowGenerator.
        For more advanced tree operations, use TreeBuilder directly.
    """

    def __init__(
        self,
        base_path: str,
        max_depth: int = 5,
        exclude_dirs: Optional[Set[str]] = None
    ):
        """Initialize DirectoryTreeBuilder.

        Args:
            base_path: Root directory to scan from (string or Path object)
            max_depth: Maximum depth to scan recursively (default: 5)
            exclude_dirs: Set of directory names to exclude (default: uses _default_exclude_dirs())

        Example:
            >>> # Basic usage with defaults
            >>> builder = DirectoryTreeBuilder('/my/project')
            >>>
            >>> # Custom depth and exclusions
            >>> builder = DirectoryTreeBuilder(
            ...     '/my/project',
            ...     max_depth=3,
            ...     exclude_dirs={'.git', '__pycache__', 'node_modules'}
            ... )
        """
        self.base_path = Path(base_path) if not isinstance(base_path, Path) else base_path
        self.max_depth = max_depth
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else self._default_exclude_dirs()

        # Create internal TreeBuilder instance
        self._tree_builder = TreeBuilder(
            base_path=str(self.base_path),
            max_depth=self.max_depth,
            exclude_dirs=self.exclude_dirs
        )

    def scan(self) -> Dict[str, Any]:
        """Scan filesystem directory structure to build a directory tree.

        Recursively scans directories up to max_depth, excluding specified
        directories, and marks directories that contain code files.

        Returns:
            Nested dictionary representing directory tree structure with keys:
            - '__files__': Dict of files in this directory
            - '__subdirs__': Dict of subdirectories
            - '__has_code__': Boolean flag indicating if directory has code files

        Example:
            >>> builder = DirectoryTreeBuilder('/my/project')
            >>> tree = builder.scan()
            >>> print(tree.keys())
            dict_keys(['__files__', '__subdirs__', '__has_code__'])

        Note:
            Delegates to TreeBuilder.scan_directory_structure()
        """
        return self._tree_builder.scan_directory_structure()

    def populate_with_functions(
        self,
        dir_tree: Dict[str, Any],
        functions_by_folder: Dict[str, Dict[str, Dict[str, List[str]]]]
    ) -> Dict[str, Any]:
        """Populate the scanned directory tree with collected functions.

        Matches functions to their locations in the directory tree based on
        folder paths. Functions are organized as: folder -> file -> class -> [functions].

        Args:
            dir_tree: Scanned directory structure from scan()
            functions_by_folder: Collected functions grouped by:
                folder path -> file base name -> class name -> list of function names

        Returns:
            The populated directory tree (same object as dir_tree, modified in place)

        Example:
            >>> builder = DirectoryTreeBuilder('/my/project')
            >>> tree = builder.scan()
            >>> functions = {
            ...     'src': {
            ...         'main.py': {
            ...             'Main': ['run', 'init']
            ...         }
            ...     }
            ... }
            >>> populated = builder.populate_with_functions(tree, functions)
            >>> print(populated['__subdirs__']['src']['__files__'])
            {'main.py': {'Main': ['run', 'init']}}

        Note:
            Delegates to TreeBuilder.populate_tree_with_functions()
        """
        return self._tree_builder.populate_tree_with_functions(dir_tree, functions_by_folder)

    @staticmethod
    def _default_exclude_dirs() -> Set[str]:
        """Get the default set of directories to exclude from scanning.

        Returns:
            Set of directory names that should be excluded (version control,
            build artifacts, virtual environments, caches, etc.)

        Example:
            >>> excluded = DirectoryTreeBuilder._default_exclude_dirs()
            >>> '.git' in excluded
            True
            >>> '__pycache__' in excluded
            True

        Note:
            Returns the same default set as TreeBuilder.DEFAULT_EXCLUDE_DIRS
        """
        return TreeBuilder.DEFAULT_EXCLUDE_DIRS.copy()
