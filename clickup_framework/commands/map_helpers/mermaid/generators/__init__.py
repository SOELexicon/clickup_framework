"""Mermaid diagram generators.

This module provides generator classes for creating various types of Mermaid diagrams.
All generators inherit from BaseGenerator and follow the template method pattern.

Available Generators:
    BaseGenerator - Abstract base class for all generators (template method pattern)
    FlowchartGenerator - Generate flowchart diagrams showing directory structure
    ClassDiagramGenerator - Generate class diagrams with inheritance
    PieChartGenerator - Generate pie charts showing language distribution
    MindmapGenerator - Generate mindmaps showing code hierarchy
    SequenceGenerator - Generate sequence diagrams showing execution flow
    CodeFlowGenerator - Generate code flow diagrams with subgraphs

Usage:
    from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator

    generator = FlowchartGenerator(stats, output_file, theme='dark')
    generator.generate()
"""

from .base_generator import BaseGenerator
from .flowchart_generator import FlowchartGenerator
from .class_diagram_generator import ClassDiagramGenerator
from .pie_chart_generator import PieChartGenerator
from .mindmap_generator import MindmapGenerator
from .sequence_generator import SequenceGenerator
from .code_flow_generator import CodeFlowGenerator

__all__ = [
    'BaseGenerator',
    'FlowchartGenerator',
    'ClassDiagramGenerator',
    'PieChartGenerator',
    'MindmapGenerator',
    'SequenceGenerator',
    'CodeFlowGenerator',
]
