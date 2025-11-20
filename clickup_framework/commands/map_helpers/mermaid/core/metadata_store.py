"""
Centralized metadata storage for diagram nodes.

This module provides a way to store rich metadata about nodes, edges, and subgraphs
separately from the diagram text. This significantly reduces diagram size while
preserving all the detailed information for tooltips, exports, and analysis.
"""
from typing import Dict, Any, Optional, List
import json


class MetadataStore:
    """
    Store and retrieve node metadata separately from diagram.

    This allows diagrams to use minimal labels (e.g., "func_name()") while
    preserving all detailed information (class, file, line numbers, etc.)
    for use in HTML tooltips, JSON exports, and other output formats.
    """

    def __init__(self):
        """Initialize empty metadata storage."""
        self.node_metadata: Dict[str, Dict[str, Any]] = {}
        self.edge_metadata: Dict[str, Dict[str, Any]] = {}
        self.subgraph_metadata: Dict[str, Dict[str, Any]] = {}
        self.stats: Dict[str, Any] = {}

    def add_node_metadata(
        self,
        node_id: str,
        function: str = '',
        class_name: str = '',
        file: str = '',
        line_start: int = 0,
        line_end: int = 0,
        path: str = '',
        is_entry_point: bool = False,
        **kwargs
    ) -> None:
        """
        Add metadata for a node (function, class, file info).

        Args:
            node_id: Unique node identifier (e.g., "N123")
            function: Function name
            class_name: Class or module name
            file: File name (not full path)
            line_start: Starting line number
            line_end: Ending line number
            path: Full file path
            is_entry_point: Whether this is an entry point function
            **kwargs: Additional custom metadata
        """
        self.node_metadata[node_id] = {
            'function': function,
            'class': class_name,
            'file': file,
            'line_start': line_start,
            'line_end': line_end,
            'line_range': f'{line_start}-{line_end}' if line_end > line_start else str(line_start),
            'path': path,
            'is_entry_point': is_entry_point,
            **kwargs
        }

    def add_edge_metadata(
        self,
        from_id: str,
        to_id: str,
        call_type: str = 'direct',
        **kwargs
    ) -> None:
        """
        Add metadata for an edge (call relationship).

        Args:
            from_id: Source node ID
            to_id: Target node ID
            call_type: Type of call (direct, recursive, callback, etc.)
            **kwargs: Additional custom metadata
        """
        edge_key = f'{from_id}->{to_id}'
        self.edge_metadata[edge_key] = {
            'from': from_id,
            'to': to_id,
            'call_type': call_type,
            **kwargs
        }

    def add_subgraph_metadata(
        self,
        subgraph_id: str,
        subgraph_type: str,  # 'dir', 'file', 'class'
        name: str = '',
        path: str = '',
        **kwargs
    ) -> None:
        """
        Add metadata for a subgraph (directory, file, or class).

        Args:
            subgraph_id: Unique subgraph identifier (e.g., "SG0", "FSG1")
            subgraph_type: Type of subgraph ('dir', 'file', 'class')
            name: Display name
            path: Full path (for dir/file) or qualified name (for class)
            **kwargs: Additional custom metadata
        """
        self.subgraph_metadata[subgraph_id] = {
            'type': subgraph_type,
            'name': name,
            'path': path,
            **kwargs
        }

    def set_stats(self, **kwargs) -> None:
        """
        Set overall diagram statistics.

        Args:
            **kwargs: Statistics key-value pairs
        """
        self.stats.update(kwargs)

    def get_node_metadata(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a node.

        Args:
            node_id: Node identifier

        Returns:
            Metadata dictionary or None if not found
        """
        return self.node_metadata.get(node_id)

    def get_edge_metadata(self, from_id: str, to_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for an edge.

        Args:
            from_id: Source node ID
            to_id: Target node ID

        Returns:
            Metadata dictionary or None if not found
        """
        edge_key = f'{from_id}->{to_id}'
        return self.edge_metadata.get(edge_key)

    def get_subgraph_metadata(self, subgraph_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a subgraph.

        Args:
            subgraph_id: Subgraph identifier

        Returns:
            Metadata dictionary or None if not found
        """
        return self.subgraph_metadata.get(subgraph_id)

    def export_json(self, indent: int = 2) -> str:
        """
        Export all metadata as JSON for HTML template.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string with all metadata
        """
        return json.dumps({
            'nodes': self.node_metadata,
            'edges': self.edge_metadata,
            'subgraphs': self.subgraph_metadata,
            'stats': self.stats
        }, indent=indent)

    def export_dict(self) -> Dict[str, Any]:
        """
        Export all metadata as dictionary.

        Returns:
            Dictionary with all metadata
        """
        return {
            'nodes': self.node_metadata,
            'edges': self.edge_metadata,
            'subgraphs': self.subgraph_metadata,
            'stats': self.stats
        }

    def get_stats_summary(self) -> Dict[str, int]:
        """
        Get summary statistics about stored metadata.

        Returns:
            Dictionary with counts
        """
        return {
            'node_count': len(self.node_metadata),
            'edge_count': len(self.edge_metadata),
            'subgraph_count': len(self.subgraph_metadata),
            'entry_point_count': sum(
                1 for node in self.node_metadata.values()
                if node.get('is_entry_point', False)
            )
        }

    def clear(self) -> None:
        """Clear all stored metadata."""
        self.node_metadata.clear()
        self.edge_metadata.clear()
        self.subgraph_metadata.clear()
        self.stats.clear()

    def get_node_tooltip(self, node_id: str) -> str:
        """
        Generate a tooltip string for a node.

        Args:
            node_id: Node identifier

        Returns:
            Formatted tooltip string
        """
        meta = self.get_node_metadata(node_id)
        if not meta:
            return ''

        parts = []
        if meta.get('function'):
            parts.append(f"Function: {meta['function']}()")
        if meta.get('class') and not meta['class'].startswith('module_'):
            parts.append(f"Class: {meta['class']}")
        if meta.get('file'):
            parts.append(f"File: {meta['file']}")
        if meta.get('line_range'):
            parts.append(f"Lines: {meta['line_range']}")
        if meta.get('path'):
            parts.append(f"Path: {meta['path']}")

        return '\n'.join(parts)
