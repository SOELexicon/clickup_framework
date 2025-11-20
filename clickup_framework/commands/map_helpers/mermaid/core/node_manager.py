"""
Node management for diagram generation.

This module handles node creation, ID generation, and organization for Mermaid diagrams.
It coordinates between the metadata store (for rich data) and label formatter (for display).
"""
from typing import Dict, Any, Set, Tuple
from .metadata_store import MetadataStore
from ..formatters.label_formatter import LabelFormatter


class NodeManager:
    """
    Manage node creation, IDs, and organization.

    This class centralizes all node-related operations, ensuring consistent
    ID generation and proper metadata storage.
    """

    def __init__(
        self,
        metadata_store: MetadataStore,
        label_formatter: LabelFormatter = None
    ):
        """
        Initialize node manager.

        Args:
            metadata_store: Metadata storage instance
            label_formatter: Label formatter instance (creates new if None)
        """
        self.node_ids: Dict[str, str] = {}  # func_name -> node_id mapping
        self.node_count = 0
        self.metadata_store = metadata_store
        self.label_formatter = label_formatter or LabelFormatter('minimal')
        self.processed: Set[str] = set()  # Track processed functions
        self.entry_points: Set[str] = set()  # Track entry point functions

    def create_node(
        self,
        func_name: str,
        symbol: Dict[str, Any],
        is_entry_point: bool = False
    ) -> Tuple[str, str]:
        """
        Create a node and return its ID and label.

        Args:
            func_name: Function name (may be qualified)
            symbol: Symbol metadata dictionary
            is_entry_point: Whether this is an entry point function

        Returns:
            Tuple of (node_id, node_label)
        """
        # Check if already created
        if func_name in self.node_ids:
            return self.node_ids[func_name], ''

        # Generate new node ID
        node_id = f'N{self.node_count}'
        self.node_ids[func_name] = node_id
        self.node_count += 1

        # Mark as processed
        self.processed.add(func_name)
        if is_entry_point:
            self.entry_points.add(func_name)

        # Generate label
        node_label = self.label_formatter.format_function_label(
            func_name,
            symbol,
            self.label_formatter.default_format
        )

        # Store metadata separately
        self.metadata_store.add_node_metadata(
            node_id=node_id,
            function=func_name.split('.')[-1],
            class_name=symbol.get('class', ''),
            file=symbol.get('path', '').split('\\')[-1].split('/')[-1],
            line_start=symbol.get('line', 0),
            line_end=symbol.get('end', symbol.get('line', 0)),
            path=symbol.get('path', ''),
            is_entry_point=is_entry_point
        )

        return node_id, node_label

    def get_node_id(self, func_name: str) -> str:
        """
        Get node ID for a function.

        Args:
            func_name: Function name

        Returns:
            Node ID or empty string if not found
        """
        return self.node_ids.get(func_name, '')

    def is_processed(self, func_name: str) -> bool:
        """
        Check if function has been processed.

        Args:
            func_name: Function name

        Returns:
            True if processed, False otherwise
        """
        return func_name in self.processed

    def is_entry_point(self, func_name: str) -> bool:
        """
        Check if function is an entry point.

        Args:
            func_name: Function name

        Returns:
            True if entry point, False otherwise
        """
        return func_name in self.entry_points

    def collect_functions_recursive(
        self,
        entry_point: str,
        function_calls: Dict[str, list],
        all_symbols: Dict[str, Any],
        max_depth: int = 12,
        max_nodes: int = 150,
        current_depth: int = 0
    ) -> Set[str]:
        """
        Recursively collect functions from entry point.

        Args:
            entry_point: Starting function name
            function_calls: Dictionary mapping functions to their calls
            all_symbols: All available symbols
            max_depth: Maximum recursion depth
            max_nodes: Maximum nodes to collect
            current_depth: Current recursion depth

        Returns:
            Set of collected function names
        """
        collected = set()

        # Base cases
        if current_depth >= max_depth:
            return collected

        if len(self.processed) >= max_nodes:
            return collected

        if entry_point in self.processed:
            return collected

        if entry_point not in all_symbols:
            return collected

        # Mark as processed
        self.processed.add(entry_point)
        collected.add(entry_point)

        # Create node
        symbol = all_symbols[entry_point]
        self.create_node(
            entry_point,
            symbol,
            is_entry_point=(current_depth == 0)
        )

        # Recursively process callees (limit to reduce edge count and text size)
        callees = function_calls.get(entry_point, [])[:5]  # Limit to 5 callees per function
        for callee in callees:
            if len(self.processed) >= max_nodes:
                break

            callee_collected = self.collect_functions_recursive(
                callee,
                function_calls,
                all_symbols,
                max_depth,
                max_nodes,
                current_depth + 1
            )
            collected.update(callee_collected)

        return collected

    def get_stats(self) -> Dict[str, int]:
        """
        Get node statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_nodes': self.node_count,
            'entry_points': len(self.entry_points),
            'processed': len(self.processed)
        }

    def reset(self) -> None:
        """Reset node manager state."""
        self.node_ids.clear()
        self.processed.clear()
        self.entry_points.clear()
        self.node_count = 0
