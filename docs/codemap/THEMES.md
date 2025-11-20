# Diagram Themes

## Overview

The ClickUp Framework code mapping tool supports multiple color themes for generated Mermaid diagrams. Themes control the visual appearance of diagrams including node colors, edge colors, subgraph styles, and overall aesthetics.

### What are Themes?

Themes are pre-defined color schemes that apply consistent styling across all diagram components:
- **Nodes** - Function and class boxes
- **Edges** - Connections between nodes
- **Subgraphs** - Directory, file, and class groupings
- **Text** - Labels and annotations

### Why Use Themes?

- **Consistency** - Uniform appearance across all generated diagrams
- **Context** - Match your documentation style (dark mode, print-ready, etc.)
- **Accessibility** - Choose themes appropriate for different audiences
- **Branding** - Select themes that align with your organization's colors

## Available Themes

### Dark Theme (Default)

- **Purpose**: Dark mode documentation with vibrant accent colors
- **Use Cases**:
  - Developer documentation
  - Dark-mode IDEs and editors
  - Modern web documentation
  - GitHub dark mode README files
- **Colors**: 5 vibrant color schemes (emerald, purple, cyan, amber, pink)
- **Background**: Very dark backgrounds (#0a0a0a to #211a0d)
- **Accents**: Bright, vibrant borders and text

**Example Usage:**
```bash
cum map --python --mer flow --theme dark
```

**Color Palette:**
- Emerald: `#10b981` (green) - Default color for nodes and edges
- Purple: `#8b5cf6` - Entry points and special nodes
- Cyan: `#06b6d4` - Alternative node color
- Amber: `#f59e0b` - Warning/attention nodes
- Pink: `#ec4899` - Alternative accent color

---

### Light Theme

- **Purpose**: Light backgrounds for print and presentations
- **Use Cases**:
  - Printed documentation
  - PowerPoint/PDF presentations
  - Light-mode documentation sites
  - Academic papers
- **Colors**: 5 muted color schemes (emerald_light, purple_light, cyan_light, amber_light, pink_light)
- **Background**: Very light backgrounds (#cffafe to #fef3c7)
- **Accents**: Darker, more subdued borders and text

**Example Usage:**
```bash
cum map --python --mer flowchart --theme light
```

**Color Palette:**
- Emerald Light: `#047857` (dark green) - Default for light backgrounds
- Purple Light: `#6d28d9` - Entry points on light backgrounds
- Cyan Light: `#0e7490` - Alternative node color
- Amber Light: `#b45309` - Warning/attention nodes
- Pink Light: `#be185d` - Alternative accent color

## Theme Selection

### List Available Themes

To see all available themes with descriptions:

```bash
cum map --list-themes
```

Output:
```
===============================================================================
Available Themes
===============================================================================

dark:
  Dark theme with vibrant colors on dark backgrounds
  Colors: 5
  Best for: Developer documentation, dark mode interfaces

light:
  Light theme with muted colors on light backgrounds
  Colors: 5
  Best for: Print documentation, presentations
```

### Using a Theme

Specify the theme with the `--theme` flag:

```bash
# Use dark theme (default)
cum map --python --mer flow --theme dark

# Use light theme
cum map --python --mer flowchart --theme light
```

### Default Theme

If no `--theme` flag is specified, the **dark** theme is used by default.

## Theme Application

### Which Generators Support Themes?

Currently, themes are supported by:
- `flowchart` - Directory structure diagrams
- `swim` - Alias for flowchart
- `flow` - Execution flow / call graph diagrams

Other diagram types (class, sequence, pie, mindmap) use default Mermaid styling.

### Theme Components

Themes control several styling aspects:

**1. Node Styles**
- Entry points: Distinct styling (purple in dark theme)
- Regular nodes: Standard styling (green in dark theme)
- Default nodes: Fallback styling

**2. Subgraph Styles**
- File subgraphs: Group functions from the same file
- Class subgraphs: Group methods within a class
- Directory subgraphs: Color-rotated for visual distinction

**3. Edge Styles**
- Connection lines between nodes
- Color matches destination node for clarity

## Workflow Examples

### Generate Multiple Themed Versions

Generate the same diagram in both themes for different contexts:

```bash
# Dark version for web documentation
cum map --python --mer flow --theme dark --output dark_flow.md

# Light version for print documentation
cum map --python --mer flow --theme light --output light_flow.md
```

### Export to Images with Theme

Combine theme selection with image export:

```bash
# Dark theme PNG for GitHub README
cum map --python --mer flowchart --theme dark --output diagram.png

# Light theme SVG for presentation
cum map --python --mer flowchart --theme light --output slides.svg
```

## See Also

- [Theme Customization Guide](THEME_CUSTOMIZATION.md) - Create custom themes
- [Map Command Reference](../cli/TASK_COMMANDS.md) - Complete CLI documentation
- [Color Reference](https://tailwindcss.com/docs/customizing-colors) - Tailwind color palette (used as basis)

## Future Enhancements

Planned theme features:
- High-contrast theme for accessibility (WCAG 2.1 AA compliant)
- Colorblind-friendly theme (deuteranopia/protanopia safe)
- Custom theme loading from JSON files
- Per-node-type color customization
- Theme preview generation
