"""
Mermaid diagram validation helper.

Validates Mermaid diagrams before they're written to ensure they're renderable.
"""
from typing import List, Tuple, Optional
from .mermaid.config import get_config


class MermaidValidationError(Exception):
    """Exception raised when a Mermaid diagram fails validation."""
    pass


def validate_mermaid_diagram(lines: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a Mermaid diagram for common issues.

    Args:
        lines: List of diagram lines

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if mermaid code block is present
    has_opening_fence = any(line.strip() == '```mermaid' for line in lines[:10])
    # Search entire file for closing fence (not just last 20 lines, as statistics can be longer)
    has_closing_fence = any(line.strip() == '```' for line in lines)

    if not has_opening_fence:
        return False, "Missing opening ```mermaid fence"
    if not has_closing_fence:
        return False, "Missing closing ``` fence"

    # Count subgraph opens and closes
    subgraph_opens = sum(1 for line in lines if line.strip().startswith('subgraph '))
    subgraph_closes = sum(1 for line in lines if line.strip() == 'end')

    if subgraph_opens != subgraph_closes:
        return False, f"Unbalanced subgraphs: {subgraph_opens} opens, {subgraph_closes} closes"

    # Check for reasonable diagram size (Mermaid struggles with very large diagrams)
    import re
    node_pattern = re.compile(r'^\s*N\d+\[')
    node_count = sum(1 for line in lines if node_pattern.match(line))
    edge_count = sum(1 for line in lines if '-->' in line or '---' in line)

    # Get validation thresholds from configuration
    validation_config = get_config().validation
    MAX_NODES = validation_config.max_nodes
    MAX_EDGES = validation_config.max_edges
    MAX_SUBGRAPHS = validation_config.max_subgraphs
    MAX_TEXT_SIZE = validation_config.max_text_size

    if node_count > MAX_NODES:
        return False, f"Too many nodes ({node_count}). Limit is {MAX_NODES} for renderable diagrams."

    if edge_count > MAX_EDGES:
        return False, f"Too many edges ({edge_count}). Limit is {MAX_EDGES} for renderable diagrams."

    if subgraph_opens > MAX_SUBGRAPHS:
        return False, f"Too many subgraphs ({subgraph_opens}). Limit is {MAX_SUBGRAPHS} for renderable diagrams."

    # Check total text size
    total_text = '\n'.join(lines)
    text_size = len(total_text)
    if text_size > MAX_TEXT_SIZE:
        return False, f"Total text size ({text_size} chars) exceeds limit of {MAX_TEXT_SIZE} chars. Reduce nodes/edges/depth."

    # Check for valid Mermaid graph declaration
    has_graph_declaration = any(
        line.strip().startswith(('graph ', 'flowchart ', 'sequenceDiagram', 'classDiagram', 'pie ', 'mindmap'))
        for line in lines[:20]
    )

    if not has_graph_declaration:
        return False, "Missing or invalid graph type declaration"

    return True, None


def validate_and_raise(lines: List[str]) -> None:
    """
    Validate a Mermaid diagram and raise an exception if invalid.

    Args:
        lines: List of diagram lines

    Raises:
        MermaidValidationError: If the diagram is invalid
    """
    is_valid, error_msg = validate_mermaid_diagram(lines)
    if not is_valid:
        raise MermaidValidationError(f"Mermaid validation failed: {error_msg}")


def get_diagram_stats(lines: List[str]) -> dict:
    """
    Get statistics about a Mermaid diagram.

    Args:
        lines: List of diagram lines

    Returns:
        Dictionary with diagram statistics
    """
    import re
    node_pattern = re.compile(r'^\s*N\d+\[')
    total_text = '\n'.join(lines)
    return {
        'total_lines': len(lines),
        'node_count': sum(1 for line in lines if node_pattern.match(line)),
        'edge_count': sum(1 for line in lines if '-->' in line or '---' in line),
        'subgraph_count': sum(1 for line in lines if line.strip().startswith('subgraph ')),
        'style_count': sum(1 for line in lines if line.strip().startswith('style ')),
        'text_size': len(total_text),
    }
