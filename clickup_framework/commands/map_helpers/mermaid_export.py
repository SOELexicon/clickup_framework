"""Mermaid diagram export utilities (image formats via mmdc and interactive HTML)."""

import sys
import subprocess
from pathlib import Path
from clickup_framework.utils.colors import colorize, TextColor


def check_mmdc_available() -> bool:
    """Check if mermaid-cli (mmdc) is available."""
    try:
        result = subprocess.run(
            ['mmdc', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True  # Use shell on Windows to find mmdc
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def export_mermaid_to_image(markdown_file: str, output_file: str, image_format: str, use_color: bool = False) -> bool:
    """
    Export mermaid markdown to image using mmdc (mermaid-cli).

    Args:
        markdown_file: Input markdown file with mermaid diagram
        output_file: Output image file path
        image_format: Image format (png, svg, jpg)
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    if not check_mmdc_available():
        error_msg = "ERROR: mmdc (mermaid-cli) not found. Install with: npm install -g @mermaid-js/mermaid-cli"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        return False

    try:
        # Map jpg to jpeg for mmdc
        mmdc_format = 'jpeg' if image_format == 'jpg' else image_format

        cmd = [
            'mmdc',
            '-i', markdown_file,
            '-o', output_file,
            '-t', 'dark',  # Use dark theme
            '-b', 'transparent',  # Transparent background
            '-w', '4000',  # High width for better resolution
            '-H', '3000',  # High height
            '-s', '3'  # Scale factor for even higher quality
        ]

        if use_color:
            print(colorize(f"[PROGRESS] Converting to {image_format.upper()}...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Converting to {image_format.upper()}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True  # Use shell on Windows
        )

        if result.returncode == 0:
            if use_color:
                print(colorize(f"[SUCCESS] Image exported: {output_file}", TextColor.GREEN))
            else:
                print(f"[SUCCESS] Image exported: {output_file}")
            return True
        else:
            if use_color:
                print(colorize(f"[ERROR] mmdc failed: {result.stderr}", TextColor.RED), file=sys.stderr)
            else:
                print(f"[ERROR] mmdc failed: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to export image: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to export image: {e}", file=sys.stderr)
        return False


def export_mermaid_to_interactive_html(
    mermaid_content: str,
    output_file: str,
    title: str = "Code Map",
    theme: str = "dark",
    use_color: bool = False
) -> bool:
    """
    Export mermaid diagram to interactive HTML with pan, zoom, search, and theme toggle.

    This creates a self-contained HTML file that works with all Mermaid diagram types
    (flowchart, class, pie, mindmap, sequence, code flow).

    Args:
        mermaid_content: Mermaid diagram code (just the diagram, not the markdown fences)
        output_file: Output HTML file path
        title: Page title (default: "Code Map")
        theme: Initial theme - 'dark' or 'light' (default: 'dark')
        use_color: Whether to use colored console output

    Returns:
        True if successful, False otherwise

    Example:
        >>> mermaid = "graph TD\\n    A[Start] --> B[End]"
        >>> export_mermaid_to_interactive_html(mermaid, "diagram.html")
        True
    """
    try:
        # Escape the mermaid content for embedding in HTML
        escaped_content = mermaid_content.replace('`', '\\`').replace('${', '\\${')

        # Determine initial theme classes
        theme_class = "dark-theme" if theme == "dark" else "light-theme"

        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{theme}',
            securityLevel: 'loose',
            flowchart: {{ useMaxWidth: false }},
            htmlLabels: true
        }});
        window.mermaid = mermaid;
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            overflow: hidden;
            height: 100vh;
            transition: background-color 0.3s, color 0.3s;
        }}

        /* Theme styles */
        body.dark-theme {{
            background-color: #1e1e1e;
            color: #e0e0e0;
        }}

        body.light-theme {{
            background-color: #ffffff;
            color: #333333;
        }}

        /* Toolbar */
        #toolbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 1000;
            transition: background-color 0.3s, box-shadow 0.3s;
        }}

        body.dark-theme #toolbar {{
            background-color: #2d2d2d;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}

        body.light-theme #toolbar {{
            background-color: #f5f5f5;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        #toolbar h1 {{
            font-size: 20px;
            font-weight: 600;
            margin-right: auto;
        }}

        /* Search box */
        #search-box {{
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid;
            font-size: 14px;
            width: 250px;
            transition: border-color 0.2s, background-color 0.3s, color 0.3s;
        }}

        body.dark-theme #search-box {{
            background-color: #3d3d3d;
            border-color: #555;
            color: #e0e0e0;
        }}

        body.light-theme #search-box {{
            background-color: #ffffff;
            border-color: #ddd;
            color: #333;
        }}

        #search-box:focus {{
            outline: none;
            border-color: #4a9eff;
        }}

        /* Buttons */
        .btn {{
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
        }}

        body.dark-theme .btn {{
            background-color: #4a9eff;
            color: white;
        }}

        body.light-theme .btn {{
            background-color: #2196f3;
            color: white;
        }}

        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}

        .btn:active {{
            transform: translateY(0);
        }}

        /* Diagram container */
        #diagram-container {{
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            bottom: 0;
            overflow: hidden;
            cursor: grab;
        }}

        #diagram-container.grabbing {{
            cursor: grabbing;
        }}

        #diagram-wrapper {{
            transform-origin: 0 0;
            transition: transform 0.1s ease-out;
            will-change: transform;
        }}

        /* Mermaid diagram styling */
        .mermaid {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100%;
            padding: 40px;
        }}

        /* Zoom controls */
        #zoom-controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 1000;
        }}

        .zoom-btn {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }}

        body.dark-theme .zoom-btn {{
            background-color: #4a9eff;
            color: white;
        }}

        body.light-theme .zoom-btn {{
            background-color: #2196f3;
            color: white;
        }}

        .zoom-btn:hover {{
            transform: scale(1.1);
        }}

        /* Status message */
        #status-msg {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            z-index: 1000;
        }}

        body.dark-theme #status-msg {{
            background-color: #3d3d3d;
            color: #e0e0e0;
        }}

        body.light-theme #status-msg {{
            background-color: #f5f5f5;
            color: #333;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }}

        #status-msg.show {{
            opacity: 1;
        }}

        /* Highlight matching elements */
        .highlight {{
            outline: 3px solid #ffeb3b !important;
            outline-offset: 2px;
        }}
    </style>
</head>
<body class="{theme_class}">
    <div id="toolbar">
        <h1>{title}</h1>
        <input type="text" id="search-box" placeholder="Search diagram elements...">
        <button class="btn" id="reset-btn">Reset View</button>
        <button class="btn" id="theme-btn">Toggle Theme</button>
    </div>

    <div id="diagram-container">
        <div id="diagram-wrapper">
            <pre class="mermaid">{escaped_content}</pre>
        </div>
    </div>

    <div id="zoom-controls">
        <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
        <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
        <button class="zoom-btn" id="fit-btn" title="Fit to Screen">⊡</button>
    </div>

    <div id="status-msg"></div>

    <script>
        // State
        let scale = 1;
        let panX = 0;
        let panY = 0;
        let isPanning = false;
        let startX = 0;
        let startY = 0;
        let currentTheme = '{theme}';

        // Elements
        const container = document.getElementById('diagram-container');
        const wrapper = document.getElementById('diagram-wrapper');
        const searchBox = document.getElementById('search-box');
        const resetBtn = document.getElementById('reset-btn');
        const themeBtn = document.getElementById('theme-btn');
        const zoomInBtn = document.getElementById('zoom-in');
        const zoomOutBtn = document.getElementById('zoom-out');
        const fitBtn = document.getElementById('fit-btn');
        const statusMsg = document.getElementById('status-msg');

        // Update transform
        function updateTransform() {{
            wrapper.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
        }}

        // Show status message
        function showStatus(message, duration = 2000) {{
            statusMsg.textContent = message;
            statusMsg.classList.add('show');
            setTimeout(() => {{
                statusMsg.classList.remove('show');
            }}, duration);
        }}

        // Pan controls
        container.addEventListener('mousedown', (e) => {{
            if (e.target.closest('.mermaid')) {{
                isPanning = true;
                startX = e.clientX - panX;
                startY = e.clientY - panY;
                container.classList.add('grabbing');
            }}
        }});

        document.addEventListener('mousemove', (e) => {{
            if (isPanning) {{
                panX = e.clientX - startX;
                panY = e.clientY - startY;
                updateTransform();
            }}
        }});

        document.addEventListener('mouseup', () => {{
            isPanning = false;
            container.classList.remove('grabbing');
        }});

        // Zoom with mouse wheel
        container.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.min(Math.max(0.1, scale * delta), 5);

            // Zoom towards mouse position
            const rect = container.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            panX = mouseX - (mouseX - panX) * (newScale / scale);
            panY = mouseY - (mouseY - panY) * (newScale / scale);
            scale = newScale;

            updateTransform();
        }});

        // Zoom buttons
        zoomInBtn.addEventListener('click', () => {{
            scale = Math.min(scale * 1.2, 5);
            updateTransform();
            showStatus(`Zoom: ${{Math.round(scale * 100)}}%`);
        }});

        zoomOutBtn.addEventListener('click', () => {{
            scale = Math.max(scale / 1.2, 0.1);
            updateTransform();
            showStatus(`Zoom: ${{Math.round(scale * 100)}}%`);
        }});

        // Fit to screen
        fitBtn.addEventListener('click', () => {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                const containerRect = container.getBoundingClientRect();
                const svgRect = svg.getBoundingClientRect();

                const scaleX = containerRect.width / svgRect.width * 0.9;
                const scaleY = containerRect.height / svgRect.height * 0.9;
                scale = Math.min(scaleX, scaleY, 1);

                panX = (containerRect.width - svgRect.width * scale) / 2;
                panY = (containerRect.height - svgRect.height * scale) / 2;

                updateTransform();
                showStatus('Fit to screen');
            }}
        }});

        // Reset view
        resetBtn.addEventListener('click', () => {{
            scale = 1;
            panX = 0;
            panY = 0;
            updateTransform();
            showStatus('View reset');
        }});

        // Theme toggle
        themeBtn.addEventListener('click', () => {{
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.className = currentTheme === 'dark' ? 'dark-theme' : 'light-theme';

            // Reinitialize Mermaid with new theme
            window.mermaid.initialize({{
                startOnLoad: false,
                theme: currentTheme,
                securityLevel: 'loose',
                flowchart: {{ useMaxWidth: false }},
                htmlLabels: true
            }});

            // Re-render diagram
            const mermaidDiv = document.querySelector('.mermaid');
            const content = `{escaped_content}`;
            mermaidDiv.innerHTML = content;
            mermaidDiv.removeAttribute('data-processed');
            window.mermaid.run({{ nodes: [mermaidDiv] }});

            showStatus(`Theme: ${{currentTheme}}`);
        }});

        // Search functionality
        let searchTimeout;
        searchBox.addEventListener('input', (e) => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {{
                const searchTerm = e.target.value.toLowerCase().trim();

                // Remove previous highlights
                document.querySelectorAll('.highlight').forEach(el => {{
                    el.classList.remove('highlight');
                }});

                if (searchTerm) {{
                    // Search in text elements
                    const svg = document.querySelector('.mermaid svg');
                    if (svg) {{
                        let matchCount = 0;
                        svg.querySelectorAll('text, tspan, .nodeLabel, .edgeLabel').forEach(el => {{
                            if (el.textContent.toLowerCase().includes(searchTerm)) {{
                                // Highlight parent node or edge
                                let parent = el.closest('g[id], rect, circle, ellipse, polygon, path');
                                if (parent) {{
                                    parent.classList.add('highlight');
                                    matchCount++;
                                }}
                            }}
                        }});

                        if (matchCount > 0) {{
                            showStatus(`Found ${{matchCount}} match${{matchCount === 1 ? '' : 'es'}}`);
                        }} else {{
                            showStatus('No matches found');
                        }}
                    }}
                }}
            }}, 300);
        }});

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.ctrlKey || e.metaKey) {{
                if (e.key === '=' || e.key === '+') {{
                    e.preventDefault();
                    zoomInBtn.click();
                }} else if (e.key === '-') {{
                    e.preventDefault();
                    zoomOutBtn.click();
                }} else if (e.key === '0') {{
                    e.preventDefault();
                    resetBtn.click();
                }} else if (e.key === 'f') {{
                    e.preventDefault();
                    searchBox.focus();
                }}
            }} else if (e.key === 'Escape') {{
                searchBox.value = '';
                searchBox.dispatchEvent(new Event('input'));
                searchBox.blur();
            }}
        }});

        // Initial fit after diagram loads
        setTimeout(() => {{
            fitBtn.click();
        }}, 500);
    </script>
</body>
</html>'''

        # Write HTML file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_template, encoding='utf-8')

        if use_color:
            print(colorize(f"[SUCCESS] Interactive HTML exported: {output_file}", TextColor.GREEN))
        else:
            print(f"[SUCCESS] Interactive HTML exported: {output_file}")

        return True

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to export interactive HTML: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to export interactive HTML: {e}", file=sys.stderr)
        return False
