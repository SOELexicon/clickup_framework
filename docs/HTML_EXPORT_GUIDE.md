# Interactive HTML Diagram Export

## Overview

The ClickUp Framework CLI now supports exporting Mermaid diagrams to interactive, self-contained HTML files. These HTML files include pan, zoom, search, and theme toggle capabilities, providing a rich viewing experience for code maps and diagrams.

## Features

- **Pan and Zoom Controls**: Navigate large diagrams with mouse drag, wheel scroll, and button controls
- **Search with Highlighting**: Find elements in the diagram with instant highlighting
- **Theme Toggle**: Switch between dark and light themes dynamically
- **Keyboard Shortcuts**: Quick access to common operations
- **Fit to Screen**: Automatically size diagram to viewport
- **Status Messages**: Visual feedback for user actions
- **Self-Contained**: No external dependencies except Mermaid.js CDN
- **All Diagram Types**: Works with pie, flowchart, class, mindmap, sequence, and flow diagrams

## Command Line Usage

### Basic Export

Export any diagram type to interactive HTML:

```bash
cum map --python --mer pie --html --output report.html
```

### With Theme Selection

Choose dark or light theme:

```bash
# Dark theme (default)
cum map --python --mer flowchart --theme dark --html --output flowchart.html

# Light theme
cum map --python --mer class --theme light --html --output classes.html
```

### All Diagram Types

```bash
# Pie chart
cum map --python --mer pie --html --output pie.html

# Flowchart (code structure)
cum map --python --mer flowchart --html --output structure.html

# Code flow (execution flow with calls)
cum map --python --mer flow --html --output execution.html

# Class diagram
cum map --python --mer class --html --output classes.html

# Sequence diagram
cum map --python --mer sequence --html --output sequence.html

# Mindmap
cum map --python --mer mindmap --html --output mindmap.html
```

### Auto-Extension Detection

If you omit the `.html` extension, it will be added automatically:

```bash
cum map --python --mer pie --html --output report
# Creates: report.html
```

## Programmatic Usage

### Using BaseGenerator

All diagram generators inherit from `BaseGenerator` and include the `export_html()` method:

```python
from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator

# Sample statistics
stats = {
    'total_symbols': 150,
    'files_analyzed': 10,
    'by_language': {
        'Python': {'function': 50, 'class': 20},
        'JavaScript': {'function': 40, 'class': 15},
        'TypeScript': {'function': 25, 'class': 10}
    }
}

# Create generator
generator = PieChartGenerator(stats, 'diagram.md', theme='dark')

# Generate markdown diagram
generator.generate()

# Export to HTML (auto-generates diagram.html)
generator.export_html(use_color=True)

# Or specify custom filename
generator.export_html('custom_report.html', use_color=True)
```

### Using export_mermaid_to_interactive_html()

For direct export without generators:

```python
from clickup_framework.commands.map_helpers.mermaid_export import export_mermaid_to_interactive_html

# Mermaid diagram code
diagram = """
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
"""

# Export to HTML
success = export_mermaid_to_interactive_html(
    mermaid_content=diagram,
    output_file="my_diagram.html",
    title="My Flowchart",
    theme="dark",
    use_color=True
)

if success:
    print("HTML export successful!")
```

## Interactive Features

### Pan Controls

- **Mouse Drag**: Click and drag on diagram to pan
- **Touch Drag**: Drag with finger on touch devices

### Zoom Controls

- **Mouse Wheel**: Scroll to zoom in/out (zooms toward cursor position)
- **Zoom Buttons**: Click + or - buttons in bottom-right corner
- **Keyboard**: `Ctrl+` to zoom in, `Ctrl-` to zoom out

### Search

1. Click search box in toolbar (or press `Ctrl+F`)
2. Type search term
3. Matching elements highlight in yellow
4. Status message shows number of matches
5. Press `Esc` to clear search

### Theme Toggle

- Click "Toggle Theme" button in toolbar
- Switches between dark and light themes
- Diagram re-renders with new theme
- Theme preference persists during session

### Fit to Screen

- Click fit button (⊡) in bottom-right corner
- Automatically scales diagram to fit viewport
- Centers diagram in view

### Reset View

- Click "Reset View" button in toolbar
- Resets zoom to 100%
- Resets pan to origin
- Keyboard shortcut: `Ctrl+0`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+` or `Ctrl+=` | Zoom in |
| `Ctrl-` | Zoom out |
| `Ctrl+0` | Reset view |
| `Ctrl+F` | Focus search box |
| `Esc` | Clear search and blur search box |

## Technical Details

### Architecture

The HTML export system consists of three main components:

1. **export_mermaid_to_interactive_html()** (mermaid_export.py:94-612)
   - Core export function
   - Generates self-contained HTML with embedded template
   - Handles theme configuration
   - Writes file to disk

2. **BaseGenerator.export_html()** (base_generator.py:357-415)
   - Public method available to all generators
   - Extracts Mermaid content from generated markdown
   - Calls export function with generator's theme
   - Auto-generates filename if not specified

3. **BaseGenerator._extract_mermaid_content()** (base_generator.py:417-438)
   - Helper method to parse markdown
   - Extracts pure Mermaid code (between ```mermaid and ``` markers)
   - Returns clean diagram content for embedding

### HTML Template Structure

The generated HTML includes:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Mermaid.js ES6 module from CDN -->
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ /* config */ });
        window.mermaid = mermaid;
    </script>

    <!-- Embedded CSS for UI and themes -->
    <style>
        /* Dark/light theme styles */
        /* Toolbar, buttons, search box */
        /* Diagram container and zoom controls */
        /* Status messages and highlights */
    </style>
</head>
<body class="dark-theme">
    <!-- Toolbar with title, search, buttons -->
    <div id="toolbar">...</div>

    <!-- Pan/zoom container with diagram -->
    <div id="diagram-container">
        <div id="diagram-wrapper">
            <pre class="mermaid">
                <!-- Mermaid diagram code here -->
            </pre>
        </div>
    </div>

    <!-- Zoom control buttons -->
    <div id="zoom-controls">...</div>

    <!-- Status message display -->
    <div id="status-msg"></div>

    <!-- JavaScript for interactivity -->
    <script>
        /* Pan, zoom, search, theme toggle */
        /* Event handlers and keyboard shortcuts */
    </script>
</body>
</html>
```

### Dependencies

- **Mermaid.js 10**: Loaded from CDN (https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs)
- **No Build Required**: Pure HTML/CSS/JS, works in any modern browser
- **No External Files**: All styles and scripts embedded

### Browser Compatibility

- Chrome/Edge: 90+
- Firefox: 88+
- Safari: 14+
- Opera: 76+

Requires ES6 module support and CSS Grid/Flexbox.

## File Size

Typical HTML export file sizes:

- **Simple diagrams** (pie, sequence): 14-16 KB
- **Medium diagrams** (flowchart, class): 15-18 KB
- **Complex diagrams** (large flow graphs): 18-25 KB

File size includes:
- Full HTML template with CSS (~8 KB)
- Interactive JavaScript (~6 KB)
- Mermaid diagram content (varies)

## Performance Considerations

### Large Diagrams

For very large diagrams (100+ nodes):

1. **Initial Render**: May take 1-2 seconds
2. **Pan/Zoom**: Smooth after initial render
3. **Search**: Fast (DOM query-based)
4. **Theme Toggle**: Requires re-render (1-2 seconds)

### Memory Usage

- Small diagrams: ~10-15 MB browser memory
- Large diagrams: ~50-100 MB browser memory
- No memory leaks (proper event cleanup)

## Comparison with Image Export

| Feature | HTML Export | Image Export (PNG/SVG) |
|---------|-------------|------------------------|
| Interactive | ✓ Yes | ✗ No |
| Pan/Zoom | ✓ Yes | ✗ No (static) |
| Search | ✓ Yes | ✗ No |
| Theme Toggle | ✓ Yes | ✗ No (baked in) |
| File Size | 14-25 KB | 50-500 KB |
| Requires mmdc | ✗ No | ✓ Yes |
| Print Quality | Medium | High |
| Offline Viewing | ✓ Yes (after download) | ✓ Yes |
| Email Friendly | ✓ Yes | ✓ Yes |
| GitHub README | ✗ No (security) | ✓ Yes |

## Use Cases

### Documentation

```bash
# Generate interactive code map for documentation
cum map --python --mer flowchart --html --output docs/architecture.html
```

### Code Reviews

```bash
# Create class diagram for PR review
cum map --python --mer class --html --output review/classes.html
```

### Presentations

```bash
# Generate execution flow for presentation
cum map --python --mer flow --theme light --html --output presentation/flow.html
```

### Reports

```bash
# Create pie chart for language distribution report
cum map --python --mer pie --html --output reports/languages.html
```

## Troubleshooting

### Diagram Not Rendering

**Symptom**: Blank page or "Loading..." message

**Solutions**:
1. Check browser console for errors (F12)
2. Verify internet connection (Mermaid.js CDN required)
3. Try different browser
4. Check if browser blocks CDN content

### Search Not Working

**Symptom**: No highlights when searching

**Solutions**:
1. Ensure diagram has finished rendering
2. Check if search term matches diagram content
3. Try clicking elsewhere in diagram first
4. Refresh page and try again

### Theme Toggle Not Working

**Symptom**: Theme button doesn't change appearance

**Solutions**:
1. Wait for initial render to complete
2. Check browser console for errors
3. Refresh page
4. Try different diagram type

### Large File Size

**Symptom**: HTML file is unexpectedly large (>100 KB)

**Possible Causes**:
1. Very large diagram with many nodes
2. Long node labels or descriptions

**Solutions**:
1. Split into multiple smaller diagrams
2. Use abbreviations for labels
3. Filter to specific language/subset

## Examples

See test files for complete examples:

- `test_interactive_html.py` - Standalone function usage
- `test_generator_html_export.py` - BaseGenerator integration
- `test_cli_html_export.py` - CLI usage examples
- `test_all_diagram_types.py` - All diagram types

## API Reference

### export_mermaid_to_interactive_html()

```python
def export_mermaid_to_interactive_html(
    mermaid_content: str,
    output_file: str,
    title: str = "Code Map",
    theme: str = "dark",
    use_color: bool = False
) -> bool:
    """
    Export mermaid diagram to interactive HTML.

    Args:
        mermaid_content: The mermaid diagram code
        output_file: Path to output HTML file
        title: Page title (default: "Code Map")
        theme: Initial theme - "dark" or "light" (default: "dark")
        use_color: Whether to use colored console output (default: False)

    Returns:
        True if export successful, False otherwise
    """
```

### BaseGenerator.export_html()

```python
def export_html(
    self,
    html_file: Optional[str] = None,
    use_color: bool = False
) -> bool:
    """
    Export diagram to interactive HTML.

    Args:
        html_file: Output HTML file path. If None, uses same base name
                  as markdown file with .html extension (default: None)
        use_color: Whether to use colored console output (default: False)

    Returns:
        True if export successful, False otherwise
    """
```

## Future Enhancements

Potential improvements for future versions:

1. **Export Options**
   - Custom CSS themes
   - Logo/branding support
   - Configurable keyboard shortcuts

2. **Advanced Features**
   - Click to collapse/expand nodes
   - Export current view as PNG
   - Bookmark specific views
   - Multiple diagram tabs

3. **Integration**
   - Save theme preference to localStorage
   - URL hash for view state
   - Embed mode for iframes

4. **Performance**
   - Virtual rendering for huge diagrams
   - Web Worker for search
   - Canvas fallback for large graphs

## Credits

Built with:
- [Mermaid.js](https://mermaid.js.org/) - Diagram rendering
- ES6 Modules - Modern JavaScript
- CSS Grid/Flexbox - Responsive layout
- SVG DOM - Search and highlighting

## License

Part of ClickUp Framework CLI. See main project LICENSE.
