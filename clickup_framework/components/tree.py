"""
Tree Formatting Module

Provides utilities for rendering hierarchical data as tree structures with box-drawing characters.
"""

from typing import List, Dict, Any, Callable, Optional


class TreeFormatter:
    """
    Formats hierarchical data as tree structures with box-drawing characters.

    Uses Unicode box-drawing characters for visual hierarchy:
        ├──  Branch (not last item)
        └──  Last branch
        │    Vertical continuation
             Empty space (for completed branches)

    All indentation uses consistent 4-character widths for proper alignment.
    """

    @staticmethod
    def build_tree(
        items: List[Dict[str, Any]],
        format_fn: Callable[[Dict[str, Any]], str],
        get_children_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
        prefix: str = "",
        is_last: bool = True,
        current_depth: int = 0,
        max_depth: Optional[int] = None
    ) -> List[str]:
        """
        Recursively build a tree structure from hierarchical items with optional depth limiting.

        Args:
            items: List of items to display
            format_fn: Function to format each item into a string
            get_children_fn: Function to get children of an item
            prefix: Current indentation prefix
            is_last: Whether this is the last item in its level
            current_depth: Current depth in the tree (0 = root level)
            max_depth: Maximum depth to display (None = unlimited)

        Returns:
            List of formatted lines
        """
        lines = []

        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1)

            # Determine the branch character (with proper spacing: 2 dashes + space)
            branch = "└── " if is_last_item else "├── "

            # Format the current item
            formatted = format_fn(item)

            # Handle multi-line formatted content
            formatted_lines = formatted.split('\n')

            # Add the first line with branch character
            lines.append(f"{prefix}{branch}{formatted_lines[0]}")

            # Get children to determine if we need to continue vertical line
            children = get_children_fn(item)

            # Add remaining lines with proper indentation
            if len(formatted_lines) > 1:
                # Calculate the continuation prefix (4 chars: pipe + 3 spaces or 4 spaces)
                # Show vertical line if: not last item OR has children
                if is_last_item and not children:
                    continuation_prefix = prefix + "    "  # No vertical line, 4 spaces for alignment
                else:
                    continuation_prefix = prefix + "│   "  # Continue vertical line (pipe + 3 spaces)

                for line in formatted_lines[1:]:
                    lines.append(f"{continuation_prefix}{line}")

            if children:
                # Check if we've reached max depth
                if max_depth is not None and current_depth >= max_depth:
                    # Show truncation message
                    # Truncate prefix should align with continuation (4 chars)
                    if is_last_item:
                        truncate_prefix = prefix + "    "
                    else:
                        truncate_prefix = prefix + "│   "

                    hidden_count = len(children)
                    truncate_msg = f"... ({hidden_count} subtask{'s' if hidden_count != 1 else ''} hidden - max depth {max_depth} reached)"
                    lines.append(f"{truncate_prefix}{truncate_msg}")
                else:
                    # Calculate the prefix for children (4 chars: pipe + 3 spaces or 4 spaces)
                    if is_last_item:
                        child_prefix = prefix + "    "  # 4 spaces, no vertical line for last item's children
                    else:
                        child_prefix = prefix + "│   "  # Pipe + 3 spaces to continue vertical line

                    # Recursively format children
                    child_lines = TreeFormatter.build_tree(
                        children,
                        format_fn,
                        get_children_fn,
                        child_prefix,
                        False,
                        current_depth + 1,
                        max_depth
                    )
                    lines.extend(child_lines)

        return lines

    @staticmethod
    def render(
        items: List[Dict[str, Any]],
        format_fn: Callable[[Dict[str, Any]], str],
        get_children_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
        header: Optional[str] = None,
        max_depth: Optional[int] = None,
        show_root_connector: bool = False
    ) -> str:
        """
        Render items as a tree structure with optional depth limiting and root connector.

        Args:
            items: List of root items
            format_fn: Function to format each item
            get_children_fn: Function to get children of an item
            header: Optional header to display before the tree
            max_depth: Maximum depth to display (None = unlimited)
            show_root_connector: If True, adds a vertical connector from header to root

        Returns:
            Complete tree as a string
        """
        lines = []

        if header:
            lines.append(header)
            if show_root_connector:
                lines.append("│")  # Add connecting line from header to tree
            else:
                lines.append("")

        tree_lines = TreeFormatter.build_tree(
            items,
            format_fn,
            get_children_fn,
            max_depth=max_depth
        )
        lines.extend(tree_lines)

        return "\n".join(lines)

    @staticmethod
    def format_container_tree(
        containers: List[Dict[str, Any]],
        format_container_fn: Callable[[Dict[str, Any]], str],
        format_item_fn: Callable[[Dict[str, Any]], str],
        get_sub_containers_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
        get_items_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
        prefix: str = "",
        is_last: bool = True
    ) -> List[str]:
        """
        Build a tree with containers (e.g., folders) and items (e.g., tasks).

        Args:
            containers: List of containers to display
            format_container_fn: Function to format container
            format_item_fn: Function to format items
            get_sub_containers_fn: Function to get sub-containers
            get_items_fn: Function to get items in a container
            prefix: Current indentation prefix
            is_last: Whether this is the last container

        Returns:
            List of formatted lines
        """
        lines = []

        for i, container in enumerate(containers):
            is_last_container = (i == len(containers) - 1)

            # Determine the branch character (with proper spacing: 2 dashes + space)
            branch = "└── " if is_last_container else "├── "

            # Format the container
            formatted_container = format_container_fn(container)
            lines.append(f"{prefix}{branch}{formatted_container}")

            # Calculate prefix for children (4 chars: pipe + 3 spaces or 4 spaces)
            if is_last_container:
                child_prefix = prefix + "    "  # 4 spaces
            else:
                child_prefix = prefix + "│   "  # Pipe + 3 spaces

            # Get sub-containers
            sub_containers = get_sub_containers_fn(container)
            if sub_containers:
                sub_lines = TreeFormatter.format_container_tree(
                    sub_containers,
                    format_container_fn,
                    format_item_fn,
                    get_sub_containers_fn,
                    get_items_fn,
                    child_prefix,
                    False
                )
                lines.extend(sub_lines)

            # Get items in this container
            items = get_items_fn(container)
            if items:
                for j, item in enumerate(items):
                    is_last_item = (j == len(items) - 1) and not sub_containers

                    item_branch = "└── " if is_last_item else "├── "
                    formatted_item = format_item_fn(item)
                    lines.append(f"{child_prefix}{item_branch}{formatted_item}")

        return lines
