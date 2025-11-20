"""
SubgraphBuilder class for generating nested Mermaid subgraphs.

This module provides the SubgraphBuilder class that generates nested directory,
file, and class subgraphs for Mermaid diagrams with proper indentation and ID management.

Extracted from mermaid_generators.py lines 598-704.
"""

from typing import Dict, List, Any
from ..core.node_manager import NodeManager
from ..formatters.label_formatter import LabelFormatter


class SubgraphBuilder:
    """
    Builder class for generating nested Mermaid subgraphs.

    This class handles:
    - Nested directory subgraphs (SG0, SG1, ...)
    - File component subgraphs (FSG0, FSG1, ...)
    - Class subgraphs when multiple classes exist (CSG0_0, CSG0_1, ...)
    - Proper indentation based on nesting depth
    - Integration with NodeManager for node IDs and LabelFormatter for labels
    """

    def __init__(
        self,
        node_manager: NodeManager,
        label_formatter: LabelFormatter,
        collected_symbols: Dict[str, Any]
    ):
        """
        Initialize SubgraphBuilder.

        Args:
            node_manager: NodeManager instance for node ID lookup
            label_formatter: LabelFormatter instance for label generation
            collected_symbols: Dictionary of all collected symbols
        """
        self.node_manager = node_manager
        self.label_formatter = label_formatter
        self.collected_symbols = collected_symbols

        # Subgraph counters for ID generation
        self.subgraph_count = 0
        self.file_sg_count = 0

    def generate_nested_subgraphs(
        self,
        tree: Dict[str, Any],
        depth: int = 0,
        path_parts: List[str] = None,
        skip_root: bool = True
    ) -> List[str]:
        """
        Recursively generate nested subgraphs for directory hierarchy.

        Generates Mermaid subgraph syntax for directories, files, and classes,
        with proper indentation based on nesting depth.

        Args:
            tree: Directory tree structure from TreeBuilder
            depth: Current nesting depth (for indentation)
            path_parts: List of path components (for tracking location)
            skip_root: If True, skip creating subgraph for root level

        Returns:
            List of Mermaid diagram lines

        Note:
            Extracted from mermaid_generators.py lines 598-645
        """
        if path_parts is None:
            path_parts = []

        lines = []

        # Handle root level specially
        if skip_root and depth == 0:
            # Process root's files and subdirs directly without creating root subgraph
            files_dict = tree.get('__files__', {})
            if files_dict:
                # Generate file subgraphs at root level
                file_lines = self._generate_file_subgraphs(files_dict, depth)
                lines.extend(file_lines)

            subdirs = tree.get('__subdirs__', {})
            subdir_lines = self.generate_nested_subgraphs(
                subdirs,
                depth,
                path_parts,
                skip_root=False
            )
            lines.extend(subdir_lines)
            return lines

        # Normal processing for non-root levels
        for dir_name in sorted(tree.keys()):
            node = tree[dir_name]

            # Skip if no functions in this branch
            if not self._has_functions_in_tree(node):
                continue

            files_dict = node.get('__files__', {})
            subdirs = node.get('__subdirs__', {})

            # Create subgraph for this directory
            folder_sg_id = f"SG{self.subgraph_count}"
            self.subgraph_count += 1

            indent = "    " * depth
            lines.append(f"{indent}subgraph {folder_sg_id}[\"DIR: {dir_name}\"]")

            # Generate file subgraphs in this directory
            if files_dict:
                file_lines = self._generate_file_subgraphs(files_dict, depth)
                lines.extend(file_lines)

            # Recursively process subdirectories
            if subdirs:
                subdir_lines = self.generate_nested_subgraphs(
                    subdirs,
                    depth + 1,
                    path_parts + [dir_name],
                    skip_root=False
                )
                lines.extend(subdir_lines)

            # Close directory subgraph
            lines.append(f"{indent}end")

        return lines

    def _generate_file_subgraphs(
        self,
        files_dict: Dict[str, Dict[str, List[str]]],
        depth: int
    ) -> List[str]:
        """
        Generate file and class subgraphs with function nodes.

        Creates file component subgraphs (FSG) and optionally class subgraphs (CSG)
        when multiple classes exist in the same file.

        Args:
            files_dict: Dictionary of files with their classes and functions
                       Structure: {file_name: {class_name: [func_names]}}
            depth: Current nesting depth (for indentation)

        Returns:
            List of Mermaid diagram lines

        Note:
            Extracted from mermaid_generators.py lines 647-704
        """
        lines = []

        # Iterate through file components in this folder
        for base_file_name, classes_dict in sorted(files_dict.items()):
            if not classes_dict:
                continue

            # Create nested file component subgraph
            file_sg_id = f"FSG{self.file_sg_count}"
            self.file_sg_count += 1

            file_indent = "    " * (depth + 1)
            lines.append(f"{file_indent}subgraph {file_sg_id}[\"FILE: {base_file_name}\"]")

            # Check if there are multiple classes - if so, create class subgraphs
            has_multiple_classes = len([
                c for c in classes_dict.keys()
                if not c.startswith('module_')
            ]) > 1
            class_sg_count = 0

            # Add all functions from all classes in this file component
            for class_name, funcs in sorted(classes_dict.items()):
                if not funcs:
                    continue

                # If multiple classes exist and this is a real class (not module_), create class subgraph
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_sg_id = f"CSG{self.file_sg_count}_{class_sg_count}"
                    class_sg_count += 1
                    class_display = class_name.replace('module_', '')
                    class_indent = "    " * (depth + 2)
                    lines.append(f"{class_indent}subgraph {class_sg_id}[\"CLASS: {class_display}\"]")
                    node_indent = "    " * (depth + 3)
                else:
                    node_indent = "    " * (depth + 2)

                # Add function nodes (limit to 50 per file)
                for func_name in funcs[:50]:
                    # Get node ID from NodeManager (already created during collection)
                    node_id = self.node_manager.get_node_id(func_name)
                    if not node_id:
                        continue  # Skip if node wasn't created

                    # Get label from formatter
                    symbol = self.collected_symbols.get(func_name, {})
                    label = self.label_formatter.format_function_label(func_name, symbol)

                    # Add node to diagram with label
                    lines.append(f"{node_indent}{node_id}[\"{label}\"]")

                    # Metadata is already stored in metadata_store via NodeManager

                # Close class subgraph if we created one
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_indent = "    " * (depth + 2)
                    lines.append(f"{class_indent}end")

            file_indent = "    " * (depth + 1)
            lines.append(f"{file_indent}end")  # Close file component subgraph

        return lines

    def _has_functions_in_tree(self, tree_node: Dict[str, Any]) -> bool:
        """
        Check if a tree node or its children have any functions.

        This is a helper method used internally to determine if a directory
        should have a subgraph created for it.

        Args:
            tree_node: A node in the directory tree structure

        Returns:
            True if node or any descendant has functions, False otherwise
        """
        files_dict = tree_node.get('__files__', {})
        if files_dict:
            # Check if any file has any class with functions
            for file_classes in files_dict.values():
                if any(file_classes.values()):
                    return True

        # Check subdirectories
        subdirs = tree_node.get('__subdirs__', {})
        for subdir_node in subdirs.values():
            if self._has_functions_in_tree(subdir_node):
                return True

        return False

    def reset_counters(self) -> None:
        """
        Reset subgraph counters.

        Useful when generating multiple diagrams and you want to start
        subgraph numbering from 0 again.
        """
        self.subgraph_count = 0
        self.file_sg_count = 0
