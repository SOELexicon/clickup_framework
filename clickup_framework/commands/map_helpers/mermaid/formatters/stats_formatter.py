"""Statistics formatter for Mermaid diagrams.

This module provides utilities for collecting, formatting, and comparing diagram
generation statistics. It standardizes how metrics are reported across all diagram types.

Usage:
    from .stats_formatter import StatsFormatter, DiagramStats

    # Collect stats from generated lines
    stats = StatsFormatter.collect_from_lines(lines)

    # Log summary
    print(f"[INFO] {StatsFormatter.format_summary(stats)}")

    # Get detailed breakdown
    print(StatsFormatter.format_detailed(stats))
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class DiagramStats:
    """Container for diagram generation statistics.

    Attributes:
        node_count: Number of nodes in the diagram
        edge_count: Number of edges (connections) in the diagram
        subgraph_count: Number of subgraphs (nested containers)
        total_lines: Total number of lines in the diagram
        text_size: Total character count of the diagram
        style_count: Number of style definitions
    """

    node_count: int = 0
    edge_count: int = 0
    subgraph_count: int = 0
    total_lines: int = 0
    text_size: int = 0
    style_count: int = 0

    def __str__(self) -> str:
        """Format for console output (concise).

        Returns:
            Formatted string like "Diagram Stats: 42 nodes, 56 edges, 3 subgraphs, 1,234 chars"
        """
        return (
            f"Diagram Stats: "
            f"{self.node_count} nodes, "
            f"{self.edge_count} edges, "
            f"{self.subgraph_count} subgraphs, "
            f"{self.text_size:,} chars"
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for metadata storage.

        Returns:
            Dictionary with all stat fields
        """
        return asdict(self)


class StatsFormatter:
    """Formatter for diagram statistics.

    This class provides static methods for collecting and formatting
    diagram generation statistics in a consistent way across all generators.
    """

    # Regex patterns for stat collection
    _NODE_PATTERNS = [
        re.compile(r'^\s*[A-Z_]\w*[\[(]'),  # Standard nodes: N1[...], DIR0(...), etc.
        re.compile(r'^\s*class\s+\w+'),      # Class definitions in class diagrams
        re.compile(r'^\s*participant\s+'),   # Participants in sequence diagrams
    ]

    _EDGE_PATTERNS = [
        re.compile(r'-->'),     # Directed edge
        re.compile(r'---'),     # Undirected edge
        re.compile(r'\.\.>'),   # Dotted edge
        re.compile(r'==>'),     # Thick edge
        re.compile(r'<-->'),    # Bidirectional edge
    ]

    @staticmethod
    def collect_from_lines(lines: List[str]) -> DiagramStats:
        """Collect statistics from generated diagram lines.

        This method analyzes the diagram content to extract metrics like
        node count, edge count, subgraphs, etc.

        Args:
            lines: List of diagram lines (including fences and metadata)

        Returns:
            DiagramStats object with collected metrics
        """
        # Filter out metadata and fences
        diagram_lines = [
            line for line in lines
            if not line.startswith('#') and
            line.strip() not in ['```mermaid', '```', '']
        ]

        node_count = 0
        edge_count = 0
        subgraph_count = 0
        style_count = 0

        for line in diagram_lines:
            stripped = line.strip()

            # Count nodes
            if any(pattern.match(line) for pattern in StatsFormatter._NODE_PATTERNS):
                node_count += 1

            # Count edges
            if any(pattern.search(line) for pattern in StatsFormatter._EDGE_PATTERNS):
                edge_count += 1

            # Count subgraphs
            if stripped.startswith('subgraph '):
                subgraph_count += 1

            # Count styles
            if stripped.startswith('style '):
                style_count += 1

        return DiagramStats(
            node_count=node_count,
            edge_count=edge_count,
            subgraph_count=subgraph_count,
            total_lines=len(lines),
            text_size=len('\n'.join(lines)),
            style_count=style_count
        )

    @staticmethod
    def format_summary(stats: DiagramStats) -> str:
        """Format concise summary for logging.

        Args:
            stats: DiagramStats object to format

        Returns:
            One-line summary string
        """
        return str(stats)

    @staticmethod
    def format_detailed(stats: DiagramStats) -> str:
        """Format detailed breakdown for verbose output.

        Args:
            stats: DiagramStats object to format

        Returns:
            Multi-line detailed breakdown
        """
        return f"""
Diagram Generation Summary:
  Nodes:     {stats.node_count:>6}
  Edges:     {stats.edge_count:>6}
  Subgraphs: {stats.subgraph_count:>6}
  Styles:    {stats.style_count:>6}
  Lines:     {stats.total_lines:>6}
  Size:      {stats.text_size:>6,} characters
"""

    @staticmethod
    def compare_stats(before: DiagramStats, after: DiagramStats) -> str:
        """Compare two stat sets (useful for refactoring validation).

        This is helpful when refactoring generators to ensure output
        doesn't change unexpectedly.

        Args:
            before: Stats from original implementation
            after: Stats from refactored implementation

        Returns:
            Comparison table showing differences
        """
        def calc_diff(old: int, new: int) -> str:
            """Calculate and format difference."""
            diff = new - old
            if diff == 0:
                return "no change"
            symbol = '+' if diff > 0 else ''
            return f"{symbol}{diff}"

        return f"""
Stats Comparison (Before → After):
  Nodes:     {before.node_count} → {after.node_count} ({calc_diff(before.node_count, after.node_count)})
  Edges:     {before.edge_count} → {after.edge_count} ({calc_diff(before.edge_count, after.edge_count)})
  Subgraphs: {before.subgraph_count} → {after.subgraph_count} ({calc_diff(before.subgraph_count, after.subgraph_count)})
  Size:      {before.text_size:,} → {after.text_size:,} ({calc_diff(before.text_size, after.text_size)})
"""

    @staticmethod
    def validate_equivalence(before: DiagramStats, after: DiagramStats) -> bool:
        """Check if two stat sets are equivalent (for validation).

        Args:
            before: Stats from original implementation
            after: Stats from refactored implementation

        Returns:
            True if stats are equivalent, False otherwise
        """
        return (
            before.node_count == after.node_count and
            before.edge_count == after.edge_count and
            before.subgraph_count == after.subgraph_count
            # Note: total_lines and text_size may differ due to formatting
        )
