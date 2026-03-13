# Mermaid Generator Styling API Guide

## Overview

The Mermaid generator framework provides a flexible styling system that allows individual generators to customize node and edge appearance beyond global theme settings. This guide explains how to implement custom styling in your generator.

## Architecture

The styling system consists of three layers:

1. **Global Themes** (`ThemeManager`): Provides consistent color schemes across all diagrams
2. **Default Styles** (`NodeStyle`, `EdgeStyle`): Predefined styles for common elements
3. **Per-Generator Customization**: Override `style_node()` and `style_edge()` in your generator

This layered approach allows you to:
- Use global themes as a foundation
- Apply generator-specific styling logic
- Conditionally style elements based on their properties

## Core Classes

### NodeStyle

Represents styling for a diagram node.

```python
from clickup_framework.commands.map_helpers.mermaid.styling import NodeStyle

style = NodeStyle(
    name='my_node',
    fill='#1a1625',        # Background color (hex)
    stroke='#8b5cf6',      # Border color (hex)
    stroke_width='3px',    # Border width (CSS unit)
    text_color='#a855f7'   # Text color (hex)
)

# Convert to Mermaid syntax
mermaid_str = style.to_mermaid_style()
# Result: "fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7"
```

### EdgeStyle

Represents styling for connections between nodes.

```python
from clickup_framework.commands.map_helpers.mermaid.styling import EdgeStyle

style = EdgeStyle(
    name='inheritance',
    stroke='#10b981',        # Line color (hex)
    stroke_width='2px',      # Line width (CSS unit)
    stroke_dash='',          # Dash pattern: '' (solid), '5 5' (dashed), '2 2' (dotted)
    arrow_style='normal'     # Arrow style: 'normal', 'thick', 'dotted'
)

# Convert to Mermaid syntax
mermaid_str = style.to_mermaid_style()
# Result: "stroke:#10b981,stroke-width:2px"
```

## Implementing Custom Styling

### Step 1: Import Required Classes

```python
from typing import Dict, Any, Optional
from .base_generator import BaseGenerator
from ..styling import NodeStyle, EdgeStyle
```

### Step 2: Override style_node()

The `style_node()` method determines the visual appearance of nodes based on their type and properties.

**Method Signature:**
```python
def style_node(
    self,
    node_id: str,
    node_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> NodeStyle:
    """
    Args:
        node_id: Unique identifier for the node (e.g., 'MyClass', 'DIR0')
        node_type: Classification (e.g., 'class', 'directory', 'file')
        properties: Additional data for conditional styling

    Returns:
        NodeStyle object defining colors and borders
    """
```

**Example - Class Diagram Generator:**

```python
def style_node(
    self,
    node_id: str,
    node_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> NodeStyle:
    """Style base classes differently from derived classes."""
    properties = properties or {}

    # Custom logic: purple theme for base classes
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
```

**Example - Flowchart Generator:**

```python
def style_node(
    self,
    node_id: str,
    node_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> NodeStyle:
    """Style nodes hierarchically."""
    properties = properties or {}

    if node_type == 'directory':
        # Rotate colors for directories
        color_index = properties.get('color_index', 0)
        color_scheme = self.theme_manager.get_color_scheme(color_index)
        return NodeStyle(
            name='directory',
            fill=color_scheme.fill,
            stroke=color_scheme.stroke,
            stroke_width='3px',
            text_color=color_scheme.text_color
        )
    elif node_type == 'file':
        # Cyan theme for files
        return NodeStyle(
            name='file',
            fill='#0c1c20',
            stroke='#06b6d4',
            stroke_width='2px',
            text_color='#06b6d4'
        )

    return super().style_node(node_id, node_type, properties)
```

### Step 3: Override style_edge()

The `style_edge()` method determines the appearance of connections based on relationship type.

**Method Signature:**
```python
def style_edge(
    self,
    edge_id: str,
    edge_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> EdgeStyle:
    """
    Args:
        edge_id: Identifier (e.g., 'BaseClass->DerivedClass')
        edge_type: Relationship classification (e.g., 'inheritance', 'call')
        properties: Additional data for conditional styling

    Returns:
        EdgeStyle object defining line appearance
    """
```

**Example - Class Diagram Generator:**

```python
def style_edge(
    self,
    edge_id: str,
    edge_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> EdgeStyle:
    """Style inheritance edges."""
    properties = properties or {}

    if edge_type == 'inheritance':
        return EdgeStyle(
            name='inheritance',
            stroke='#10b981',      # Green to match theme
            stroke_width='2px',
            stroke_dash='',        # Solid line
            arrow_style='normal'
        )

    return super().style_edge(edge_id, edge_type, properties)
```

**Example - Flowchart Generator:**

```python
def style_edge(
    self,
    edge_id: str,
    edge_type: str = 'default',
    properties: Optional[Dict[str, Any]] = None
) -> EdgeStyle:
    """Distinguish hierarchy from containment."""
    properties = properties or {}

    if edge_type == 'dir_to_file':
        # Solid green for structural hierarchy
        return EdgeStyle(
            name='dir_to_file',
            stroke='#10b981',
            stroke_width='2px',
            stroke_dash='',
            arrow_style='normal'
        )
    elif edge_type == 'file_to_class':
        # Dashed cyan for containment
        return EdgeStyle(
            name='file_to_class',
            stroke='#06b6d4',
            stroke_width='1px',
            stroke_dash='5 5',     # Dashed
            arrow_style='normal'
        )

    return super().style_edge(edge_id, edge_type, properties)
```

### Step 4: Apply Styles in generate_body()

After generating nodes and edges, apply the custom styles using Mermaid syntax.

**For Nodes:**
```python
# Apply node style
node_style = self.style_node(node_id, 'class', {'is_base': True})
style_str = node_style.to_mermaid_style()
self._add_line(f"    style {node_id} {style_str}")
```

**For Edges:**
```python
# Apply edge style (linkStyle uses zero-based index)
edge_style = self.style_edge('A->B', 'inheritance')
style_str = edge_style.to_mermaid_style()
self._add_line(f"    linkStyle {edge_index} {style_str}")
```

**Complete Example:**

```python
def generate_body(self, **kwargs) -> None:
    # ... generate nodes and edges ...

    # Track for styling
    node_list = []
    edge_list = []

    # Example: create a node
    self._add_line(f"    MyClass[My Class]")
    node_list.append(('MyClass', 'class', {'is_base': False}))

    # Example: create an edge
    self._add_line(f"    BaseClass <|-- MyClass")
    edge_list.append(('BaseClass', 'MyClass', 'inheritance'))

    # Apply custom styles
    self._apply_custom_styles(node_list, edge_list)

def _apply_custom_styles(
    self,
    node_list: List[Tuple[str, str, Dict]],
    edge_list: List[Tuple[str, str, str]]
) -> None:
    """Apply custom styling to nodes and edges."""
    self._add_line("")
    self._add_line("    %% Custom styling")

    # Apply node styles
    for node_id, node_type, properties in node_list:
        node_style = self.style_node(node_id, node_type, properties)
        style_str = node_style.to_mermaid_style()
        self._add_line(f"    style {node_id} {style_str}")

    # Apply edge styles
    for idx, (from_node, to_node, edge_type) in enumerate(edge_list):
        edge_id = f"{from_node}->{to_node}"
        edge_style = self.style_edge(edge_id, edge_type)
        style_str = edge_style.to_mermaid_style()
        self._add_line(f"    linkStyle {idx} {style_str}")
```

## Best Practices

### 1. Always Provide Fallback

Always call `super().style_node()` or `super().style_edge()` for unhandled cases to ensure theme consistency.

```python
def style_node(self, node_id, node_type='default', properties=None):
    # Your custom logic...

    # Fallback to theme
    return super().style_node(node_id, node_type, properties)
```

### 2. Use Properties for Conditional Styling

Pass relevant data through the `properties` dictionary to make informed styling decisions.

```python
# When creating nodes
properties = {
    'complexity': 42,
    'is_public': True,
    'line_count': 150
}
node_style = self.style_node(node_id, 'function', properties)

# In style_node()
if properties.get('complexity', 0) > 20:
    return high_complexity_style
```

### 3. Maintain Visual Hierarchy

Use consistent styling patterns to establish visual hierarchy:
- **Thickness**: More important elements = thicker borders
- **Brightness**: Key elements = brighter colors
- **Line Style**: Solid = strong relationship, dashed = weak relationship

```python
# Important base classes
stroke_width='3px'  # Thick border

# Regular classes
stroke_width='2px'  # Standard border

# Utility classes
stroke_width='1px'  # Thin border
```

### 4. Document Your Styling Logic

Add clear docstrings explaining your styling rules:

```python
def style_node(self, node_id, node_type='default', properties=None):
    """Custom node styling for class diagrams.

    Styling Rules:
    - Base classes (containing 'Base' in name): Purple theme, 3px borders
    - Abstract classes: Orange theme, 2px borders
    - Concrete classes: Green theme (from global theme), 2px borders

    Properties Used:
    - is_base (bool): Whether this is a base class
    - is_abstract (bool): Whether this is an abstract class
    """
```

### 5. Test with Different Themes

Ensure your custom styles work well with both dark and light themes.

```python
# Access current theme
theme = self.theme_manager.current_theme  # 'dark' or 'light'

# Adjust styling based on theme
if theme == 'light':
    return lighter_style
else:
    return darker_style
```

## Color Palette Reference

### Dark Theme Colors

```python
# Emerald (Default)
fill='#0d1f1a'
stroke='#10b981'
text_color='#10b981'

# Purple
fill='#1a1625'
stroke='#8b5cf6'
text_color='#8b5cf6'

# Cyan
fill='#0c1c20'
stroke='#06b6d4'
text_color='#06b6d4'

# Amber
fill='#211a0d'
stroke='#f59e0b'
text_color='#f59e0b'

# Pink
fill='#1f0d18'
stroke='#ec4899'
text_color='#ec4899'
```

### Light Theme Colors

```python
# Emerald Light
fill='#d1fae5'
stroke='#059669'
text_color='#047857'

# Purple Light
fill='#ede9fe'
stroke='#7c3aed'
text_color='#6d28d9'

# Cyan Light
fill='#cffafe'
stroke='#0891b2'
text_color='#0e7490'

# Amber Light
fill='#fef3c7'
stroke='#d97706'
text_color='#b45309'

# Pink Light
fill='#fce7f3'
stroke='#db2777'
text_color='#be185d'
```

## Advanced Techniques

### Dynamic Color Rotation

Use indexed colors for variety in repetitive elements:

```python
def style_node(self, node_id, node_type='default', properties=None):
    properties = properties or {}

    if node_type == 'directory':
        # Rotate through color schemes
        index = properties.get('color_index', 0)
        color_scheme = self.theme_manager.get_color_scheme(index)
        return NodeStyle(
            name='directory',
            fill=color_scheme.fill,
            stroke=color_scheme.stroke,
            stroke_width='2px',
            text_color=color_scheme.text_color
        )
```

### Metric-Based Styling

Style elements based on quantitative metrics:

```python
def style_node(self, node_id, node_type='default', properties=None):
    properties = properties or {}

    # Color code by complexity
    complexity = properties.get('complexity', 0)

    if complexity > 50:
        # High complexity = red
        return NodeStyle('high_complexity', '#2d1b1b', '#ef4444', '3px', '#ef4444')
    elif complexity > 20:
        # Medium complexity = amber
        return NodeStyle('med_complexity', '#211a0d', '#f59e0b', '2px', '#f59e0b')
    else:
        # Low complexity = green (theme)
        return super().style_node(node_id, node_type, properties)
```

### Relationship Strength Visualization

Vary edge appearance based on relationship strength:

```python
def style_edge(self, edge_id, edge_type='default', properties=None):
    properties = properties or {}

    # Vary line width and dash pattern by call frequency
    call_count = properties.get('call_count', 0)

    if call_count > 100:
        # Frequent calls = thick solid line
        return EdgeStyle('frequent', '#10b981', '3px', '', 'thick')
    elif call_count > 10:
        # Moderate calls = standard line
        return EdgeStyle('moderate', '#06b6d4', '2px', '', 'normal')
    else:
        # Rare calls = thin dashed line
        return EdgeStyle('rare', '#8b5cf6', '1px', '5 5', 'normal')
```

## Common Patterns

### Pattern 1: Type-Based Styling

Style elements based on their role or type:

```python
type_styles = {
    'controller': NodeStyle('controller', '#1a1625', '#8b5cf6', '2px', '#8b5cf6'),
    'service': NodeStyle('service', '#0c1c20', '#06b6d4', '2px', '#06b6d4'),
    'model': NodeStyle('model', '#0d1f1a', '#10b981', '2px', '#10b981'),
    'utility': NodeStyle('utility', '#211a0d', '#f59e0b', '1px', '#f59e0b')
}

def style_node(self, node_id, node_type='default', properties=None):
    return type_styles.get(node_type) or super().style_node(node_id, node_type, properties)
```

### Pattern 2: Hierarchical Styling

Create visual hierarchy through progressive styling:

```python
def style_node(self, node_id, node_type='default', properties=None):
    properties = properties or {}
    depth = properties.get('depth', 0)

    # Fade colors at deeper levels
    if depth == 0:
        return NodeStyle('root', '#1a1625', '#8b5cf6', '3px', '#a855f7')
    elif depth == 1:
        return NodeStyle('level1', '#15131f', '#7c3aed', '2px', '#9333ea')
    elif depth == 2:
        return NodeStyle('level2', '#100f19', '#6d28d9', '1px', '#8b5cf6')
    else:
        return NodeStyle('deep', '#0a0a0a', '#5b21b6', '1px', '#7c3aed')
```

### Pattern 3: State-Based Styling

Reflect element state visually:

```python
def style_node(self, node_id, node_type='default', properties=None):
    properties = properties or {}
    state = properties.get('state', 'active')

    if state == 'deprecated':
        # Muted red for deprecated
        return NodeStyle('deprecated', '#1a0d0d', '#7f1d1d', '1px', '#991b1b')
    elif state == 'experimental':
        # Bright yellow for experimental
        return NodeStyle('experimental', '#1f1a0d', '#eab308', '2px', '#facc15')
    elif state == 'active':
        # Green for active (default theme)
        return super().style_node(node_id, node_type, properties)
```

## Troubleshooting

### Styles Not Appearing

1. **Verify style syntax:** Ensure `style` and `linkStyle` directives use correct IDs
2. **Check node IDs:** Node IDs in style directives must exactly match node declarations
3. **Validate edge indices:** linkStyle uses zero-based indices in order of edge creation

### Theme Colors Not Used

If calling `super().style_node()` doesn't use theme colors, ensure:
1. You're calling the parent method: `return super().style_node(...)`
2. ThemeManager is initialized: `self.theme_manager` exists
3. Node type is recognized: Use predefined types or 'default'

### Conflicts with Global Theme

Custom styles override global theme. To blend:
```python
# Get theme color
theme_color = self.theme_manager.get_color_scheme(0)

# Use in custom style
return NodeStyle(
    name='custom',
    fill=theme_color.fill,      # From theme
    stroke='#ec4899',            # Custom
    stroke_width='3px',          # Custom
    text_color=theme_color.text_color  # From theme
)
```

## Further Reading

- `base_generator.py:176-293` - style_node() and style_edge() base implementations
- `class_diagram_generator.py:103-216` - Class diagram styling example
- `flowchart_generator.py:109-232` - Flowchart styling example
- `color_schemes.py` - ColorScheme, NodeStyle, and EdgeStyle definitions
- `theme_manager.py` - Global theme management

## Summary

The custom styling API provides:
- **Flexibility**: Override style_node() and style_edge() for full control
- **Consistency**: Fallback to global themes ensures coherent diagrams
- **Expressiveness**: Use properties for conditional, metric-based, or contextual styling
- **Simplicity**: NodeStyle and EdgeStyle classes handle Mermaid syntax generation

By following this guide, you can create visually distinctive diagrams that communicate structure and meaning effectively.
