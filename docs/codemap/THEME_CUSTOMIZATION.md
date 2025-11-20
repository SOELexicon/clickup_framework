# Theme Customization Guide

## Overview

This guide explains how to create custom color themes for the ClickUp Framework code mapping tool. Custom themes allow you to match your organization's branding, create specialized color schemes for different contexts, or design themes optimized for specific accessibility requirements.

## Prerequisites

Basic understanding of:
- Python programming
- Color theory (hex color codes, RGB values)
- Mermaid diagram styling
- The ClickUp Framework theme system (see [THEMES.md](THEMES.md))

## Theme Architecture

### ColorScheme Structure

Each color scheme is a dataclass with the following properties:

```python
@dataclass
class ColorScheme:
    """A color scheme for theming diagram elements."""
    name: str              # Unique identifier (e.g., 'emerald', 'corporate_blue')
    fill: str              # Background fill color (hex: #rrggbb)
    stroke: str            # Border/outline color (hex: #rrggbb)
    text: str              # Text color (hex: #rrggbb)
    stroke_width: str      # Border width (e.g., '2px', '3px')
```

**Methods**:
- `node_style()` → Returns Mermaid style for nodes: `fill:{fill},stroke:{stroke},color:{text},stroke-width:{stroke_width}`
- `edge_color()` → Returns stroke color for edges/connections
- `to_dict()` → Converts to dictionary for serialization

### NodeStyle Structure

Node styles define the visual appearance of specific node types:

```python
@dataclass
class NodeStyle:
    """Style definition for a specific node type."""
    fill: str              # Background color
    stroke: str            # Border color
    text_color: str        # Text color
    stroke_width: str      # Border width

    def to_mermaid_style(self) -> str:
        """Convert to Mermaid style string."""
```

## Creating a Custom Theme

### Step 1: Define Color Schemes

Create a list of `ColorScheme` objects for your theme. Each scheme represents a color that will be rotated through for different diagram elements.

**Example: Corporate Theme**

```python
from clickup_framework.commands.map_helpers.mermaid.styling import ColorScheme

CORPORATE_THEME_COLORS = [
    # Primary brand color (blue)
    ColorScheme(
        name='corporate_blue',
        fill='#001f3f',        # Navy blue background
        stroke='#0074D9',       # Bright blue border
        text='#7FDBFF',         # Light blue text
        stroke_width='2px'
    ),

    # Secondary brand color (gold)
    ColorScheme(
        name='corporate_gold',
        fill='#2b1d0e',        # Dark brown background
        stroke='#FF851B',       # Orange-gold border
        text='#FFD700',         # Gold text
        stroke_width='2px'
    ),

    # Accent color (green)
    ColorScheme(
        name='corporate_green',
        fill='#0a1f0a',        # Dark green background
        stroke='#2ECC40',       # Bright green border
        text='#3D9970',         # Medium green text
        stroke_width='2px'
    ),

    # Neutral color (gray)
    ColorScheme(
        name='corporate_gray',
        fill='#1a1a1a',        # Dark gray background
        stroke='#AAAAAA',       # Light gray border
        text='#DDDDDD',         # Very light gray text
        stroke_width='2px'
    ),
]
```

### Step 2: Define Node Styles

Create style definitions for different node types (entry points, regular nodes, etc.):

```python
from clickup_framework.commands.map_helpers.mermaid.styling import NodeStyle

# Style for entry point nodes (main functions)
CORPORATE_ENTRY_POINT_STYLE = NodeStyle(
    fill='#001f3f',          # Navy blue (primary brand color)
    stroke='#0074D9',        # Bright blue border
    text_color='#7FDBFF',    # Light blue text
    stroke_width='3px'       # Thicker border for emphasis
)

# Style for regular nodes
CORPORATE_DEFAULT_NODE_STYLE = NodeStyle(
    fill='#0a0a0a',          # Very dark background
    stroke='#0074D9',        # Bright blue border
    text_color='#7FDBFF',    # Light blue text
    stroke_width='2px'
)

# Style for file subgraphs
CORPORATE_FILE_SUBGRAPH_STYLE = NodeStyle(
    fill='#0d1117',          # Slightly lighter dark background
    stroke='#AAAAAA',        # Gray border
    text_color='#DDDDDD',    # Light gray text
    stroke_width='1px'
)

# Style for class subgraphs
CORPORATE_CLASS_SUBGRAPH_STYLE = NodeStyle(
    fill='#161b22',          # Medium dark background
    stroke='#FF851B',        # Orange-gold border (secondary color)
    text_color='#FFD700',    # Gold text
    stroke_width='2px'
)
```

### Step 3: Register Your Theme

Add your theme to the `ThemeManager` class:

**Location**: `clickup_framework/commands/map_helpers/mermaid/styling/theme_manager.py`

```python
class ThemeManager:
    VALID_THEMES = {'dark', 'light', 'corporate'}  # Add your theme name
    DEFAULT_THEME = 'dark'

    def __init__(self, theme_name: str = 'dark'):
        # ... existing code ...
        if not self.set_theme(theme_name):
            self.set_theme(self.DEFAULT_THEME)

    def set_theme(self, theme_name: str) -> bool:
        """Set the active theme."""
        if theme_name not in self.VALID_THEMES:
            return False

        self.current_theme = theme_name

        if theme_name == 'dark':
            self._theme_colors = DARK_THEME_COLORS
        elif theme_name == 'light':
            self._theme_colors = LIGHT_THEME_COLORS
        elif theme_name == 'corporate':  # Add your theme
            self._theme_colors = CORPORATE_THEME_COLORS
            # Optionally override node styles
            self._node_styles['entry_point'] = CORPORATE_ENTRY_POINT_STYLE
            self._node_styles['default'] = CORPORATE_DEFAULT_NODE_STYLE
            self._node_styles['file_subgraph'] = CORPORATE_FILE_SUBGRAPH_STYLE
            self._node_styles['class_subgraph'] = CORPORATE_CLASS_SUBGRAPH_STYLE

        self._style_cache.clear()
        return True
```

### Step 4: Update Theme Listing

Add your theme to the `list_available_themes()` method:

```python
def list_available_themes(self) -> Dict[str, Dict[str, Any]]:
    """List all available themes with metadata."""
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
        },
        'corporate': {  # Add your theme metadata
            'description': 'Corporate theme with company brand colors',
            'colors': len(CORPORATE_THEME_COLORS),
            'best_for': 'Internal documentation, stakeholder presentations'
        }
    }
```

### Step 5: Export Your Theme

Add your theme colors to the module exports in `color_schemes.py`:

**Location**: `clickup_framework/commands/map_helpers/mermaid/styling/color_schemes.py`

```python
# At the end of the file
__all__ = [
    'ColorScheme',
    'NodeStyle',
    'DARK_THEME_COLORS',
    'LIGHT_THEME_COLORS',
    'CORPORATE_THEME_COLORS',  # Add your theme
    'DEFAULT_NODE_STYLE',
    'ENTRY_POINT_STYLE',
    'FILE_SUBGRAPH_STYLE',
    'CLASS_SUBGRAPH_STYLE',
    'CORPORATE_ENTRY_POINT_STYLE',  # Add your custom styles
    'CORPORATE_DEFAULT_NODE_STYLE',
    'CORPORATE_FILE_SUBGRAPH_STYLE',
    'CORPORATE_CLASS_SUBGRAPH_STYLE',
    'list_themes'
]
```

## Color Selection Guidelines

### Contrast Requirements

Ensure sufficient contrast between:
- **Fill and Text**: Minimum 4.5:1 ratio (WCAG AA standard)
- **Stroke and Fill**: Minimum 3:1 ratio for visibility
- **Adjacent Elements**: Different hues to avoid confusion

**Tools**:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Coolors Contrast Checker](https://coolors.co/contrast-checker)

### Dark Theme Guidelines

- **Backgrounds**: Very dark (#0a0a0a to #1a1a1a range)
- **Borders**: Bright, saturated colors (#10b981, #8b5cf6, etc.)
- **Text**: Light, high-contrast colors matching border hues

**Example Palette**:
```
Background: #0d1f1a (very dark green)
Border:     #10b981 (bright emerald)
Text:       #34d399 (lighter emerald)
```

### Light Theme Guidelines

- **Backgrounds**: Very light (#f0f0f0 to #ffffff range)
- **Borders**: Dark, muted colors (#047857, #6d28d9, etc.)
- **Text**: Dark colors matching border hues

**Example Palette**:
```
Background: #cffafe (very light cyan)
Border:     #0e7490 (dark cyan)
Text:       #164e63 (darker cyan)
```

### Color Rotation Strategy

Your theme should have **4-6 color schemes** that:
1. Are visually distinct from each other
2. Work harmoniously together
3. Rotate well for large diagrams (20+ subgraphs)

**Good rotation examples**:
- Analogous colors: Blue → Cyan → Teal → Green
- Complementary pairs: Blue/Orange, Purple/Yellow
- Triadic: Red, Yellow, Blue

## Validation and Testing

### Theme Validation

Use the `ThemeManager.validate_theme()` method to check completeness:

```python
from clickup_framework.commands.map_helpers.mermaid.styling import ThemeManager

theme_manager = ThemeManager()

# Validate your theme dictionary
theme_dict = {
    'name': 'corporate',
    'colors': CORPORATE_THEME_COLORS,
    'node_styles': {
        'default': CORPORATE_DEFAULT_NODE_STYLE,
        'entry_point': CORPORATE_ENTRY_POINT_STYLE
    }
}

is_valid, errors = theme_manager.validate_theme(theme_dict)
if not is_valid:
    print("Theme validation errors:")
    for error in errors:
        print(f"  - {error}")
```

### Testing Your Theme

Generate test diagrams with your custom theme:

```bash
# Generate flowchart with corporate theme
cum map --python --mer flowchart --theme corporate

# Generate execution flow with corporate theme
cum map --python --mer flow --theme corporate

# Export to PNG for visual inspection
cum map --python --mer flow --theme corporate --output corporate_test.png
```

### Visual Inspection Checklist

- [ ] All nodes are clearly visible
- [ ] Text is readable on all backgrounds
- [ ] Borders stand out from fills
- [ ] Color rotation provides clear visual distinction
- [ ] Entry points are visually emphasized
- [ ] Subgraphs are distinguishable from nodes
- [ ] Edge colors match destination nodes
- [ ] No color clashing or visual confusion

## Advanced Customization

### Conditional Styling

Apply different colors based on node metadata:

```python
def get_color_for_node(node_name: str, metadata: Dict) -> ColorScheme:
    """Select color scheme based on node characteristics."""

    # Hot path nodes (frequently called)
    if metadata.get('call_count', 0) > 100:
        return CORPORATE_THEME_COLORS[0]  # Primary color

    # External library calls
    elif metadata.get('is_external', False):
        return CORPORATE_THEME_COLORS[3]  # Neutral gray

    # Error handlers
    elif 'error' in node_name.lower() or 'exception' in node_name.lower():
        return CORPORATE_THEME_COLORS[2]  # Accent green (warning)

    # Default
    else:
        return CORPORATE_THEME_COLORS[1]  # Secondary gold
```

### Dynamic Theme Generation

Generate themes programmatically from a base color:

```python
from typing import List

def generate_theme_from_base(base_color: str, theme_name: str) -> List[ColorScheme]:
    """Generate a complete theme from a single base color."""
    # Convert hex to HSL, rotate hue, generate variants
    # (Implementation would require color manipulation library)
    pass
```

### Accessibility Themes

Create high-contrast and colorblind-safe themes:

```python
# High contrast theme (WCAG AAA)
HIGH_CONTRAST_THEME = [
    ColorScheme(
        name='high_contrast_primary',
        fill='#000000',      # Pure black
        stroke='#FFFFFF',    # Pure white
        text='#FFFFFF',      # Pure white
        stroke_width='3px'   # Thick borders
    ),
    # ... more schemes with 7:1+ contrast ratio
]

# Deuteranopia-safe theme (no red-green)
COLORBLIND_SAFE_THEME = [
    ColorScheme(name='cb_blue', fill='#000033', stroke='#0077BB', text='#88CCEE', stroke_width='2px'),
    ColorScheme(name='cb_orange', fill='#331100', stroke='#EE7733', text='#FFAA88', stroke_width='2px'),
    ColorScheme(name='cb_purple', fill='#220033', stroke='#AA3377', text='#DD88CC', stroke_width='2px'),
    # Blue-Orange-Purple palette works for most colorblind types
]
```

## Complete Example: Academic Theme

Here's a complete example of a light, print-friendly theme for academic papers:

```python
# File: clickup_framework/commands/map_helpers/mermaid/styling/color_schemes.py

# Academic theme - optimized for black & white printing
ACADEMIC_THEME_COLORS = [
    ColorScheme(
        name='academic_dark_blue',
        fill='#e6f2ff',        # Very light blue
        stroke='#003366',       # Dark blue
        text='#001a33',         # Very dark blue
        stroke_width='2px'
    ),
    ColorScheme(
        name='academic_medium_gray',
        fill='#f0f0f0',        # Light gray
        stroke='#404040',       # Dark gray
        text='#202020',         # Very dark gray
        stroke_width='2px'
    ),
    ColorScheme(
        name='academic_dark_green',
        fill='#e6f9e6',        # Very light green
        stroke='#1a5c1a',       # Dark green
        text='#0d2e0d',         # Very dark green
        stroke_width='2px'
    ),
    ColorScheme(
        name='academic_burgundy',
        fill='#ffeef0',        # Very light red
        stroke='#660000',       # Dark burgundy
        text='#330000',         # Very dark red
        stroke_width='2px'
    ),
]

# Academic node styles - clear hierarchy
ACADEMIC_ENTRY_POINT_STYLE = NodeStyle(
    fill='#e6f2ff',
    stroke='#003366',
    text_color='#001a33',
    stroke_width='3px'  # Thicker for importance
)

ACADEMIC_DEFAULT_NODE_STYLE = NodeStyle(
    fill='#ffffff',     # Pure white
    stroke='#404040',
    text_color='#202020',
    stroke_width='1.5px'
)

ACADEMIC_FILE_SUBGRAPH_STYLE = NodeStyle(
    fill='#fafafa',     # Off-white
    stroke='#808080',
    text_color='#404040',
    stroke_width='1px'
)

ACADEMIC_CLASS_SUBGRAPH_STYLE = NodeStyle(
    fill='#f5f5f5',
    stroke='#606060',
    text_color='#303030',
    stroke_width='1.5px'
)
```

Then register in `theme_manager.py`:

```python
VALID_THEMES = {'dark', 'light', 'academic'}

# In set_theme():
elif theme_name == 'academic':
    self._theme_colors = ACADEMIC_THEME_COLORS
    self._node_styles['entry_point'] = ACADEMIC_ENTRY_POINT_STYLE
    self._node_styles['default'] = ACADEMIC_DEFAULT_NODE_STYLE
    self._node_styles['file_subgraph'] = ACADEMIC_FILE_SUBGRAPH_STYLE
    self._node_styles['class_subgraph'] = ACADEMIC_CLASS_SUBGRAPH_STYLE
```

Usage:

```bash
cum map --python --mer flowchart --theme academic --output figure1.svg
```

## Troubleshooting

### Common Issues

**Issue**: Colors appear too similar when rotated
- **Solution**: Increase hue separation between color schemes (60° minimum)

**Issue**: Text is unreadable
- **Solution**: Check contrast ratio, increase text color brightness/darkness

**Issue**: Theme doesn't appear in --list-themes
- **Solution**: Verify theme is added to `VALID_THEMES` and `list_available_themes()`

**Issue**: Diagram renders incorrectly
- **Solution**: Validate all hex colors are 6 characters (#rrggbb format)

### Debug Commands

```bash
# List all themes to verify registration
cum map --list-themes

# Test theme on small Python project
cum map --python --mer flow --theme your_theme

# Export to image to see actual rendering
cum map --python --mer flow --theme your_theme --output test.png
```

## Best Practices

1. **Start with existing themes**: Copy dark or light theme as a template
2. **Test early and often**: Generate diagrams after each color change
3. **Use color tools**: Leverage online palette generators
4. **Document your theme**: Add comments explaining color choices
5. **Consider context**: Different themes for different output formats
6. **Maintain consistency**: Use same color family across related schemes
7. **Plan for scale**: Test with large diagrams (100+ nodes)
8. **Get feedback**: Share with target audience for validation

## See Also

- [Theme Overview](THEMES.md) - Using existing themes
- [Mermaid Styling Documentation](https://mermaid.js.org/config/theming.html)
- [WCAG Color Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Tailwind Color Palette](https://tailwindcss.com/docs/customizing-colors) - Used as basis for default themes

## Future Features

Planned enhancements for theme customization:

- **JSON theme loading**: Define themes in external JSON files
- **Theme inheritance**: Extend existing themes with overrides
- **Per-node-type colors**: Assign specific colors to node types
- **Gradient fills**: Support CSS gradients in node backgrounds
- **Theme preview**: Generate sample diagrams for all themes
- **Theme validator CLI**: Standalone validation tool
