"""
ThemeManager class for managing and applying color themes to Mermaid diagrams.

This module provides a centralized theme management system that:
- Loads and validates themes from color_schemes.py
- Applies themes consistently across all diagram components
- Provides fallback to default theme for invalid selections
- Generates Mermaid style definitions from theme configurations
- Caches applied themes for performance

Extracted from mermaid_generators.py lines 709-787 (color application logic).

Usage Example:
    from clickup_framework.commands.map_helpers.mermaid.styling import ThemeManager

    # Initialize with default dark theme
    manager = ThemeManager(theme_name='dark')

    # Get color for specific node type
    node_color = manager.apply_to_nodes('entry_point')

    # Generate all Mermaid style definitions
    styles = manager.generate_mermaid_styles()

    # Switch themes at runtime
    manager.set_theme('light')
"""

from typing import List, Tuple, Dict, Optional, Any
from .color_schemes import (
    ColorScheme,
    NodeStyle,
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    DEFAULT_NODE_STYLE,
    ENTRY_POINT_STYLE,
    FILE_SUBGRAPH_STYLE,
    CLASS_SUBGRAPH_STYLE,
    get_color_scheme
)


class ThemeManager:
    """
    Manages theme selection, validation, and application for Mermaid diagrams.

    This class provides a single interface for applying color themes to all
    diagram components, with automatic validation and fallback mechanisms.

    Attributes:
        current_theme: Name of the currently active theme
        _theme_colors: List of available color schemes for current theme
        _node_styles: Dictionary of predefined node styles
        _style_cache: Cache of generated Mermaid style strings
    """

    # Available theme names
    VALID_THEMES = {'dark', 'light'}

    # Default theme to use
    DEFAULT_THEME = 'dark'

    def __init__(self, theme_name: str = 'dark'):
        """
        Initialize ThemeManager with specified theme.

        Args:
            theme_name: Name of theme to use ('dark' or 'light', default: 'dark')

        Raises:
            ValueError: If theme_name is not a valid theme
        """
        self.current_theme: str = self.DEFAULT_THEME
        self._theme_colors: List[ColorScheme] = DARK_THEME_COLORS
        self._node_styles: Dict[str, NodeStyle] = {
            'default': DEFAULT_NODE_STYLE,
            'entry_point': ENTRY_POINT_STYLE,
            'file_subgraph': FILE_SUBGRAPH_STYLE,
            'class_subgraph': CLASS_SUBGRAPH_STYLE
        }
        self._style_cache: Dict[str, str] = {}

        # Set initial theme (validates theme name)
        if not self.set_theme(theme_name):
            # Fallback to default if invalid
            self.set_theme(self.DEFAULT_THEME)

    def set_theme(self, theme_name: str) -> bool:
        """
        Set the active theme.

        Changes the current color scheme to the specified theme.
        Clears the style cache to force regeneration with new colors.

        Args:
            theme_name: Name of theme to activate ('dark' or 'light')

        Returns:
            True if theme was set successfully, False if invalid theme name

        Example:
            >>> manager = ThemeManager()
            >>> manager.set_theme('light')
            True
            >>> manager.current_theme
            'light'
        """
        if theme_name not in self.VALID_THEMES:
            return False

        self.current_theme = theme_name

        # Load appropriate color scheme list
        if theme_name == 'dark':
            self._theme_colors = DARK_THEME_COLORS
        elif theme_name == 'light':
            self._theme_colors = LIGHT_THEME_COLORS

        # Clear style cache
        self._style_cache.clear()

        return True

    def get_theme(self) -> Dict[str, Any]:
        """
        Get current active theme information.

        Returns:
            Dictionary containing theme metadata:
            - name: Current theme name
            - color_count: Number of color schemes available
            - node_styles: List of available node style names

        Example:
            >>> manager = ThemeManager('dark')
            >>> theme = manager.get_theme()
            >>> theme['name']
            'dark'
        """
        return {
            'name': self.current_theme,
            'color_count': len(self._theme_colors),
            'node_styles': list(self._node_styles.keys())
        }

    def apply_to_nodes(self, node_type: str = 'default') -> str:
        """
        Get Mermaid style string for specified node type.

        Returns the complete style definition for a node type,
        using predefined node styles (e.g., entry_point, default).

        Args:
            node_type: Type of node ('default', 'entry_point', etc.)

        Returns:
            Mermaid-compatible style string (e.g., 'fill:#0a0a0a,stroke:#10b981,...')

        Example:
            >>> manager = ThemeManager('dark')
            >>> manager.apply_to_nodes('entry_point')
            'fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7'
        """
        node_style = self._node_styles.get(node_type, DEFAULT_NODE_STYLE)
        return node_style.to_mermaid_style()

    def apply_to_edges(self, edge_type: str = 'default') -> str:
        """
        Get color for edge/connection lines.

        Args:
            edge_type: Type of edge (currently only 'default' supported)

        Returns:
            Hex color string for edges (e.g., '#10b981')

        Example:
            >>> manager = ThemeManager('dark')
            >>> manager.apply_to_edges()
            '#10b981'
        """
        # For now, use the first color scheme's edge color
        # Future: could support different edge colors per type
        return self._theme_colors[0].edge_color()

    def apply_to_subgraph(self, subgraph_type: str) -> str:
        """
        Get Mermaid style string for specified subgraph type.

        Args:
            subgraph_type: Type of subgraph ('file_subgraph', 'class_subgraph', etc.)

        Returns:
            Mermaid-compatible style string for subgraph styling

        Example:
            >>> manager = ThemeManager('dark')
            >>> manager.apply_to_subgraph('file_subgraph')
            'fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981'
        """
        if subgraph_type == 'file_subgraph':
            return FILE_SUBGRAPH_STYLE.to_mermaid_style()
        elif subgraph_type == 'class_subgraph':
            return CLASS_SUBGRAPH_STYLE.to_mermaid_style()
        else:
            # Fallback to default node style
            return DEFAULT_NODE_STYLE.to_mermaid_style()

    def get_color_scheme(self, index: int) -> ColorScheme:
        """
        Get a color scheme by rotation index from current theme.

        This allows cycling through available colors to provide variety
        in diagrams with multiple elements.

        Args:
            index: Rotation index (will wrap around using modulo)

        Returns:
            ColorScheme object from current theme

        Example:
            >>> manager = ThemeManager('dark')
            >>> scheme = manager.get_color_scheme(0)
            >>> scheme.name
            'emerald'
        """
        return self._theme_colors[index % len(self._theme_colors)]

    def generate_mermaid_styles(
        self,
        node_ids: Optional[List[str]] = None,
        color_rotation: Optional[Dict[str, int]] = None
    ) -> List[str]:
        """
        Generate Mermaid style definitions for diagram nodes.

        Creates style statements that can be appended to Mermaid diagrams
        to apply colors to specific nodes based on rotation index.

        Args:
            node_ids: List of node IDs to style (if None, returns empty list)
            color_rotation: Mapping of node_id to color index (if None, no styles generated)

        Returns:
            List of Mermaid style definition strings

        Example:
            >>> manager = ThemeManager('dark')
            >>> styles = manager.generate_mermaid_styles(
            ...     node_ids=['N0', 'N1'],
            ...     color_rotation={'N0': 0, 'N1': 1}
            ... )
            >>> styles[0]
            'style N0 fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px'
        """
        if not node_ids or not color_rotation:
            return []

        styles = []
        for node_id in node_ids:
            if node_id in color_rotation:
                color_idx = color_rotation[node_id]
                color_scheme = self.get_color_scheme(color_idx)
                style_str = f"style {node_id} {color_scheme.to_mermaid_style()}"
                styles.append(style_str)

        return styles

    def validate_theme(self, theme_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a theme dictionary for completeness.

        Checks if a theme dictionary contains all required keys and
        valid color values. Useful for custom theme validation.

        Args:
            theme_dict: Dictionary representing a theme configuration

        Returns:
            Tuple of (is_valid, list_of_missing_keys)

        Example:
            >>> manager = ThemeManager()
            >>> valid, missing = manager.validate_theme({
            ...     'colors': DARK_THEME_COLORS,
            ...     'node_styles': {'default': DEFAULT_NODE_STYLE}
            ... })
            >>> valid
            True
        """
        required_keys = ['colors', 'node_styles']
        missing_keys = []

        for key in required_keys:
            if key not in theme_dict:
                missing_keys.append(key)

        if missing_keys:
            return False, missing_keys

        # Validate colors list
        colors = theme_dict.get('colors', [])
        if not isinstance(colors, list) or len(colors) == 0:
            missing_keys.append('colors (must be non-empty list)')
            return False, missing_keys

        # Validate node_styles dict
        node_styles = theme_dict.get('node_styles', {})
        if not isinstance(node_styles, dict) or 'default' not in node_styles:
            missing_keys.append('node_styles (must contain "default" key)')
            return False, missing_keys

        return True, []

    def list_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available themes with metadata.

        Returns:
            Dictionary mapping theme names to their descriptions and details

        Example:
            >>> manager = ThemeManager()
            >>> themes = manager.list_available_themes()
            >>> 'dark' in themes
            True
        """
        return {
            'dark': {
                'description': 'Dark theme with vibrant colors on dark backgrounds',
                'colors': len(DARK_THEME_COLORS),
                'best_for': 'Developer documentation, dark mode interfaces'
            },
            'light': {
                'description': 'Light theme with muted colors on light backgrounds',
                'colors': len(LIGHT_THEME_COLORS),
                'best_for': 'Print documentation, presentations'
            }
        }
