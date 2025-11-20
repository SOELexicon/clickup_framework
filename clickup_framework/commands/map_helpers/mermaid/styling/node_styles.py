"""
NodeStyler class for managing node shapes and structural styling in Mermaid diagrams.

This module provides node shape definitions and formatting separate from color themes,
focusing on the structural appearance of nodes (shapes, borders) rather than colors.

Mermaid Node Shape Reference:
    Rectangle:      N0[Label]
    Rounded:        N0(Label)
    Stadium:        N0([Label])
    Subroutine:     N0[[Label]]
    Cylindrical:    N0[(Label)]
    Circle:         N0((Label))
    Diamond:        N0{Label}
    Hexagon:        N0{{Label}}
    Trapezoid:      N0[/Label/]
    Inv Trapezoid:  N0[\Label\]

Usage Example:
    from clickup_framework.commands.map_helpers.mermaid.styling import NodeStyler

    # Initialize styler
    styler = NodeStyler()

    # Format node declaration with appropriate shape
    node_decl = styler.format_node_declaration('N0', 'main()', 'entry_point')
    # Result: 'N0([main()])'

    # Get shape syntax for custom formatting
    open_tag, close_tag = styler.get_shape('class_method')
    # Result: ('[[', ']]')
"""

from typing import Tuple, List, Dict


class NodeStyler:
    """
    Manages node shapes and structural styling for Mermaid diagrams.

    This class focuses on the structural aspects of node styling (shapes, borders)
    while delegating color management to ThemeManager. It provides consistent
    node shape application across all diagram types.

    Attributes:
        _shape_map: Mapping of node types to (opening, closing) shape syntax
        _border_styles: Mapping of node types to border style names
    """

    def __init__(self):
        """Initialize NodeStyler with default shape mappings."""

        # Map node types to Mermaid shape syntax (opening, closing)
        self._shape_map: Dict[str, Tuple[str, str]] = {
            # Function types
            'entry_point': ('([', '])'),      # Stadium - for entry points/main functions
            'normal': ('(', ')'),              # Rounded rectangle - standard functions
            'class_method': ('[[', ']]'),      # Subroutine - class/instance methods
            'static_method': ('[[', ']]'),     # Subroutine - static methods
            'external': ('[/', '/]'),          # Trapezoid - external/imported functions
            'callback': ('[(', ')]'),          # Cylindrical - callback functions

            # Special states
            'error': ('{', '}'),               # Diamond - error handlers/exceptions
            'deprecated': ('[\\', '\\]'),      # Inv Trapezoid - deprecated functions
            'async': ('{{', '}}'),             # Hexagon - async/await functions

            # Generic shapes
            'rectangle': ('[', ']'),           # Rectangle - generic container
            'circle': ('((', '))'),            # Circle - simple nodes
        }

        # Border style mappings (for use with Mermaid class definitions)
        self._border_styles: Dict[str, str] = {
            'normal': 'solid',
            'external': 'dashed',
            'deprecated': 'dotted',
            'error': 'solid',
            'entry_point': 'solid',
            'class_method': 'solid',
            'static_method': 'solid',
            'callback': 'solid',
            'async': 'solid',
        }

    def get_shape(self, node_type: str = 'normal') -> Tuple[str, str]:
        """
        Get opening and closing shape syntax for specified node type.

        Args:
            node_type: Type of node ('entry_point', 'normal', 'class_method', etc.)
                      Defaults to 'normal' (rounded rectangle)

        Returns:
            Tuple of (opening, closing) shape markers
            Example: ('([', '])') for stadium shape

        Example:
            >>> styler = NodeStyler()
            >>> styler.get_shape('entry_point')
            ('([', '])')
            >>> styler.get_shape('class_method')
            ('[[', ']]')
        """
        return self._shape_map.get(node_type, self._shape_map['normal'])

    def format_node_declaration(
        self,
        node_id: str,
        label: str,
        node_type: str = 'normal'
    ) -> str:
        """
        Format a complete Mermaid node declaration with appropriate shape.

        Generates the Mermaid syntax for defining a node with its label
        and shape based on node type. Automatically escapes special characters
        in labels that could break Mermaid syntax.

        Args:
            node_id: Unique identifier for the node (e.g., 'N0', 'N42')
            label: Display text for the node
            node_type: Type of node determining its shape (default: 'normal')

        Returns:
            Complete Mermaid node declaration string

        Example:
            >>> styler = NodeStyler()
            >>> styler.format_node_declaration('N0', 'main()', 'entry_point')
            'N0([main()])'
            >>> styler.format_node_declaration('N1', 'process_data()', 'normal')
            'N1(process_data())'
            >>> styler.format_node_declaration('N2', 'MyClass.method()', 'class_method')
            'N2[[MyClass.method()]]'
        """
        # Get appropriate shape markers
        open_shape, close_shape = self.get_shape(node_type)

        # Escape special characters that could break Mermaid syntax
        # Quotes need to be escaped in labels
        escaped_label = label.replace('"', '\\"')

        # Format the node declaration
        return f'{node_id}{open_shape}"{escaped_label}"{close_shape}'

    def get_border_style(self, node_type: str = 'normal') -> str:
        """
        Get border style name for specified node type.

        Returns the CSS border style (solid, dashed, dotted) appropriate
        for the given node type. This can be used in Mermaid class definitions.

        Args:
            node_type: Type of node

        Returns:
            Border style name ('solid', 'dashed', or 'dotted')

        Example:
            >>> styler = NodeStyler()
            >>> styler.get_border_style('normal')
            'solid'
            >>> styler.get_border_style('external')
            'dashed'
            >>> styler.get_border_style('deprecated')
            'dotted'
        """
        return self._border_styles.get(node_type, 'solid')

    def generate_style_classes(self) -> List[str]:
        """
        Generate Mermaid classDef statements for all node types.

        Creates Mermaid class definitions that can be applied to nodes
        to set their border styles. These should be included in the
        diagram definition before being referenced.

        Note: This generates only the structural styling (borders).
        Colors should be applied separately via ThemeManager.

        Returns:
            List of Mermaid classDef statements

        Example:
            >>> styler = NodeStyler()
            >>> classes = styler.generate_style_classes()
            >>> classes[0]
            'classDef external stroke-dasharray: 5 5'
        """
        class_defs = []

        # Generate classDef for dashed borders (external functions)
        class_defs.append('classDef external stroke-dasharray: 5 5')

        # Generate classDef for dotted borders (deprecated functions)
        class_defs.append('classDef deprecated stroke-dasharray: 2 2')

        # Could add more class definitions here for other styling aspects
        # (rounded corners, shadows, etc.) but keeping minimal for now

        return class_defs

    def list_available_shapes(self) -> Dict[str, Dict[str, str]]:
        """
        List all available node shapes with descriptions.

        Returns:
            Dictionary mapping node types to their shape info and descriptions

        Example:
            >>> styler = NodeStyler()
            >>> shapes = styler.list_available_shapes()
            >>> shapes['entry_point']['description']
            'Stadium shape for entry points and main functions'
        """
        return {
            'entry_point': {
                'shape': '([Label])',
                'description': 'Stadium shape for entry points and main functions',
                'use_case': 'Main entry points, program starts'
            },
            'normal': {
                'shape': '(Label)',
                'description': 'Rounded rectangle for standard functions',
                'use_case': 'Regular functions and methods'
            },
            'class_method': {
                'shape': '[[Label]]',
                'description': 'Subroutine shape for class methods',
                'use_case': 'Instance methods and class methods'
            },
            'static_method': {
                'shape': '[[Label]]',
                'description': 'Subroutine shape for static methods',
                'use_case': 'Static and utility methods'
            },
            'external': {
                'shape': '[/Label/]',
                'description': 'Trapezoid for external/imported functions',
                'use_case': 'External library calls, API calls'
            },
            'callback': {
                'shape': '[(Label)]',
                'description': 'Cylindrical shape for callback functions',
                'use_case': 'Event handlers, callbacks'
            },
            'error': {
                'shape': '{Label}',
                'description': 'Diamond shape for error handlers',
                'use_case': 'Exception handlers, error states'
            },
            'deprecated': {
                'shape': r'[\Label\]',
                'description': 'Inverted trapezoid for deprecated functions',
                'use_case': 'Deprecated or legacy code'
            },
            'async': {
                'shape': '{{Label}}',
                'description': 'Hexagon for async/await functions',
                'use_case': 'Asynchronous functions and coroutines'
            },
            'rectangle': {
                'shape': '[Label]',
                'description': 'Rectangle for generic containers',
                'use_case': 'Groups, containers, generic nodes'
            },
            'circle': {
                'shape': '((Label))',
                'description': 'Circle for simple nodes',
                'use_case': 'Simple markers, states'
            }
        }

    def get_node_type_for_symbol(
        self,
        symbol_name: str,
        symbol_metadata: Dict = None
    ) -> str:
        """
        Determine appropriate node type based on symbol name and metadata.

        Analyzes function/method characteristics to suggest the most
        appropriate node shape type.

        Args:
            symbol_name: Name of the symbol/function
            symbol_metadata: Optional metadata dict with symbol details

        Returns:
            Suggested node type string

        Example:
            >>> styler = NodeStyler()
            >>> styler.get_node_type_for_symbol('main')
            'entry_point'
            >>> styler.get_node_type_for_symbol('MyClass.method')
            'class_method'
        """
        if symbol_metadata is None:
            symbol_metadata = {}

        # Check for entry points
        if symbol_name in ('main', '__main__', 'run', 'start', 'execute'):
            return 'entry_point'

        # Check for class methods (contains a dot)
        if '.' in symbol_name:
            return 'class_method'

        # Check metadata flags if available
        if symbol_metadata.get('is_async', False):
            return 'async'

        if symbol_metadata.get('is_deprecated', False):
            return 'deprecated'

        if symbol_metadata.get('is_external', False):
            return 'external'

        if symbol_metadata.get('is_callback', False):
            return 'callback'

        if symbol_metadata.get('is_error_handler', False):
            return 'error'

        # Default to normal function
        return 'normal'
