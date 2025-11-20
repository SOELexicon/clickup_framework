"""
Color scheme definitions for Mermaid diagram styling.

This module defines color palettes, themes, and default styles for various
diagram elements including nodes, subgraphs, and edges.

Extracted from mermaid_generators.py lines 709-787.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ColorScheme:
    """
    Represents a color scheme for diagram elements.

    Attributes:
        name: Descriptive name for the color scheme
        fill: Background fill color (hex)
        stroke: Border/stroke color (hex)
        text_color: Text color (hex)
        stroke_width: Border width (CSS unit)
    """
    name: str
    fill: str
    stroke: str
    text_color: str
    stroke_width: str = "2px"

    def to_mermaid_style(self) -> str:
        """
        Convert color scheme to Mermaid style string.

        Returns:
            Mermaid-compatible style string

        Example:
            >>> scheme = ColorScheme('emerald', '#0d1f1a', '#10b981', '#10b981')
            >>> scheme.to_mermaid_style()
            'fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px'
        """
        return f"fill:{self.fill},stroke:{self.stroke},color:{self.text_color},stroke-width:{self.stroke_width}"

    def edge_color(self) -> str:
        """
        Get the color to use for edges/connections.

        Returns:
            Hex color string for edges (typically the stroke color)
        """
        return self.stroke


# Dark Theme Color Schemes
# Extracted from mermaid_generators.py lines 710-716
DARK_THEME_COLORS: List[ColorScheme] = [
    ColorScheme(
        name="emerald",
        fill="#0d1f1a",      # Very dark emerald background
        stroke="#10b981",     # Bright emerald border
        text_color="#10b981"  # Bright emerald text
    ),
    ColorScheme(
        name="purple",
        fill="#1a1625",      # Very dark purple background
        stroke="#8b5cf6",     # Bright purple border
        text_color="#8b5cf6"  # Bright purple text
    ),
    ColorScheme(
        name="cyan",
        fill="#0c1c20",      # Very dark cyan background
        stroke="#06b6d4",     # Bright cyan border
        text_color="#06b6d4"  # Bright cyan text
    ),
    ColorScheme(
        name="amber",
        fill="#211a0d",      # Very dark amber background
        stroke="#f59e0b",     # Bright amber border
        text_color="#f59e0b"  # Bright amber text
    ),
    ColorScheme(
        name="pink",
        fill="#1f0d18",      # Very dark pink background
        stroke="#ec4899",     # Bright pink border
        text_color="#ec4899"  # Bright pink text
    )
]

# Light Theme Color Schemes (for future expansion)
LIGHT_THEME_COLORS: List[ColorScheme] = [
    ColorScheme(
        name="emerald_light",
        fill="#d1fae5",      # Very light emerald background
        stroke="#059669",     # Dark emerald border
        text_color="#047857"  # Dark emerald text
    ),
    ColorScheme(
        name="purple_light",
        fill="#ede9fe",      # Very light purple background
        stroke="#7c3aed",     # Dark purple border
        text_color="#6d28d9"  # Dark purple text
    ),
    ColorScheme(
        name="cyan_light",
        fill="#cffafe",      # Very light cyan background
        stroke="#0891b2",     # Dark cyan border
        text_color="#0e7490"  # Dark cyan text
    ),
    ColorScheme(
        name="amber_light",
        fill="#fef3c7",      # Very light amber background
        stroke="#d97706",     # Dark amber border
        text_color="#b45309"  # Dark amber text
    ),
    ColorScheme(
        name="pink_light",
        fill="#fce7f3",      # Very light pink background
        stroke="#db2777",     # Dark pink border
        text_color="#be185d"  # Dark pink text
    )
]

# Default Node Styles
# Extracted from mermaid_generators.py lines 780-787

@dataclass
class NodeStyle:
    """
    Represents styling for a node type.

    Attributes:
        name: Node type name
        fill: Background color
        stroke: Border color
        stroke_width: Border width
        text_color: Text color
    """
    name: str
    fill: str
    stroke: str
    stroke_width: str
    text_color: str

    def to_mermaid_style(self) -> str:
        """
        Convert node style to Mermaid style string.

        Returns:
            Mermaid-compatible style string
        """
        return f"fill:{self.fill},stroke:{self.stroke},stroke-width:{self.stroke_width},color:{self.text_color}"


# Default style for regular nodes (line 787)
DEFAULT_NODE_STYLE = NodeStyle(
    name="default",
    fill="#0a0a0a",        # Very dark background
    stroke="#10b981",       # Green border
    stroke_width="2px",
    text_color="#10b981"    # Green text
)

# Style for entry point nodes (line 784)
ENTRY_POINT_STYLE = NodeStyle(
    name="entry_point",
    fill="#1a1625",        # Subtle purple background
    stroke="#8b5cf6",       # Purple border
    stroke_width="3px",     # Thicker border for emphasis
    text_color="#a855f7"    # Lighter purple text
)

# Style for file subgraphs (line 771)
FILE_SUBGRAPH_STYLE = NodeStyle(
    name="file_subgraph",
    fill="#1a1a1a",        # Dark background
    stroke="#10b981",       # Green border
    stroke_width="1px",     # Thin border
    text_color="#10b981"    # Green text
)

# Style for class subgraphs (line 778)
CLASS_SUBGRAPH_STYLE = NodeStyle(
    name="class_subgraph",
    fill="#0f0f0f",        # Very dark background
    stroke="#8b5cf6",       # Purple border
    stroke_width="1px",     # Thin border
    text_color="#8b5cf6"    # Purple text
)


def get_color_scheme(index: int, theme: str = "dark") -> ColorScheme:
    """
    Get a color scheme by rotation index.

    This allows cycling through available colors to provide variety
    in diagrams with multiple elements.

    Args:
        index: Rotation index (will wrap around)
        theme: Theme name ('dark' or 'light')

    Returns:
        ColorScheme object

    Example:
        >>> scheme = get_color_scheme(0, 'dark')
        >>> scheme.name
        'emerald'
    """
    colors = DARK_THEME_COLORS if theme == "dark" else LIGHT_THEME_COLORS
    return colors[index % len(colors)]


def list_themes() -> dict:
    """
    List all available themes.

    Returns:
        Dictionary mapping theme names to their descriptions
    """
    return {
        "dark": {
            "description": "Dark theme with vibrant colors on dark backgrounds",
            "colors": len(DARK_THEME_COLORS),
            "best_for": "Developer documentation, dark mode interfaces"
        },
        "light": {
            "description": "Light theme with muted colors on light backgrounds",
            "colors": len(LIGHT_THEME_COLORS),
            "best_for": "Print documentation, presentations"
        }
    }
