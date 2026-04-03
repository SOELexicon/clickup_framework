"""Tests for custom node and edge styling API."""

import pytest
from clickup_framework.commands.map_helpers.mermaid.styling import (
    NodeStyle,
    EdgeStyle,
    ColorScheme
)
from clickup_framework.commands.map_helpers.mermaid.generators.base_generator import BaseGenerator
from clickup_framework.commands.map_helpers.mermaid.generators.class_diagram_generator import ClassDiagramGenerator
from clickup_framework.commands.map_helpers.mermaid.generators.flowchart_generator import FlowchartGenerator


class TestNodeStyle:
    """Tests for NodeStyle class."""

    def test_node_style_creation(self):
        """Test creating a NodeStyle object."""
        style = NodeStyle(
            name='test_node',
            fill='#1a1625',
            stroke='#8b5cf6',
            stroke_width='3px',
            text_color='#a855f7'
        )

        assert style.name == 'test_node'
        assert style.fill == '#1a1625'
        assert style.stroke == '#8b5cf6'
        assert style.stroke_width == '3px'
        assert style.text_color == '#a855f7'

    def test_node_style_to_mermaid_style(self):
        """Test converting NodeStyle to Mermaid syntax."""
        style = NodeStyle(
            name='test',
            fill='#0d1f1a',
            stroke='#10b981',
            stroke_width='2px',
            text_color='#10b981'
        )

        mermaid_str = style.to_mermaid_style()
        assert mermaid_str == 'fill:#0d1f1a,stroke:#10b981,stroke-width:2px,color:#10b981'

    def test_node_style_custom_width(self):
        """Test NodeStyle with custom stroke width."""
        style = NodeStyle(
            name='thick',
            fill='#000',
            stroke='#fff',
            stroke_width='5px',
            text_color='#fff'
        )

        mermaid_str = style.to_mermaid_style()
        assert 'stroke-width:5px' in mermaid_str


class TestEdgeStyle:
    """Tests for EdgeStyle class."""

    def test_edge_style_creation(self):
        """Test creating an EdgeStyle object."""
        style = EdgeStyle(
            name='inheritance',
            stroke='#10b981',
            stroke_width='2px',
            stroke_dash='',
            arrow_style='normal'
        )

        assert style.name == 'inheritance'
        assert style.stroke == '#10b981'
        assert style.stroke_width == '2px'
        assert style.stroke_dash == ''
        assert style.arrow_style == 'normal'

    def test_edge_style_to_mermaid_style_solid(self):
        """Test converting solid EdgeStyle to Mermaid syntax."""
        style = EdgeStyle(
            name='solid',
            stroke='#10b981',
            stroke_width='2px'
        )

        mermaid_str = style.to_mermaid_style()
        assert mermaid_str == 'stroke:#10b981,stroke-width:2px'
        assert 'stroke-dasharray' not in mermaid_str

    def test_edge_style_to_mermaid_style_dashed(self):
        """Test converting dashed EdgeStyle to Mermaid syntax."""
        style = EdgeStyle(
            name='dashed',
            stroke='#06b6d4',
            stroke_width='1px',
            stroke_dash='5 5'
        )

        mermaid_str = style.to_mermaid_style()
        assert mermaid_str == 'stroke:#06b6d4,stroke-width:1px,stroke-dasharray:5 5'

    def test_edge_style_defaults(self):
        """Test EdgeStyle default values."""
        style = EdgeStyle(name='test', stroke='#fff')

        assert style.stroke_width == '2px'
        assert style.stroke_dash == ''
        assert style.arrow_style == 'normal'


class TestBaseGeneratorStyling:
    """Tests for BaseGenerator styling methods."""

    class TestGenerator(BaseGenerator):
        """Test generator for testing base styling functionality."""

        def validate_inputs(self, **kwargs):
            pass

        def generate_body(self, **kwargs):
            self._add_diagram_declaration('graph TD')
            self._add_line('    A[Test Node]')

    def test_style_node_default(self):
        """Test default node styling."""
        generator = self.TestGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        style = generator.style_node('TestNode', 'default')
        assert isinstance(style, NodeStyle)
        assert style.name == 'default'

    def test_style_node_entry_point(self):
        """Test entry point node styling."""
        generator = self.TestGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        style = generator.style_node('main', 'entry_point')
        assert isinstance(style, NodeStyle)
        assert style.name == 'entry_point'
        assert style.stroke_width == '3px'  # Thicker border for entry points

    def test_style_node_with_properties(self):
        """Test node styling with properties."""
        generator = self.TestGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        properties = {'complexity': 42, 'is_public': True}
        style = generator.style_node('MyNode', 'default', properties)
        assert isinstance(style, NodeStyle)

    def test_style_edge_default(self):
        """Test default edge styling."""
        generator = self.TestGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        style = generator.style_edge('A->B', 'default')
        assert isinstance(style, EdgeStyle)
        assert style.name == 'default'
        assert style.stroke_width == '2px'

    def test_style_edge_uses_theme_color(self):
        """Test that default edge styling uses theme colors."""
        generator = self.TestGenerator(
            stats={'total_symbols': 0},
            output_file='test.md',
            theme='dark'
        )

        style = generator.style_edge('A->B', 'default')
        assert isinstance(style, EdgeStyle)
        # Theme color should be applied
        assert style.stroke.startswith('#')


class TestClassDiagramGeneratorStyling:
    """Tests for ClassDiagramGenerator custom styling."""

    def test_style_node_base_class(self):
        """Test styling for base classes."""
        generator = ClassDiagramGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        # Test base class identification by name
        style = generator.style_node('BaseController', 'class')
        assert style.name == 'base_class'
        assert style.fill == '#1a1625'  # Purple background
        assert style.stroke == '#8b5cf6'  # Purple border
        assert style.stroke_width == '3px'  # Thicker border

    def test_style_node_base_class_by_property(self):
        """Test styling base classes by property."""
        generator = ClassDiagramGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_node('MyClass', 'class', {'is_base': True})
        assert style.name == 'base_class'
        assert style.stroke_width == '3px'

    def test_style_node_regular_class(self):
        """Test styling for regular classes."""
        generator = ClassDiagramGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        # Regular class should fall back to theme
        style = generator.style_node('RegularClass', 'class')
        assert isinstance(style, NodeStyle)
        assert style.name == 'default'  # Falls back to default

    def test_style_edge_inheritance(self):
        """Test styling for inheritance edges."""
        generator = ClassDiagramGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_edge('BaseClass->DerivedClass', 'inheritance')
        assert style.name == 'inheritance'
        assert style.stroke == '#10b981'  # Green
        assert style.stroke_dash == ''  # Solid line
        assert style.stroke_width == '2px'


class TestFlowchartGeneratorStyling:
    """Tests for FlowchartGenerator custom styling."""

    def test_style_node_directory(self):
        """Test styling for directory nodes."""
        generator = FlowchartGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_node('DIR0', 'directory', {'color_index': 0})
        assert style.name == 'directory'
        assert style.stroke_width == '3px'  # Thicker for directories
        assert isinstance(style, NodeStyle)

    def test_style_node_file(self):
        """Test styling for file nodes."""
        generator = FlowchartGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_node('F0', 'file')
        assert style.name == 'file'
        assert style.fill == '#0c1c20'  # Cyan background
        assert style.stroke == '#06b6d4'  # Cyan border
        assert style.stroke_width == '2px'

    def test_style_node_class(self):
        """Test styling for class nodes."""
        generator = FlowchartGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_node('C0_0', 'class')
        assert style.name == 'class'
        assert style.stroke == '#8b5cf6'  # Purple border
        assert style.stroke_width == '2px'

    def test_style_edge_dir_to_file(self):
        """Test styling for directory to file edges."""
        generator = FlowchartGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_edge('DIR0->F0', 'dir_to_file')
        assert style.name == 'dir_to_file'
        assert style.stroke == '#10b981'  # Green
        assert style.stroke_dash == ''  # Solid
        assert style.stroke_width == '2px'

    def test_style_edge_file_to_class(self):
        """Test styling for file to class edges."""
        generator = FlowchartGenerator(
            stats={'symbols_by_file': {}},
            output_file='test.md'
        )

        style = generator.style_edge('F0->C0_0', 'file_to_class')
        assert style.name == 'file_to_class'
        assert style.stroke == '#06b6d4'  # Cyan
        assert style.stroke_dash == '5 5'  # Dashed
        assert style.stroke_width == '1px'


class TestStylingInheritance:
    """Tests for style method inheritance and fallback behavior."""

    class CustomGenerator(BaseGenerator):
        """Custom generator for testing inheritance."""

        def validate_inputs(self, **kwargs):
            pass

        def generate_body(self, **kwargs):
            pass

        def style_node(self, node_id, node_type='default', properties=None):
            """Override with custom logic."""
            properties = properties or {}

            # Custom styling for 'special' type
            if node_type == 'special':
                return NodeStyle(
                    name='special',
                    fill='#ff0000',
                    stroke='#00ff00',
                    stroke_width='10px',
                    text_color='#0000ff'
                )

            # Fall back to parent for other types
            return super().style_node(node_id, node_type, properties)

    def test_custom_style_applied(self):
        """Test that custom styles are applied correctly."""
        generator = self.CustomGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        style = generator.style_node('Special', 'special')
        assert style.name == 'special'
        assert style.fill == '#ff0000'
        assert style.stroke_width == '10px'

    def test_fallback_to_parent(self):
        """Test that unknown types fall back to parent implementation."""
        generator = self.CustomGenerator(
            stats={'total_symbols': 0},
            output_file='test.md'
        )

        # Should fall back to parent's default styling
        style = generator.style_node('Regular', 'default')
        assert isinstance(style, NodeStyle)
        assert style.name == 'default'


class TestMermaidSyntaxGeneration:
    """Tests for Mermaid syntax generation from styles."""

    def test_node_style_application_syntax(self):
        """Test that node styles generate correct Mermaid syntax."""
        style = NodeStyle(
            name='test',
            fill='#123456',
            stroke='#abcdef',
            stroke_width='2px',
            text_color='#fedcba'
        )

        # Syntax should be: style NodeID fill:...,stroke:...,stroke-width:...,color:...
        mermaid_str = style.to_mermaid_style()
        assert mermaid_str == 'fill:#123456,stroke:#abcdef,stroke-width:2px,color:#fedcba'

    def test_edge_style_application_syntax(self):
        """Test that edge styles generate correct Mermaid linkStyle syntax."""
        style = EdgeStyle(
            name='test',
            stroke='#123456',
            stroke_width='3px',
            stroke_dash='5 5'
        )

        # Syntax should be: linkStyle INDEX stroke:...,stroke-width:...,stroke-dasharray:...
        mermaid_str = style.to_mermaid_style()
        assert mermaid_str == 'stroke:#123456,stroke-width:3px,stroke-dasharray:5 5'

    def test_solid_edge_no_dasharray(self):
        """Test that solid edges don't include stroke-dasharray."""
        style = EdgeStyle(
            name='solid',
            stroke='#fff',
            stroke_width='2px',
            stroke_dash=''
        )

        mermaid_str = style.to_mermaid_style()
        assert 'stroke-dasharray' not in mermaid_str


class TestColorSchemeIntegration:
    """Tests for ColorScheme integration with styling."""

    def test_color_scheme_to_node_style_conversion(self):
        """Test converting ColorScheme to NodeStyle properties."""
        color_scheme = ColorScheme(
            name='test_scheme',
            fill='#111111',
            stroke='#222222',
            text_color='#333333',
            stroke_width='4px'
        )

        # Can create NodeStyle from ColorScheme
        node_style = NodeStyle(
            name='from_scheme',
            fill=color_scheme.fill,
            stroke=color_scheme.stroke,
            stroke_width=color_scheme.stroke_width,
            text_color=color_scheme.text_color
        )

        assert node_style.fill == '#111111'
        assert node_style.stroke == '#222222'
        assert node_style.text_color == '#333333'
        assert node_style.stroke_width == '4px'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
