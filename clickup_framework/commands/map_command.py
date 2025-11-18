"""Code mapping command using ctags for ClickUp Framework CLI."""

import sys
import os
import json
import subprocess
import zipfile
import urllib.request
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List, Set
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle

# Metadata for automatic help generation
COMMAND_METADATA = {
    "category": "🛠️  Utility Commands",
    "commands": [
        {
            "name": "map",
            "args": "[--python|--csharp|--all-langs] [--mer TYPE] [--output FILE] [--format FORMAT] [--install]",
            "description": "Generate code map using ctags, optionally export as mermaid diagram"
        },
    ]
}

# Constants for ctags installation
CTAGS_DOWNLOAD_URL = "https://github.com/universal-ctags/ctags-win32/releases/download/p6.2.20251116.0/ctags-p6.2.20251116.0-x64.zip"
CTAGS_LOCAL_DIR = Path.home() / ".clickup_framework" / "bin"
CTAGS_EXE = CTAGS_LOCAL_DIR / "ctags.exe"


def get_ctags_executable() -> Optional[str]:
    """
    Get the ctags executable path.

    Checks in order:
    1. Local installation in ~/.clickup_framework/bin/ctags.exe
    2. System PATH

    Returns:
        Path to ctags executable or None if not found
    """
    # Check local installation first
    if CTAGS_EXE.exists():
        return str(CTAGS_EXE)

    # Check system PATH
    try:
        result = subprocess.run(
            ['ctags', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return 'ctags'
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    return None


def check_ctags_available() -> bool:
    """Check if ctags is available."""
    return get_ctags_executable() is not None


def install_ctags_locally(use_color: bool = False) -> bool:
    """
    Download and install ctags locally to ~/.clickup_framework/bin/

    Args:
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create local bin directory
        CTAGS_LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        # Download the zip file
        zip_path = CTAGS_LOCAL_DIR / "ctags.zip"

        if use_color:
            print(colorize(f"[PROGRESS] Downloading ctags from {CTAGS_DOWNLOAD_URL}...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Downloading ctags from {CTAGS_DOWNLOAD_URL}...")

        # Download with progress
        def reporthook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(block_num * block_size * 100 / total_size, 100)
                print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

        urllib.request.urlretrieve(CTAGS_DOWNLOAD_URL, zip_path, reporthook)
        print()  # New line after progress

        # Extract the zip file
        if use_color:
            print(colorize("[PROGRESS] Extracting ctags...", TextColor.BRIGHT_BLUE))
        else:
            print("[PROGRESS] Extracting ctags...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract only ctags.exe
            for member in zip_ref.namelist():
                if member.endswith('ctags.exe'):
                    # Extract to bin directory
                    source = zip_ref.open(member)
                    target = CTAGS_EXE
                    with target.open('wb') as f:
                        shutil.copyfileobj(source, f)
                    break

        # Clean up zip file
        zip_path.unlink()

        # Verify installation
        if CTAGS_EXE.exists():
            if use_color:
                print(colorize(f"[SUCCESS] ctags installed to {CTAGS_EXE}", TextColor.GREEN))
            else:
                print(f"[SUCCESS] ctags installed to {CTAGS_EXE}")
            return True
        else:
            if use_color:
                print(colorize("[ERROR] Failed to extract ctags.exe", TextColor.RED), file=sys.stderr)
            else:
                print("[ERROR] Failed to extract ctags.exe", file=sys.stderr)
            return False

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to install ctags: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to install ctags: {e}", file=sys.stderr)
        return False


def generate_ctags(language: Optional[str] = None, output_file: str = '.tags.json', ctags_exe: Optional[str] = None) -> bool:
    """
    Generate ctags JSON output.

    Args:
        language: Language filter ('python', 'csharp', 'all', or None for all)
        output_file: Output file path
        ctags_exe: Path to ctags executable (if None, will use system ctags)

    Returns:
        True if successful, False otherwise
    """
    if ctags_exe is None:
        ctags_exe = 'ctags'

    cmd = [
        ctags_exe,
        '--output-format=json',
        '--quiet',
        '--exclude=.venv',
        '--exclude=node_modules',
        '--exclude=bin',
        '--exclude=obj',
        '--exclude=.git',
        '-R',
        '.'
    ]

    # Add language filter if specified
    if language == 'python':
        cmd.extend(['--languages=Python'])
    elif language == 'csharp':
        cmd.extend(['--languages=C#'])
    # 'all' or None means no language filter

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

        return result.returncode == 0
    except Exception as e:
        print(f"Error generating ctags: {e}", file=sys.stderr)
        return False


def parse_tags_file(tags_file: Path) -> Dict:
    """
    Parse ctags JSON output and collect statistics plus call graph data.

    Args:
        tags_file: Path to tags JSON file

    Returns:
        Dictionary with statistics and symbol data
    """
    stats = defaultdict(lambda: defaultdict(int))
    symbols_by_file = defaultdict(list)
    all_symbols = {}  # name -> symbol data
    function_calls = defaultdict(set)  # function -> set of functions it might call
    total = 0
    files = set()

    try:
        with open(tags_file, encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('_type') != 'tag':
                        continue

                    lang = data.get('language', 'Unknown')
                    kind = data.get('kind', 'other')
                    path = data.get('path', '')
                    name = data.get('name', '')
                    line_num = data.get('line', 0)
                    scope = data.get('scope', '')
                    scope_kind = data.get('scopeKind', '')

                    stats[lang][kind] += 1
                    total += 1
                    files.add(path)

                    symbol_data = {
                        'name': name,
                        'kind': kind,
                        'language': lang,
                        'line': line_num,
                        'scope': scope,
                        'scopeKind': scope_kind,
                        'path': path,
                        'pattern': data.get('pattern', '')
                    }

                    # Store symbol info for diagram generation
                    symbols_by_file[path].append(symbol_data)

                    # Index all functions/methods for call graph
                    if kind in ['function', 'method']:
                        full_name = f"{scope}.{name}" if scope else name
                        all_symbols[full_name] = symbol_data
                        all_symbols[name] = symbol_data  # Also index by short name

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        # Now parse file contents to find function calls
        for file_path in files:
            try:
                full_path = Path(file_path)
                if not full_path.exists():
                    continue

                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find functions defined in this file
                file_functions = [s for s in symbols_by_file[file_path]
                                if s['kind'] in ['function', 'method']]

                for func in file_functions:
                    func_name = func['name']
                    full_func_name = f"{func['scope']}.{func_name}" if func['scope'] else func_name

                    # Look for function calls in the pattern/code
                    # This is approximate - searches for function_name( patterns
                    for other_func_name in all_symbols.keys():
                        if other_func_name == func_name:
                            continue
                        # Simple pattern: function_name(
                        if f"{other_func_name}(" in content:
                            function_calls[full_func_name].add(other_func_name)

            except Exception:
                continue

        return {
            'total_symbols': total,
            'files_analyzed': len(files),
            'by_language': dict(stats),
            'symbols_by_file': dict(symbols_by_file),
            'files': sorted(files),
            'all_symbols': all_symbols,
            'function_calls': {k: list(v) for k, v in function_calls.items()}
        }
    except Exception as e:
        print(f"Error parsing tags file: {e}", file=sys.stderr)
        return {}


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


def export_mermaid_to_html(mermaid_content: str, output_file: str, title: str = "Code Map", use_color: bool = False) -> bool:
    """
    Export mermaid diagram to interactive HTML with zoom, pan, and animations.

    Args:
        mermaid_content: Mermaid diagram code
        output_file: Output HTML file path
        title: Page title
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#10b981',
                primaryTextColor: '#10b981',
                primaryBorderColor: '#059669',
                lineColor: '#10b981',
                secondaryColor: '#8b5cf6',
                tertiaryColor: '#a855f7',
                background: '#000000',
                mainBkg: '#0a0a0a',
                secondBkg: '#1a1a1a',
                tertiaryBkg: '#2a2a2a',
                lineColor: '#10b981',
                border1: '#10b981',
                border2: '#8b5cf6',
                arrowheadColor: '#10b981',
                fontFamily: 'ui-monospace, monospace',
                clusterBkg: '#1a1a1a',
                clusterBorder: '#10b981',
                edgeLabelBackground: '#0a0a0a',
                nodeTextColor: '#10b981'
            }},
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }},
            sequence: {{
                useMaxWidth: false,
                wrap: true,
                height: 600
            }},
            class: {{
                useMaxWidth: false
            }},
            er: {{
                useMaxWidth: false
            }},
            securityLevel: 'loose',
            logLevel: 'info'
        }});
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #1a1a1a 100%);
            color: #10b981;
            min-height: 100vh;
            overflow: hidden;
        }}
        .container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        .header {{
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 2px solid #10b981;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
            z-index: 100;
        }}
        .header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #10b981;
            text-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
        }}
        .controls {{
            margin-top: 0.5rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        .btn {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #000;
            border: 1px solid #10b981;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }}
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: #fff;
            border-color: #8b5cf6;
        }}
        .btn:active {{
            transform: translateY(0);
        }}
        .zoom-info {{
            font-size: 0.875rem;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .diagram-wrapper {{
            flex: 1;
            position: relative;
            overflow: hidden;
            background: radial-gradient(circle at 50% 50%, #0a0a0a 0%, #000000 100%);
        }}
        .diagram-container {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            transform-origin: center center;
            cursor: grab;
            will-change: transform;
        }}
        .diagram-container:active {{
            cursor: grabbing;
        }}
        .diagram-container.zoomed {{
            cursor: move;
        }}
        #mermaid-diagram {{
            display: inline-block;
            background: rgba(10, 10, 10, 0.8);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5),
                        0 0 50px rgba(16, 185, 129, 0.2),
                        inset 0 0 50px rgba(139, 92, 246, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(16, 185, 129, 0.3);
        }}
        /* Mermaid node animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .node, .cluster, .edgePath {{
            animation: fadeInUp 0.5s ease-out backwards;
        }}
        .node:nth-child(1) {{ animation-delay: 0.05s; }}
        .node:nth-child(2) {{ animation-delay: 0.1s; }}
        .node:nth-child(3) {{ animation-delay: 0.15s; }}
        .node:nth-child(4) {{ animation-delay: 0.2s; }}
        .node:nth-child(5) {{ animation-delay: 0.25s; }}
        /* Hover effects - avoid transform conflicts */
        .node {{
            transition: filter 0.2s ease, opacity 0.2s ease;
            cursor: pointer;
        }}
        .node:hover {{
            filter: brightness(1.5) drop-shadow(0 0 20px rgba(139, 92, 246, 1)) drop-shadow(0 0 40px rgba(16, 185, 129, 0.6));
        }}
        .node rect, .node circle, .node polygon, .node path {{
            transition: all 0.2s ease;
        }}
        .node:hover rect,
        .node:hover circle,
        .node:hover polygon,
        .node:hover path {{
            stroke-width: 3px !important;
        }}
        .edgePath {{
            transition: filter 0.2s ease;
        }}
        .edgePath:hover path {{
            stroke-width: 3px !important;
            filter: drop-shadow(0 0 8px rgba(147, 197, 253, 0.8));
        }}
        /* Loading animation */
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
        .spinner {{
            border: 4px solid #334155;
            border-top: 4px solid #60a5fa;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .fullscreen {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 9999;
        }}
        .fullscreen .diagram-container {{
            padding: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container" id="container">
        <div class="header">
            <h1>🗺️ {title}</h1>
            <div class="controls">
                <button class="btn" onclick="zoomIn()">🔍 Zoom In</button>
                <button class="btn" onclick="zoomOut()">🔍 Zoom Out</button>
                <button class="btn" onclick="resetZoom()">↺ Reset</button>
                <button class="btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
                <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
                <span class="zoom-info">
                    <span>Zoom:</span>
                    <strong id="zoom-level">100%</strong>
                    <span style="margin-left: 1rem">💡 Scroll to zoom, drag to pan</span>
                </span>
            </div>
        </div>
        <div class="diagram-wrapper">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Rendering diagram...</p>
            </div>
            <div class="diagram-container" id="diagram-container">
                <div class="mermaid" id="mermaid-diagram">
{mermaid_code}
                </div>
            </div>
        </div>
    </div>

    <script>
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        const container = document.getElementById('diagram-container');
        const zoomLevelEl = document.getElementById('zoom-level');

        // Hide loading when mermaid is ready
        window.addEventListener('load', () => {{
            setTimeout(() => {{
                document.getElementById('loading').style.display = 'none';

                // Add click handlers to nodes
                document.querySelectorAll('.node').forEach(node => {{
                    node.addEventListener('click', (e) => {{
                        const label = node.querySelector('text')?.textContent;
                        if (label) {{
                            alert('Node: ' + label);
                        }}
                    }});
                }});
            }}, 500);
        }});

        function updateTransform() {{
            // Use translate3d for better performance and to avoid conflicts
            container.style.transform = `translate3d(${{translateX}}px, ${{translateY}}px, 0) scale(${{scale}})`;
            zoomLevelEl.textContent = Math.round(scale * 100) + '%';
            container.classList.toggle('zoomed', scale !== 1);
        }}

        function zoomIn() {{
            scale = Math.min(scale * 1.2, 5);
            updateTransform();
        }}

        function zoomOut() {{
            scale = Math.max(scale / 1.2, 0.1);
            updateTransform();
        }}

        function resetZoom() {{
            scale = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        }}

        // Mouse wheel zoom
        container.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale = Math.max(0.1, Math.min(5, scale * delta));
            updateTransform();
        }});

        // Drag to pan - avoid dragging when clicking nodes
        container.addEventListener('mousedown', (e) => {{
            // Don't start dragging if clicking on a node
            if (e.target.closest('.node')) {{
                return;
            }}
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            updateTransform();
        }});

        document.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        // Fullscreen
        function toggleFullscreen() {{
            const elem = document.getElementById('container');
            if (!document.fullscreenElement) {{
                elem.requestFullscreen().catch(err => {{
                    console.log('Fullscreen error:', err);
                }});
            }} else {{
                document.exitFullscreen();
            }}
        }}

        // Download SVG
        function downloadSVG() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'diagram.svg';
                a.click();
                URL.revokeObjectURL(url);
            }}
        }}

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === '+' || e.key === '=') zoomIn();
            if (e.key === '-' || e.key === '_') zoomOut();
            if (e.key === '0') resetZoom();
            if (e.key === 'f' || e.key === 'F') toggleFullscreen();
        }});
    </script>
</body>
</html>'''

    try:
        html_content = html_template.format(
            title=title,
            mermaid_code=mermaid_content
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        if use_color:
            print(colorize(f"[SUCCESS] Interactive HTML: {output_file}", TextColor.GREEN))
        else:
            print(f"[SUCCESS] Interactive HTML: {output_file}")

        return True

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to generate HTML: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to generate HTML: {e}", file=sys.stderr)
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


def generate_mermaid_flowchart(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid flowchart diagram showing directory structure with symbol details.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    # Build mermaid diagram
    lines = [
        "# Code Map - Architecture Diagram",
        "",
        "```mermaid",
        "graph TB"
    ]

    # Group files by directory
    dir_structure = defaultdict(list)
    for file_path, symbols in symbols_by_file.items():
        if symbols:
            dir_name = str(Path(file_path).parent)
            if dir_name == '.':
                dir_name = 'root'
            dir_structure[dir_name].append((file_path, symbols))

    # Sort directories and limit
    sorted_dirs = sorted(dir_structure.keys())[:10]

    # Create directory nodes
    dir_nodes = {}
    for idx, dir_name in enumerate(sorted_dirs):
        dir_id = f"DIR{idx}"
        dir_nodes[dir_name] = dir_id
        # Count total symbols in directory
        total_symbols = sum(len(syms) for _, syms in dir_structure[dir_name])
        safe_dir = dir_name.replace('\\', '/').replace('clickup_framework/', '')
        lines.append(f"    {dir_id}[\"{safe_dir}<br/>{total_symbols} symbols\"]")
        lines.append(f"    style {dir_id} fill:#1e3a8a,stroke:#60a5fa,stroke-width:3px")

    lines.append("")

    # Add file nodes with more detail
    file_count = 0
    for dir_name in sorted_dirs:
        files = sorted(dir_structure[dir_name], key=lambda x: len(x[1]), reverse=True)[:5]  # Top 5 files per dir

        for file_path, symbols in files:
            file_id = f"F{file_count}"
            file_name = Path(file_path).name

            # Count different symbol types
            classes = sum(1 for s in symbols if s.get('kind') == 'class')
            functions = sum(1 for s in symbols if s.get('kind') in ['function', 'method'])
            members = sum(1 for s in symbols if s.get('kind') in ['member', 'variable'])

            # Build detailed label
            parts = []
            if classes: parts.append(f"📦 {classes} classes")
            if functions: parts.append(f"⚙️ {functions} funcs")
            if members: parts.append(f"📊 {members} vars")

            detail = "<br/>".join(parts) if parts else f"{len(symbols)} symbols"
            lines.append(f"    {file_id}[\"{file_name}<br/>{detail}\"]")

            # Link file to directory
            if dir_name in dir_nodes:
                lines.append(f"    {dir_nodes[dir_name]} --> {file_id}")

            # Add class nodes for files with classes
            if classes > 0 and classes <= 5:
                class_symbols = [s for s in symbols if s.get('kind') == 'class']
                for cls_idx, cls in enumerate(class_symbols):
                    cls_id = f"C{file_count}_{cls_idx}"
                    cls_name = cls.get('name', 'Unknown')

                    # Count methods in this class
                    methods = [s for s in symbols if s.get('scope') == cls_name and s.get('kind') in ['function', 'method']]
                    lines.append(f"    {cls_id}[\"{cls_name}<br/>{len(methods)} methods\"]")
                    lines.append(f"    style {cls_id} fill:#065f46,stroke:#34d399")
                    lines.append(f"    {file_id} --> {cls_id}")

            file_count += 1

            if file_count >= 30:
                break

        if file_count >= 30:
            break

    lines.append("```")
    lines.append("")

    # Add statistics summary
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
        ""
    ])

    # Add language breakdown
    lines.append("### By Language")
    lines.append("")
    for lang in sorted(by_language.keys()):
        count = sum(by_language[lang].values())
        lines.append(f"- **{lang}**: {count} symbols")
        for kind, kind_count in sorted(by_language[lang].items()):
            lines.append(f"  - {kind}: {kind_count}")

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_class(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid class diagram showing detailed code structure with inheritance.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Class Diagram",
        "",
        "```mermaid",
        "classDiagram"
    ]

    # Track classes and their details
    all_classes = {}
    class_count = 0

    for file_path, symbols in sorted(symbols_by_file.items()):
        if class_count >= 20:
            break

        # Find classes in this file
        classes = [s for s in symbols if s.get('kind') == 'class']
        for cls in classes:
            class_name = cls.get('name', 'Unknown')

            # Skip if we already have this class
            if class_name in all_classes:
                continue

            all_classes[class_name] = {
                'file': Path(file_path).name,
                'line': cls.get('line', 0),
                'methods': [],
                'members': []
            }

            # Find methods in this class
            methods = [s for s in symbols
                      if s.get('scope') == class_name
                      and s.get('kind') in ['function', 'method']]

            # Find members/attributes
            members = [s for s in symbols
                      if s.get('scope') == class_name
                      and s.get('kind') in ['member', 'variable']]

            all_classes[class_name]['methods'] = methods[:15]
            all_classes[class_name]['members'] = members[:10]

            class_count += 1

    # Generate class definitions with details
    for class_name, details in sorted(all_classes.items()):
        lines.append(f"    class {class_name} {{")

        # Add file annotation
        lines.append(f"        <<{details['file']}>>")

        # Add members
        for member in details['members']:
            member_name = member.get('name', '')
            lines.append(f"        -{member_name}")

        # Add methods with visibility
        for method in details['methods']:
            method_name = method.get('name', '')
            # Determine visibility based on naming convention
            if method_name.startswith('_'):
                visibility = '-'  # private
            elif method_name.startswith('__'):
                visibility = '-'  # private
            else:
                visibility = '+'  # public
            lines.append(f"        {visibility}{method_name}()")

        lines.append("    }")

    # Try to detect inheritance relationships
    lines.append("")
    lines.append("    %% Inheritance relationships")
    for class_name in all_classes.keys():
        # Common base class patterns
        if 'Base' in class_name:
            # Find classes that might inherit from this
            for other_class in all_classes.keys():
                if other_class != class_name and 'Base' not in other_class:
                    if any(word in other_class for word in class_name.replace('Base', '').split()):
                        lines.append(f"    {class_name} <|-- {other_class}")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_pie(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid pie chart showing language distribution.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Language Distribution",
        "",
        "```mermaid",
        "pie title Code Distribution by Language"
    ]

    for lang in sorted(by_language.keys()):
        count = sum(by_language[lang].values())
        lines.append(f"    \"{lang}\" : {count}")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_mindmap(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid mindmap showing code structure hierarchy.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Mind Map",
        "",
        "```mermaid",
        "mindmap",
        "  root((Codebase))"
    ]

    # Group by language
    for lang in sorted(by_language.keys())[:5]:  # Limit languages
        lines.append(f"    {lang}")

        # Find files for this language
        lang_files = []
        for file_path, symbols in symbols_by_file.items():
            if symbols and symbols[0].get('language') == lang:
                lang_files.append((file_path, symbols))

        # Show top files by symbol count
        lang_files.sort(key=lambda x: len(x[1]), reverse=True)
        for file_path, symbols in lang_files[:5]:  # Top 5 files per language
            file_name = Path(file_path).name
            symbol_count = len(symbols)
            lines.append(f"      {file_name} ({symbol_count})")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_code_flow(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid flowchart showing actual code execution flow with subgraphs by class/module.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    function_calls = stats.get('function_calls', {})
    all_symbols = stats.get('all_symbols', {})

    lines = [
        "# Code Map - Execution Flow (Call Graph)",
        "",
        "```mermaid",
        "graph TB"
    ]

    # Find entry points (functions not called by others)
    called_functions = set()
    for calls in function_calls.values():
        called_functions.update(calls)

    entry_points = [func for func in function_calls.keys()
                   if func not in called_functions][:8]  # More entry points

    # Group functions by class/module
    functions_by_class = defaultdict(list)
    processed = set()
    node_count = 0
    node_ids = {}  # Map func_name to node_id

    def collect_functions(func_name, depth=0, max_depth=4):
        nonlocal node_count

        if depth > max_depth or func_name in processed or node_count >= 60:
            return

        processed.add(func_name)
        symbol = all_symbols.get(func_name, {})
        scope = symbol.get('scope', '')

        # Group by class or module
        if scope:
            functions_by_class[scope].append(func_name)
        else:
            # Use file as grouping if no class
            file_name = Path(symbol.get('path', 'global')).stem
            functions_by_class[f"module_{file_name}"].append(func_name)

        node_count += 1

        # Recursively collect called functions
        calls = function_calls.get(func_name, [])
        for called_func in calls[:5]:
            if called_func not in processed:
                collect_functions(called_func, depth + 1, max_depth)

    # Collect all functions starting from entry points
    for entry in entry_points:
        if node_count >= 60:
            break
        collect_functions(entry, depth=0, max_depth=4)

    # Generate subgraphs for each class/module
    subgraph_count = 0
    for class_name, funcs in sorted(functions_by_class.items())[:10]:  # Limit to 10 subgraphs
        if not funcs:
            continue

        subgraph_id = f"SG{subgraph_count}"
        subgraph_count += 1

        # Clean class name for display
        display_name = class_name.replace('module_', '📦 ')

        # Start subgraph
        lines.append(f"    subgraph {subgraph_id}[\"{display_name}\"]")

        # Add nodes for functions in this class
        for func_name in funcs[:8]:  # Limit functions per subgraph
            symbol = all_symbols.get(func_name, {})
            node_id = f"N{len(node_ids)}"
            node_ids[func_name] = node_id

            display_func = func_name.split('.')[-1]
            file_name = Path(symbol.get('path', '')).name
            line_start = symbol.get('line', 0)

            # Try to estimate end line (approximate)
            # In real implementation, ctags can provide this with --fields=+ne
            line_end = line_start + 10  # Placeholder

            # Create node with line numbers
            lines.append(f"        {node_id}[\"{display_func}()<br/>📄 {file_name}<br/>📍 L{line_start}-{line_end}\"]")

        lines.append("    end")
        lines.append("")

    # Add connections between nodes
    lines.append("    %% Connections")
    for func_name, calls in function_calls.items():
        if func_name not in node_ids:
            continue

        from_id = node_ids[func_name]
        for called_func in calls[:5]:
            if called_func in node_ids:
                to_id = node_ids[called_func]
                lines.append(f"    {from_id} --> {to_id}")

    lines.append("")

    # Apply green/black/purple theme styling
    lines.append("    %% Styling - Green/Black/Purple Theme")

    # Style subgraphs with different colors
    colors = [
        ("fill:#10b981,stroke:#059669,color:#000", "emerald"),  # Emerald green
        ("fill:#8b5cf6,stroke:#7c3aed,color:#fff", "purple"),   # Purple
        ("fill:#06b6d4,stroke:#0891b2,color:#000", "cyan"),     # Cyan
        ("fill:#f59e0b,stroke:#d97706,color:#000", "amber"),    # Amber
        ("fill:#ec4899,stroke:#db2777,color:#fff", "pink"),     # Pink
    ]

    for i in range(subgraph_count):
        color_style, _ = colors[i % len(colors)]
        lines.append(f"    style SG{i} {color_style}")

    # Style nodes based on whether they're entry points
    for func_name, node_id in node_ids.items():
        if func_name in entry_points:
            # Entry points - bright purple glow
            lines.append(f"    style {node_id} fill:#a855f7,stroke:#9333ea,stroke-width:3px,color:#fff")
        else:
            # Regular nodes - dark with green accent
            lines.append(f"    style {node_id} fill:#1a1a1a,stroke:#10b981,stroke-width:2px,color:#10b981")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Legend",
        "- 🟣 **Purple nodes**: Entry points (functions not called by others)",
        "- 🟢 **Green-bordered nodes**: Called functions",
        "- **Subgraphs**: Group functions by class/module",
        "- **Line numbers**: Show start-end lines in source file",
        "",
        f"## Statistics",
        f"- **Total Functions Mapped**: {len(processed)}",
        f"- **Classes/Modules**: {len(functions_by_class)}",
        f"- **Total Call Relationships**: {sum(len(calls) for calls in function_calls.values())}",
        f"- **Entry Points Found**: {len(entry_points)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_sequence(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid sequence diagram showing typical execution flow.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    function_calls = stats.get('function_calls', {})
    all_symbols = stats.get('all_symbols', {})
    symbols_by_file = stats.get('symbols_by_file', {})

    lines = [
        "# Code Map - Sequence Diagram",
        "",
        "```mermaid",
        "sequenceDiagram"
    ]

    # Find main entry points (common patterns)
    entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
    entry_funcs = []

    for func_name in function_calls.keys():
        short_name = func_name.split('.')[-1].lower()
        if any(pattern in short_name for pattern in entry_patterns):
            entry_funcs.append(func_name)

    if not entry_funcs:
        # Fallback: find functions with most calls
        entry_funcs = sorted(function_calls.keys(),
                           key=lambda f: len(function_calls.get(f, [])),
                           reverse=True)[:3]

    # Generate sequence for first entry point
    if entry_funcs:
        entry = entry_funcs[0]
        symbol = all_symbols.get(entry, {})
        scope = symbol.get('scope', '')

        # Identify participants (classes/modules)
        participants = set()
        if scope:
            participants.add(scope)

        # Trace through calls
        def trace_calls(func, depth=0, max_depth=5):
            if depth > max_depth:
                return

            symbol = all_symbols.get(func, {})
            scope = symbol.get('scope', 'Module')
            func_short = func.split('.')[-1]

            if scope:
                participants.add(scope)

            # Add calls
            for called in function_calls.get(func, [])[:3]:  # Limit to 3 calls per function
                called_symbol = all_symbols.get(called, {})
                called_scope = called_symbol.get('scope', 'Module')
                called_short = called.split('.')[-1]

                if called_scope:
                    participants.add(called_scope)

                from_participant = scope if scope else 'Module'
                to_participant = called_scope if called_scope else 'Module'

                lines.append(f"    {from_participant}->>+{to_participant}: {called_short}()")
                trace_calls(called, depth + 1, max_depth)
                lines.append(f"    {to_participant}-->>-{from_participant}: return")

        # Add participants
        for participant in sorted(participants)[:10]:  # Limit participants
            lines.insert(3, f"    participant {participant}")

        # Trace from entry point
        entry_short = entry.split('.')[-1]
        entry_scope = all_symbols.get(entry, {}).get('scope', 'Main')
        if entry_scope:
            lines.append(f"    Note over {entry_scope}: {entry_short}() starts")
        trace_calls(entry, depth=0, max_depth=4)

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Description",
        "This sequence diagram shows the typical execution flow starting from an entry point.",
        "Arrows show function calls and returns between different components.",
        "",
        f"## Entry Point",
        f"- Starting from: `{entry_funcs[0] if entry_funcs else 'N/A'}`",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def map_command(args):
    """Generate code map using ctags."""
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Handle installation request
    if args.install:
        if use_color:
            print()
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print(colorize("Installing ctags locally", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print()
        else:
            print()
            print("=" * 80)
            print("Installing ctags locally")
            print("=" * 80)
            print()

        success = install_ctags_locally(use_color)
        sys.exit(0 if success else 1)

    # Check if ctags is available
    ctags_exe = get_ctags_executable()
    if not ctags_exe:
        error_msg = "ERROR: ctags not found. Install with: cum map --install"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            print(colorize("Or install system-wide with: choco install universal-ctags", TextColor.YELLOW), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
            print("Or install system-wide with: choco install universal-ctags", file=sys.stderr)
        sys.exit(1)

    # Determine language filter
    language = None
    if args.python:
        language = 'python'
    elif args.csharp:
        language = 'csharp'
    elif args.all_langs:
        language = 'all'

    # Determine output file
    tags_file = Path('.tags.json')

    # Print header
    if use_color:
        print()
        print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
        print(colorize("Universal ctags Code Map Generator", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
        print()
    else:
        print()
        print("=" * 80)
        print("Universal ctags Code Map Generator")
        print("=" * 80)
        print()

    # Show configuration
    lang_display = language if language else 'all'
    if use_color:
        print(f"[INFO] Filter: {colorize(lang_display, TextColor.BRIGHT_YELLOW)}")
        print(f"[INFO] Output: {colorize(str(tags_file), TextColor.BRIGHT_YELLOW)}")
    else:
        print(f"[INFO] Filter: {lang_display}")
        print(f"[INFO] Output: {tags_file}")
    print()

    # Generate ctags
    if use_color:
        print(colorize("[PROGRESS] Generating tags...", TextColor.BRIGHT_BLUE))
    else:
        print("[PROGRESS] Generating tags...")

    if not generate_ctags(language, str(tags_file), ctags_exe):
        error_msg = "[ERROR] Failed to generate ctags"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)

    if use_color:
        print(colorize("[SUCCESS] Tags generated successfully", TextColor.GREEN))
    else:
        print("[SUCCESS] Tags generated successfully")

    # Parse and analyze tags
    if use_color:
        print(colorize("[PROGRESS] Analyzing symbols...", TextColor.BRIGHT_BLUE))
    else:
        print("[PROGRESS] Analyzing symbols...")

    stats = parse_tags_file(tags_file)

    if not stats:
        error_msg = "[ERROR] Failed to parse tags file"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Display statistics
    print()
    if use_color:
        print(colorize("Summary:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print("Summary:")
    print(f"  Total symbols: {stats['total_symbols']}")
    print(f"  Files analyzed: {stats['files_analyzed']}")
    print(f"  Languages: {len(stats['by_language'])}")
    print()

    if use_color:
        print(colorize("By Language:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print("By Language:")

    for lang in sorted(stats['by_language'].keys()):
        count = sum(stats['by_language'][lang].values())
        print(f"  {lang}: {count} symbols")

    print()

    # Generate mermaid diagram if requested
    mermaid_file = None
    output_path = None
    export_success = False
    if args.mer:
        # Map diagram types to generator functions
        diagram_generators = {
            'flowchart': generate_mermaid_flowchart,
            'swim': generate_mermaid_flowchart,  # Alias
            'class': generate_mermaid_class,
            'pie': generate_mermaid_pie,
            'mindmap': generate_mermaid_mindmap,
            'sequence': generate_mermaid_sequence,
            'flow': generate_mermaid_code_flow,
        }

        generator = diagram_generators.get(args.mer.lower())
        if not generator:
            error_msg = f"Unknown mermaid diagram type: {args.mer}. Valid types: {', '.join(diagram_generators.keys())}"
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)
            sys.exit(1)

        # Determine mermaid markdown output path
        mermaid_file = Path(f'docs/codemap/diagram_{args.mer}.md')

        # Create parent directory if needed
        mermaid_file.parent.mkdir(parents=True, exist_ok=True)

        if use_color:
            print(colorize(f"[PROGRESS] Generating {args.mer} mermaid diagram...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Generating {args.mer} mermaid diagram...")

        generator(stats, str(mermaid_file))

        if use_color:
            print(colorize(f"[SUCCESS] Mermaid diagram: {mermaid_file}", TextColor.GREEN))
        else:
            print(f"[SUCCESS] Mermaid diagram: {mermaid_file}")
        print()

        # Export to image or HTML if --output is specified
        if args.output:
            output_path = Path(args.output)

            # Check if HTML output is requested
            if args.html or output_path.suffix.lower() == '.html':
                # Read mermaid content from markdown file
                with open(mermaid_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract mermaid code block
                    import re
                    match = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
                    if match:
                        mermaid_code = match.group(1)
                        if not output_path.suffix:
                            output_path = output_path.with_suffix('.html')
                        export_success = export_mermaid_to_html(
                            mermaid_code,
                            str(output_path),
                            title=f"Code Map - {args.mer.title()}",
                            use_color=use_color
                        )
                        if export_success:
                            print()
            else:
                # Image export
                if args.format:
                    image_format = args.format.lower()
                else:
                    # Infer from file extension
                    ext = output_path.suffix.lstrip('.')
                    image_format = ext if ext in ['png', 'svg', 'jpg'] else 'png'

                # Ensure correct extension
                if not output_path.suffix or output_path.suffix.lstrip('.') != image_format:
                    output_path = output_path.with_suffix(f'.{image_format}')

                # Export using mmdc
                export_success = export_mermaid_to_image(str(mermaid_file), str(output_path), image_format, use_color)
                if export_success:
                    print()

    # Final summary
    if use_color:
        print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
        print(colorize("[COMPLETE] Code map generated successfully", TextColor.GREEN, TextStyle.BOLD))
        print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
    else:
        print("=" * 80)
        print("[COMPLETE] Code map generated successfully")
        print("=" * 80)

    print()
    print("Files:")
    print(f"  - {tags_file} (JSON tags)")
    if mermaid_file:
        print(f"  - {mermaid_file} (Mermaid diagram)")
    if export_success and output_path:
        print(f"  - {output_path} (Image export)")
    print()


def register_command(subparsers):
    """Register the map command with the CLI parser."""
    parser = subparsers.add_parser(
        'map',
        help='Generate code map using ctags'
    )

    # Language filter options (mutually exclusive)
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument(
        '--python',
        action='store_true',
        help='Generate map for Python files only'
    )
    lang_group.add_argument(
        '--csharp',
        action='store_true',
        help='Generate map for C# files only'
    )
    lang_group.add_argument(
        '--all-langs',
        action='store_true',
        help='Generate map for all supported languages'
    )

    # Installation option
    parser.add_argument(
        '--install',
        action='store_true',
        help='Download and install ctags locally to ~/.clickup_framework/bin/'
    )

    # Mermaid diagram option
    parser.add_argument(
        '--mer',
        type=str,
        choices=['flowchart', 'swim', 'class', 'pie', 'mindmap', 'sequence', 'flow'],
        help='Generate mermaid diagram: flowchart (structure), flow (execution flow/calls), sequence, class, pie, mindmap'
    )

    # Image output option (requires --mer)
    parser.add_argument(
        '--output',
        type=str,
        help='Export diagram to image file (png/svg/jpg) using mmdc. Requires --mer and mermaid-cli (npm install -g @mermaid-js/mermaid-cli)'
    )

    # Image format option
    parser.add_argument(
        '--format',
        type=str,
        choices=['png', 'svg', 'jpg'],
        help='Image format for --output (default: inferred from file extension or png)'
    )

    # Interactive HTML option
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate interactive HTML with zoom, pan, animations, and click handlers'
    )

    parser.set_defaults(func=map_command)
