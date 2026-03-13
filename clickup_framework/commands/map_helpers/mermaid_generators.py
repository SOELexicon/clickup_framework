"""Mermaid diagram generators for code maps.

**DEPRECATION NOTICE**: The procedural API functions in this module are deprecated
and will be removed in a future release. Please migrate to the class-based generator API.

See MIGRATION_GUIDE.md for migration instructions.
"""

import warnings
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

    .. deprecated::
        Use :class:`FlowchartGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_flowchart(stats, 'output.md', theme='dark')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator
        generator = FlowchartGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    warnings.warn(
        "generate_mermaid_flowchart() is deprecated and will be removed in a future release. "
        "Use FlowchartGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = FlowchartGenerator(stats, output_file, theme)
    generator.generate()


def generate_mermaid_class(stats: Dict, output_file: str) -> None:
    """
    Generate a class diagram showing detailed code structure.

    .. deprecated::
        Use :class:`ClassDiagramGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_class(stats, 'output.md')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import ClassDiagramGenerator
        generator = ClassDiagramGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    warnings.warn(
        "generate_mermaid_class() is deprecated and will be removed in a future release. "
        "Use ClassDiagramGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = ClassDiagramGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_pie(stats: Dict, output_file: str) -> None:
    """
    Generate a pie chart showing language distribution.

    .. deprecated::
        Use :class:`PieChartGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_pie(stats, 'output.md')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator
        generator = PieChartGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    warnings.warn(
        "generate_mermaid_pie() is deprecated and will be removed in a future release. "
        "Use PieChartGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = PieChartGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_mindmap(stats: Dict, output_file: str) -> None:
    """
    Generate a mindmap showing code structure hierarchy.

    .. deprecated::
        Use :class:`MindmapGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_mindmap(stats, 'output.md')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import MindmapGenerator
        generator = MindmapGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    warnings.warn(
        "generate_mermaid_mindmap() is deprecated and will be removed in a future release. "
        "Use MindmapGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = MindmapGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_sequence(stats: Dict, output_file: str) -> None:
    """
    Generate a sequence diagram showing typical execution flow.

    .. deprecated::
        Use :class:`SequenceGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_sequence(stats, 'output.md')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator
        generator = SequenceGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    warnings.warn(
        "generate_mermaid_sequence() is deprecated and will be removed in a future release. "
        "Use SequenceGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = SequenceGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_code_flow(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a code execution flow diagram with hierarchical subgraphs.

    .. deprecated::
        Use :class:`CodeFlowGenerator` instead. This function will be removed in a future release.

    Migration example::

        # Old
        generate_mermaid_code_flow(stats, 'output.md', theme='dark')

        # New
        from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator
        generator = CodeFlowGenerator(stats, 'output.md', theme='dark')
        generator.generate()

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    warnings.warn(
        "generate_mermaid_code_flow() is deprecated and will be removed in a future release. "
        "Use CodeFlowGenerator class instead. "
        "See docs/codemap/MIGRATION_GUIDE.md for migration instructions.",
        DeprecationWarning,
        stacklevel=2
    )
    generator = CodeFlowGenerator(stats, output_file, theme)
    generator.generate()
