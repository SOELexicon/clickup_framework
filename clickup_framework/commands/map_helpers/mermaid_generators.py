"""Mermaid diagram generators for code maps."""

from typing import Dict
from .mermaid.generators import (
    FlowchartGenerator,
    ClassDiagramGenerator,
    PieChartGenerator,
    MindmapGenerator,
    SequenceGenerator,
    CodeFlowGenerator
)


# ========== Public API Functions (wrappers for backward compatibility) ==========

def generate_mermaid_flowchart(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a mermaid flowchart diagram showing directory structure with symbol details.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    generator = FlowchartGenerator(stats, output_file, theme)
    generator.generate()


def generate_mermaid_class(stats: Dict, output_file: str) -> None:
    """
    Generate a class diagram showing detailed code structure.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = ClassDiagramGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_pie(stats: Dict, output_file: str) -> None:
    """
    Generate a pie chart showing language distribution.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = PieChartGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_mindmap(stats: Dict, output_file: str) -> None:
    """
    Generate a mindmap showing code structure hierarchy.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = MindmapGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_sequence(stats: Dict, output_file: str) -> None:
    """
    Generate a sequence diagram showing typical execution flow.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = SequenceGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_code_flow(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a code execution flow diagram with hierarchical subgraphs.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    generator = CodeFlowGenerator(stats, output_file, theme)
    generator.generate()
