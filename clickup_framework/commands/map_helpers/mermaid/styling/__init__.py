"""
Styling system for Mermaid diagram generation.

This module provides a comprehensive styling system including color schemes,
theme management, and node styling for Mermaid diagrams.
"""

from .color_schemes import (
    ColorScheme,
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    DEFAULT_NODE_STYLE,
    ENTRY_POINT_STYLE,
    FILE_SUBGRAPH_STYLE,
    CLASS_SUBGRAPH_STYLE
)
from .theme_manager import ThemeManager
from .node_styles import NodeStyler

__all__ = [
    'ColorScheme',
    'DARK_THEME_COLORS',
    'LIGHT_THEME_COLORS',
    'DEFAULT_NODE_STYLE',
    'ENTRY_POINT_STYLE',
    'FILE_SUBGRAPH_STYLE',
    'CLASS_SUBGRAPH_STYLE',
    'ThemeManager',
    'NodeStyler'
]
