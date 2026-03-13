"""Class diagram generator."""

from pathlib import Path
from typing import Dict, Any, Optional
from .base_generator import BaseGenerator
from ..config import get_config
from ..exceptions import DataValidationError
from ..styling import NodeStyle, EdgeStyle


class ClassDiagramGenerator(BaseGenerator):
    """Generate class diagrams showing detailed code structure with inheritance."""

    def __init__(self, *args, **kwargs):
        """Initialize class diagram generator with configuration."""
        super().__init__(*args, **kwargs)
        self.config = get_config().class_diagram

    def validate_inputs(self, **kwargs) -> None:
        """Validate class diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        if not symbols_by_file:
            raise DataValidationError.missing_required_field(
                field_name='symbols_by_file',
                generator_type='class_diagram',
                stats_keys=list(self.stats.keys())
            )

    def generate_body(self, **kwargs) -> None:
        """Generate class diagram body."""
        symbols_by_file = self.stats.get('symbols_by_file', {})

        self._add_diagram_declaration("classDiagram")

        all_classes = {}
        class_count = 0

        for file_path, symbols in sorted(symbols_by_file.items()):
            if class_count >= self.config.max_classes:
                break

            classes = [s for s in symbols if s.get('kind') == 'class']
            for cls in classes:
                class_name = cls.get('name', 'Unknown')

                if class_name in all_classes:
                    continue

                all_classes[class_name] = {
                    'file': Path(file_path).name,
                    'line': cls.get('line', 0),
                    'methods': [],
                    'members': []
                }

                methods = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['function', 'method']]

                members = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['member', 'variable']]

                all_classes[class_name]['methods'] = methods[:self.config.max_methods_per_class]
                all_classes[class_name]['members'] = members[:self.config.max_members_per_class]

                class_count += 1

        for class_name, details in sorted(all_classes.items()):
            self._add_line(f"    class {class_name} {{")
            self._add_line(f"        <<{details['file']}>>")

            for member in details['members']:
                member_name = member.get('name', '')
                self._add_line(f"        -{member_name}")

            for method in details['methods']:
                method_name = method.get('name', '')
                if method_name.startswith('__'):
                    visibility = '-'
                elif method_name.startswith('_'):
                    visibility = '-'
                else:
                    visibility = '+'
                self._add_line(f"        {visibility}{method_name}()")

            self._add_line("    }")

        self._add_line("")
        self._add_line("    %% Inheritance relationships")
        relationships = []
        for class_name in all_classes.keys():
            if 'Base' in class_name:
                for other_class in all_classes.keys():
                    if other_class != class_name and 'Base' not in other_class:
                        if any(word in other_class for word in class_name.replace('Base', '').split()):
                            self._add_line(f"    {class_name} <|-- {other_class}")
                            relationships.append((class_name, other_class))

        # Apply custom styling
        self._apply_custom_styles(all_classes, relationships)

    def style_node(
        self,
        node_id: str,
        node_type: str = 'default',
        properties: Optional[Dict[str, Any]] = None
    ) -> NodeStyle:
        """Custom node styling for class diagrams.

        This demonstrates per-generator styling by distinguishing between
        base classes and derived classes with different visual styles.

        Base classes (containing 'Base' in name):
        - Purple theme: distinctive base class identification
        - Thicker stroke: emphasizes foundation classes

        Derived classes:
        - Green theme: standard class styling
        - Standard stroke: regular visual weight

        Args:
            node_id: Class name
            node_type: Node classification
            properties: Additional properties (e.g., {'is_base': True})

        Returns:
            NodeStyle with custom colors based on class characteristics
        """
        properties = properties or {}

        # Custom logic: style base classes differently
        if 'Base' in node_id or properties.get('is_base', False):
            return NodeStyle(
                name='base_class',
                fill='#1a1625',      # Dark purple background
                stroke='#8b5cf6',     # Bright purple border
                stroke_width='3px',   # Thicker for emphasis
                text_color='#a855f7'  # Lighter purple text
            )

        # Fallback to theme for regular classes
        return super().style_node(node_id, node_type, properties)

    def style_edge(
        self,
        edge_id: str,
        edge_type: str = 'default',
        properties: Optional[Dict[str, Any]] = None
    ) -> EdgeStyle:
        """Custom edge styling for class diagrams.

        Demonstrates edge styling for inheritance relationships with
        distinctive visual properties:
        - Solid lines: Clear inheritance indication
        - Themed colors: Consistent with class styling
        - Standard width: Clean, professional appearance

        Args:
            edge_id: Edge identifier (e.g., 'BaseClass->DerivedClass')
            edge_type: Relationship type ('inheritance', etc.)
            properties: Additional properties

        Returns:
            EdgeStyle for inheritance relationships
        """
        properties = properties or {}

        # Custom styling for inheritance edges
        if edge_type == 'inheritance':
            return EdgeStyle(
                name='inheritance',
                stroke='#10b981',      # Green to match theme
                stroke_width='2px',
                stroke_dash='',        # Solid line for inheritance
                arrow_style='normal'
            )

        # Fallback to theme for other edge types
        return super().style_edge(edge_id, edge_type, properties)

    def _apply_custom_styles(
        self,
        all_classes: Dict[str, Any],
        relationships: list
    ) -> None:
        """Apply custom styling to nodes and edges.

        This method demonstrates how to apply the custom styles defined
        in style_node() and style_edge() to the generated diagram.

        Args:
            all_classes: Dictionary of class names to their details
            relationships: List of (base_class, derived_class) tuples
        """
        self._add_line("")
        self._add_line("    %% Custom styling")

        # Apply node styles
        for class_name in all_classes.keys():
            # Determine node type based on properties
            properties = {'is_base': 'Base' in class_name}
            node_style = self.style_node(class_name, 'class', properties)

            # Generate Mermaid style directive
            style_str = node_style.to_mermaid_style()
            self._add_line(f"    style {class_name} {style_str}")

        # Apply edge styles
        for idx, (base_class, derived_class) in enumerate(relationships):
            edge_id = f"{base_class}->{derived_class}"
            edge_style = self.style_edge(edge_id, 'inheritance')

            # Generate Mermaid linkStyle directive
            style_str = edge_style.to_mermaid_style()
            self._add_line(f"    linkStyle {idx} {style_str}")
