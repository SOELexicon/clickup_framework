"""Code mapping command using ctags for ClickUp Framework CLI."""

import sys
import os
import json
import re
import subprocess
import zipfile
import urllib.request
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List, Set, Union
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle

# Metadata for automatic help generation
COMMAND_METADATA = {
    "category": "🛠️  Utility Commands",
    "commands": [
        {
            "name": "map",
            "args": "[--python|--csharp|--all-langs] [--mer TYPE] [--output FILE] [--format FORMAT] [--install] [--ignore-gitignore]",
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


def generate_ctags(language: Optional[str] = None, output_file: str = '.tags.json', ctags_exe: Optional[str] = None, ignore_gitignore: bool = False, in_memory: bool = True) -> Union[bool, str]:
    """
    Generate ctags JSON output.

    Args:
        language: Language filter ('python', 'csharp', 'all', or None for all)
        output_file: Output file path (only used if in_memory=False)
        ctags_exe: Path to ctags executable (if None, will use system ctags)
        ignore_gitignore: If True, scan bin/obj and other typically ignored directories
        in_memory: If True, return JSON string; if False, write to file and return success bool

    Returns:
        If in_memory=True: JSON string on success, None on failure
        If in_memory=False: True if successful, False otherwise
    """
    if ctags_exe is None:
        ctags_exe = 'ctags'

    cmd = [
        ctags_exe,
        '--output-format=json',
        '--fields=+ne',  # n=line number, e=end line
        '--quiet',
        '--exclude=.venv',
        '--exclude=venv',
        '--exclude=env',
        '--exclude=.env',
        '--exclude=node_modules',
        '--exclude=.git',
        '--exclude=__pycache__',
        '--exclude=*.pyc',
        '--exclude=.pytest_cache',
        '--exclude=.tox',
        '--exclude=dist',
        '--exclude=build',
        '--exclude=*.egg-info',
        '--exclude=.coverage',
        '--exclude=htmlcov',
        '--langmap=C#:+.razor',  # Add Razor component support
        '--langmap=C#:+.razor.cs',  # Add Razor code-behind support
        '--langmap=C#:+.cshtml',  # Add Razor view support (traditional Razor Pages)
        '-R',
        '.'
    ]

    # Process .gitignore file
    gitignore_path = Path('.gitignore')
    if ignore_gitignore and gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove leading slash if present
                        pattern = line.lstrip('/')
                        # Add as exception to override gitignore
                        cmd.insert(-2, f'--exclude-exception={pattern}')
        except Exception as e:
            print(f"Warning: Could not process .gitignore: {e}", file=sys.stderr)
    elif not ignore_gitignore:
        # Normal behavior: exclude build directories (including nested subdirectories)
        cmd.insert(-2, '--exclude=**/bin/**')
        cmd.insert(-2, '--exclude=**/obj/**')

    # Add language filter if specified
    if language == 'python':
        cmd.extend(['--languages=Python'])
    elif language == 'csharp':
        cmd.extend(['--languages=C#'])
    # 'all' or None means no language filter

    try:
        if in_memory:
            # Run ctags and capture output in memory
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 with placeholder
                timeout=300  # 5 minutes for large projects
            )

            if result.returncode == 0:
                return result.stdout  # Return JSON string
            else:
                print(f"Error generating ctags: {result.stderr}", file=sys.stderr)
                return None
        else:
            # Original file-based approach
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
        return None if in_memory else False


def parse_tags_file(tags_file: Union[Path, str], from_string: bool = False) -> Dict:
    """
    Parse ctags JSON output and collect statistics plus call graph data.

    Args:
        tags_file: Path to tags JSON file, or JSON string if from_string=True
        from_string: If True, tags_file is a JSON string; if False, it's a file path

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
        # Get iterator for lines (either from file or string)
        if from_string:
            lines = tags_file.splitlines() if isinstance(tags_file, str) else []
        else:
            with open(tags_file, encoding='utf-8') as f:
                lines = f.readlines()

        for line in lines:
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
                    'end': data.get('end', line_num),  # Capture end line from ctags
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

        # Now parse file contents to find function calls using improved pattern matching
        for file_path in files:
            try:
                full_path = Path(file_path)
                if not full_path.exists():
                    continue

                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Remove strings and comments to reduce false positives
                # Remove single-line comments (# in Python, // in C#)
                content_clean = re.sub(r'#.*?$', '', content, flags=re.MULTILINE)
                content_clean = re.sub(r'//.*?$', '', content_clean, flags=re.MULTILINE)
                # Remove multi-line comments (/* */ in C#)
                content_clean = re.sub(r'/\*.*?\*/', '', content_clean, flags=re.DOTALL)
                # Remove string literals (basic approach - may not catch all edge cases)
                content_clean = re.sub(r'"(?:[^"\\]|\\.)*"', '', content_clean)
                content_clean = re.sub(r"'(?:[^'\\]|\\.)*'", '', content_clean)

                # Find functions defined in this file
                file_functions = [s for s in symbols_by_file[file_path]
                                if s['kind'] in ['function', 'method']]

                for func in file_functions:
                    func_name = func['name']
                    full_func_name = f"{func['scope']}.{func_name}" if func['scope'] else func_name

                    # Look for function calls using regex with word boundaries
                    for other_func_name in all_symbols.keys():
                        if other_func_name == func_name or other_func_name == full_func_name:
                            continue

                        short_name = other_func_name.split('.')[-1]

                        # Skip very short names to avoid false positives
                        if len(short_name) < 3:
                            continue

                        # Use regex with word boundaries for accurate matching
                        # Pattern: word boundary, function name, optional whitespace, opening paren
                        pattern = r'\b' + re.escape(short_name) + r'\s*\('

                        if re.search(pattern, content_clean):
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
            startOnLoad: false,  // We'll manually load content from base64 to avoid HTML parsing
            theme: 'dark',
            themeVariables: {{
                primaryColor: 'rgba(16, 185, 129, 0.15)',
                primaryTextColor: '#10b981',
                primaryBorderColor: '#10b981',
                lineColor: '#34d399',
                secondaryColor: 'rgba(139, 92, 246, 0.15)',
                tertiaryColor: 'rgba(168, 85, 247, 0.15)',
                background: '#000000',
                mainBkg: 'rgba(10, 10, 10, 0.3)',
                secondBkg: 'rgba(26, 26, 26, 0.3)',
                tertiaryBkg: 'rgba(42, 42, 42, 0.3)',
                border1: '#10b981',
                border2: '#8b5cf6',
                arrowheadColor: '#10b981',
                fontFamily: 'ui-monospace, monospace',
                clusterBkg: 'rgba(26, 26, 26, 0.2)',
                clusterBorder: '#10b981',
                edgeLabelBackground: 'rgba(10, 10, 10, 0.8)',
                nodeTextColor: '#10b981'
            }},
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'linear',
                nodeSpacing: 100,
                rankSpacing: 100,
                defaultRenderer: 'elk'
            }},
            elk: {{
                mergeEdges: true,
                nodePlacementStrategy: 'SIMPLE'
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
            logLevel: 'error',
            arrowMarkerAbsolute: true
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
        .main-content {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        .sidebar {{
            width: 300px;
            background: rgba(10, 10, 10, 0.95);
            border-right: 2px solid #10b981;
            overflow-y: auto;
            padding: 1rem;
            box-shadow: 4px 0 6px -1px rgba(16, 185, 129, 0.3);
            transition: transform 0.3s ease;
        }}
        .sidebar.collapsed {{
            transform: translateX(-100%);
        }}
        .sidebar h2 {{
            color: #10b981;
            font-size: 1.125rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(16, 185, 129, 0.3);
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }}
        .sidebar-search {{
            width: 100%;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #10b981;
            padding: 0.5rem;
            color: #10b981;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
            font-family: ui-monospace, monospace;
        }}
        .sidebar-search:focus {{
            outline: none;
            border-color: #8b5cf6;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }}
        .file-tree {{
            list-style: none;
            padding: 0;
        }}
        .tree-item {{
            padding: 0.375rem 0.5rem;
            margin: 0.25rem 0;
            cursor: pointer;
            border-radius: 0.25rem;
            transition: all 0.2s;
            font-size: 0.875rem;
            font-family: ui-monospace, monospace;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .tree-item:hover {{
            background: rgba(16, 185, 129, 0.2);
            padding-left: 0.75rem;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }}
        .tree-item.active {{
            background: rgba(139, 92, 246, 0.3);
            border-left: 3px solid #8b5cf6;
            padding-left: 0.75rem;
        }}
        .tree-item .icon {{
            flex-shrink: 0;
        }}
        .tree-folder {{
            font-weight: 600;
            color: #8b5cf6;
        }}
        .tree-file {{
            color: #10b981;
        }}
        .tree-function {{
            color: #06b6d4;
            padding-left: 1.5rem;
            font-size: 0.8125rem;
        }}
        .tree-children {{
            padding-left: 1rem;
            border-left: 1px solid rgba(16, 185, 129, 0.2);
            margin-left: 0.5rem;
        }}
        .toggle-sidebar {{
            position: absolute;
            left: 300px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(16, 185, 129, 0.9);
            border: none;
            color: #000;
            padding: 0.5rem;
            cursor: pointer;
            border-radius: 0 0.25rem 0.25rem 0;
            z-index: 1000;
            transition: all 0.3s;
        }}
        .toggle-sidebar:hover {{
            background: #8b5cf6;
            color: #fff;
        }}
        .sidebar.collapsed ~ .toggle-sidebar {{
            left: 0;
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
        .spacing-control {{
            font-size: 0.875rem;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-left: 1rem;
        }}
        .spacing-slider {{
            width: 150px;
            height: 4px;
            border-radius: 2px;
            background: #1e293b;
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }}
        .spacing-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #10b981;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }}
        .spacing-slider::-moz-range-thumb {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #10b981;
            cursor: pointer;
            border: none;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }}
        .spacing-slider::-webkit-slider-thumb:hover {{
            background: #34d399;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
        }}
        .spacing-slider::-moz-range-thumb:hover {{
            background: #34d399;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
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
            background: rgba(10, 10, 10, 0.95);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5),
                        0 0 50px rgba(16, 185, 129, 0.3),
                        inset 0 0 50px rgba(139, 92, 246, 0.15);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(16, 185, 129, 0.4);
        }}
        /* Ensure SVG elements are visible */
        #mermaid-diagram svg {{
            filter: drop-shadow(0 0 1px rgba(52, 211, 153, 0.3));
        }}
        /* Node highlight animation */
        .node.highlighted rect,
        .node.highlighted polygon {{
            stroke: #8b5cf6 !important;
            stroke-width: 4px !important;
            filter: drop-shadow(0 0 20px rgba(139, 92, 246, 1));
            animation: pulse-highlight 1s ease-in-out;
        }}
        @keyframes pulse-highlight {{
            0%, 100% {{
                stroke-width: 4px;
            }}
            50% {{
                stroke-width: 6px;
            }}
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
        /* Enhanced edge/arrow visibility - Circuit board style */
        .edgePath path {{
            stroke: #000000 !important;
            stroke-width: 4px !important;
            stroke-linecap: square !important;
            filter: drop-shadow(0 0 2px rgba(16, 185, 129, 0.8));
            transition: all 0.2s ease;
        }}
        /* Subtle pulse effect */
        .edgePath {{
            animation: edge-pulse 4s ease-in-out infinite;
        }}
        @keyframes edge-pulse {{
            0%, 100% {{
                opacity: 0.9;
            }}
            50% {{
                opacity: 1;
            }}
        }}
        .edgePath:hover path {{
            stroke-width: 5px !important;
            filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.9));
        }}
        .edgePath marker path {{
            fill: #10b981 !important;
            filter: drop-shadow(0 0 2px rgba(16, 185, 129, 0.8));
        }}
        .edgePath:hover marker path {{
            fill: #8b5cf6 !important;
            filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.9));
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
                <button class="btn" onclick="toggleSidebar()">📁 Files</button>
                <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
                <span class="zoom-info">
                    <span>Zoom:</span>
                    <strong id="zoom-level">100%</strong>
                    <span style="margin-left: 1rem">💡 Scroll to zoom, drag to pan</span>
                </span>
                <span class="spacing-control">
                    <span>Spacing:</span>
                    <input type="range" class="spacing-slider" id="spacing-slider"
                           min="50" max="300" value="100" step="10"
                           oninput="updateSpacing(this.value)">
                    <strong id="spacing-value">100px</strong>
                </span>
            </div>
        </div>
        <div class="main-content">
            <div class="sidebar" id="sidebar">
                <h2>📁 File Explorer</h2>
                <input type="text" class="sidebar-search" id="sidebar-search" placeholder="Search files..." />
                <div id="file-tree"></div>
            </div>
            <div class="diagram-wrapper">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Rendering diagram...</p>
            </div>
            <div class="diagram-container" id="diagram-container">
                <div class="mermaid" id="mermaid-diagram" data-mermaid-code-b64="{mermaid_code_b64}">
                    <!-- Mermaid code will be loaded from base64 attribute by JavaScript to avoid HTML parsing issues -->
                </div>
            </div>
        </div>
        </div>
    </div>

    <script type="module">
        // Re-import mermaid for this script module (ES modules cache imports efficiently)
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

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

        function updateSpacing(value) {{
            const spacingValue = parseInt(value);
            document.getElementById('spacing-value').textContent = spacingValue + 'px';

            // Update mermaid configuration with new spacing
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'dark',
                themeVariables: {{
                    primaryColor: '#10b981',
                    primaryTextColor: '#10b981',
                    primaryBorderColor: '#10b981',
                    lineColor: '#10b981',
                    secondaryColor: '#8b5cf6',
                    tertiaryColor: '#ec4899',
                    background: '#0a0a0a',
                    mainBkg: '#0d1f1a',
                    secondBkg: '#1a1625',
                    tertiaryBkg: '#1f0a1a',
                    clusterBkg: 'rgba(16, 185, 129, 0.05)',
                    clusterBorder: '#10b981',
                    edgeLabelBackground: 'rgba(10, 10, 10, 0.8)',
                    nodeTextColor: '#10b981'
                }},
                flowchart: {{
                    useMaxWidth: false,
                    htmlLabels: true,
                    curve: 'linear',
                    nodeSpacing: spacingValue,
                    rankSpacing: spacingValue,
                    defaultRenderer: 'elk'
                }},
                elk: {{
                    mergeEdges: true,
                    nodePlacementStrategy: 'SIMPLE'
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
                logLevel: 'error',
                arrowMarkerAbsolute: true
            }});

            // Re-render the diagram with proper cleanup
            const diagramDiv = document.getElementById('mermaid-diagram');
            const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

            if (mermaidCodeB64) {{
                try {{
                    // Decode base64 mermaid code
                    const mermaidCode = atob(mermaidCodeB64);

                    // Clear old diagram completely (remove SVG and all children)
                    diagramDiv.innerHTML = '';

                    // Reset to mermaid class and insert raw mermaid code
                    diagramDiv.className = 'mermaid';
                    diagramDiv.removeAttribute('data-processed');
                    diagramDiv.textContent = mermaidCode;

                    // Reset zoom/pan for new diagram
                    scale = 1;
                    translateX = 0;
                    translateY = 0;
                    updateTransform();

                    // Re-render on next tick to ensure DOM is ready
                    setTimeout(async () => {{
                        try {{
                            await mermaid.run({{
                                querySelector: '.mermaid'
                            }});
                            // Reinitialize WebGL animations after render completes
                            setTimeout(createWebGLGlows, 500);
                        }} catch (err) {{
                            console.error('Failed to re-render diagram:', err);
                        }}
                    }}, 0);
                }} catch (error) {{
                    console.error('Failed to update spacing:', error);
                }}
            }}
        }}

        // Mouse wheel zoom - zoom towards cursor
        container.addEventListener('wheel', (e) => {{
            e.preventDefault();

            // Get mouse position relative to container
            const rect = container.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // With transform "translate(tx,ty) scale(s)", screen coords = (diagram + translate) * scale
            // So: diagram = screen / scale - translate
            // Calculate the point in diagram space that's currently under cursor
            const pointX = mouseX / scale - translateX;
            const pointY = mouseY / scale - translateY;

            // Calculate new scale
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.1, Math.min(5, scale * delta));

            // Calculate new translation to keep same diagram point under cursor
            // We want: mouseX = (pointX + new_translateX) * newScale
            // So: new_translateX = mouseX / newScale - pointX
            translateX = mouseX / newScale - pointX;
            translateY = mouseY / newScale - pointY;
            scale = newScale;

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

        // Sidebar functionality
        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
        }}

        // Parse mermaid content and build file tree
        function buildFileTree() {{
            try {{
                // Get mermaid content from base64 attribute to avoid template string issues
                const diagramDiv = document.getElementById('mermaid-diagram');
                const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

                console.log('Base64 attribute found:', !!mermaidCodeB64);
                console.log('Base64 length:', mermaidCodeB64 ? mermaidCodeB64.length : 0);

                if (!mermaidCodeB64) {{
                    console.error('No base64 data found on mermaid-diagram element');
                    document.getElementById('file-tree').innerHTML = '<div style="color:#f59e0b;">Error: No diagram data found</div>';
                    return;
                }}

                const mermaidContent = atob(mermaidCodeB64);
                console.log('Decoded mermaid content length:', mermaidContent.length);
                console.log('Sample content:', mermaidContent.substring(0, 500));

                const nodes = new Map(); // nodeId -> {{ name, file, line }}
                const fileStructure = {{}};

                // Extract nodes from mermaid content
                // Format: N0["function()<br/>🔧 class<br/>📄 file.py<br/>📍 L10-20"]
                // Use more flexible regex that doesn't rely on emoji matching
                const nodePattern = /N(\\d+)\\["([^(]+)\\(\\)<br\\/>[^<]*<br\\/>.*?\\s+([^<]+)<br\\/>[^<]*L(\\d+)-(\\d+)"\\]/g;
                let match;
                let matchCount = 0;

                while ((match = nodePattern.exec(mermaidContent)) !== null) {{
                    matchCount++;
                    if (matchCount <= 3) {{
                        console.log(`Match ${{matchCount}}:`, match[0]);
                    }}
                    const [, nodeId, funcName, fileName, lineStart, lineEnd] = match;
                const node = {{
                    id: 'N' + nodeId,
                    name: funcName.trim(),
                    file: fileName.trim(),
                    lineStart: parseInt(lineStart),
                    lineEnd: parseInt(lineEnd)
                }};
                nodes.set(node.id, node);

                // Build file structure
                if (!fileStructure[node.file]) {{
                    fileStructure[node.file] = [];
                }}
                fileStructure[node.file].push(node);
            }}

            console.log('buildFileTree: Found', matchCount, 'nodes');
            console.log('buildFileTree: Files found:', Object.keys(fileStructure).length);

            // Build HTML tree
            const treeHTML = [];
            const sortedFiles = Object.keys(fileStructure).sort();

            if (sortedFiles.length === 0) {{
                treeHTML.push('<div class="tree-item" style="color: #f59e0b;">No files found. Check console for regex match issues.</div>');
                console.warn('No files matched. Sample mermaid content:', mermaidContent.substring(0, 500));
            }} else {{
                for (const fileName of sortedFiles) {{
                    const funcs = fileStructure[fileName];
                    treeHTML.push(`
                        <div class="tree-item tree-file" onclick="highlightFile('${{fileName}}')">
                            <span class="icon">📄</span>
                            <span>${{fileName}}</span>
                        </div>
                        <div class="tree-children">
                    `);

                    for (const func of funcs) {{
                        treeHTML.push(`
                            <div class="tree-item tree-function" data-node-id="${{func.id}}" onclick="navigateToNode('${{func.id}}')">
                                <span class="icon">⚡</span>
                                <span>${{func.name}}() :${{func.lineStart}}</span>
                            </div>
                        `);
                    }}

                    treeHTML.push('</div>');
                }}
            }}

            document.getElementById('file-tree').innerHTML = treeHTML.join('');
            }} catch (error) {{
                console.error('Error in buildFileTree:', error);
                document.getElementById('file-tree').innerHTML = '<div style="color:#ef4444;">Error building file tree. Check console for details.</div>';
            }}
        }}

        // Navigate to a specific node in the diagram
        function navigateToNode(nodeId) {{
            // Find the node in the SVG
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) return;

            // Mermaid v10 with ELK renderer uses IDs like "flowchart-N0-123" instead of just "N0"
            // Try exact match first, then partial match
            let nodeElement = svg.querySelector(`#${{nodeId}}`);
            if (!nodeElement) {{
                // Try finding node by partial ID match (contains our nodeId)
                nodeElement = svg.querySelector(`g.node[id*="${{nodeId}}"]`);
            }}
            if (!nodeElement) {{
                console.warn('Node not found:', nodeId);
                console.log('Available node IDs:', Array.from(svg.querySelectorAll('g.node')).map(n => n.id));
                return;
            }}

            // Get the bounding box of the node in SVG coordinate space
            const nodeBBox = nodeElement.getBBox();
            const containerRect = container.getBoundingClientRect();

            // Calculate the center of the node in SVG coordinates
            const nodeCenterX = nodeBBox.x + nodeBBox.width / 2;
            const nodeCenterY = nodeBBox.y + nodeBBox.height / 2;

            // Set scale to 1.5 for better visibility
            scale = 1.5;

            // Center the node in the viewport
            // With transform "translate(tx,ty) scale(s)": screen = (svg + translate) * scale
            // We want: viewportCenter = (nodeCenter + translate) * scale
            // So: translate = viewportCenter / scale - nodeCenter
            const viewportCenterX = containerRect.width / 2;
            const viewportCenterY = containerRect.height / 2;

            translateX = viewportCenterX / scale - nodeCenterX;
            translateY = viewportCenterY / scale - nodeCenterY;

            updateTransform();

            // Highlight the node temporarily
            nodeElement.classList.add('highlighted');
            setTimeout(() => nodeElement.classList.remove('highlighted'), 2000);

            // Update active state in sidebar
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
            const sidebarItem = document.querySelector(`[data-node-id="${{nodeId}}"]`);
            if (sidebarItem) sidebarItem.classList.add('active');
        }}

        function highlightFile(fileName) {{
            // Highlight all nodes from this file
            const items = document.querySelectorAll(`[data-node-id]`);
            const svg = document.querySelector('#mermaid-diagram svg');

            items.forEach(item => {{
                const nodeId = item.getAttribute('data-node-id');
                // Try exact match first, then partial match
                let nodeElement = svg.querySelector(`#${{nodeId}}`);
                if (!nodeElement) {{
                    nodeElement = svg.querySelector(`g.node[id*="${{nodeId}}"]`);
                }}
                if (nodeElement && item.textContent.includes(fileName)) {{
                    nodeElement.classList.add('highlighted');
                    setTimeout(() => nodeElement.classList.remove('highlighted'), 2000);
                }}
            }});
        }}

        // Search functionality
        document.getElementById('sidebar-search').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();
            const treeItems = document.querySelectorAll('.tree-item');

            treeItems.forEach(item => {{
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    item.style.display = 'flex';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }});

        // Enhanced pulse effects with fading trails
        function createPulseEffects() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) return;

            // Create a defs section for gradients
            let defs = svg.querySelector('defs');
            if (!defs) {{
                defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                svg.insertBefore(defs, svg.firstChild);
            }}

            // Add larger radial gradient for pulse
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
            gradient.setAttribute('id', 'pulse-gradient');
            gradient.innerHTML = `
                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                <stop offset="50%" style="stop-color:#10b981;stop-opacity:0.6" />
                <stop offset="100%" style="stop-color:#10b981;stop-opacity:0" />
            `;
            defs.appendChild(gradient);

            // Only animate selected edges for performance
            const edgePaths = svg.querySelectorAll('.edgePath path');
            const maxPulses = Math.min(10, Math.floor(edgePaths.length / 5));

            for (let i = 0; i < maxPulses; i++) {{
                const index = i * Math.floor(edgePaths.length / maxPulses);
                const path = edgePaths[index];
                if (!path) continue;

                const pathLength = path.getTotalLength();
                const trailLength = 8; // Number of trail segments
                const trail = [];

                // Create trail segments
                for (let j = 0; j < trailLength; j++) {{
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    const opacity = 1 - (j / trailLength); // Fade out progressively
                    const radius = 6 - (j * 0.5); // Get smaller progressively

                    circle.setAttribute('r', radius);
                    circle.setAttribute('fill', 'url(#pulse-gradient)');
                    circle.setAttribute('opacity', opacity);
                    circle.style.filter = 'blur(1px)';

                    path.parentNode.appendChild(circle);
                    trail.push(circle);
                }}

                let distance = (i * 150) % pathLength;
                let lastTime = performance.now();

                function animatePulse(currentTime) {{
                    const deltaTime = currentTime - lastTime;

                    // 60fps cap
                    if (deltaTime < 16) {{
                        requestAnimationFrame(animatePulse);
                        return;
                    }}

                    lastTime = currentTime;
                    distance += 3; // Moderate speed

                    if (distance > pathLength) {{
                        distance = 0;
                    }}

                    // Update each trail segment
                    for (let j = 0; j < trailLength; j++) {{
                        const segmentDistance = distance - (j * 15); // Space segments out
                        let actualDistance = segmentDistance;

                        if (actualDistance < 0) {{
                            actualDistance = pathLength + actualDistance;
                        }}

                        const point = path.getPointAtLength(actualDistance % pathLength);
                        trail[j].setAttribute('cx', point.x);
                        trail[j].setAttribute('cy', point.y);
                    }}

                    requestAnimationFrame(animatePulse);
                }}

                requestAnimationFrame(animatePulse);
            }}
        }}

        // WebGL-accelerated glow particles for high-performance rendering
        function createWebGLGlows() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) {{
                console.warn('SVG not found, retrying WebGL initialization...');
                setTimeout(createWebGLGlows, 200);
                return;
            }}

            // Wait for paths to be fully rendered - check multiple times
            const edgePathCount = svg.querySelectorAll('.edgePath path').length;

            // Store last count to detect when rendering stabilizes
            if (!createWebGLGlows.lastPathCount) {{
                createWebGLGlows.lastPathCount = 0;
                createWebGLGlows.retryCount = 0;
            }}

            createWebGLGlows.retryCount++;

            // Wait longer if paths are still being added
            // Need to see same count at least 3 times before considering it stable
            if (!createWebGLGlows.stableCount) createWebGLGlows.stableCount = 0;

            if (edgePathCount !== createWebGLGlows.lastPathCount) {{
                console.log('WebGL: Found', edgePathCount, 'paths (was', createWebGLGlows.lastPathCount, '), waiting for rendering to stabilize...');
                createWebGLGlows.lastPathCount = edgePathCount;
                createWebGLGlows.stableCount = 0; // Reset stability counter
                setTimeout(createWebGLGlows, 500);
                return;
            }} else {{
                createWebGLGlows.stableCount++;
                if (createWebGLGlows.stableCount < 3 && createWebGLGlows.retryCount < 30) {{
                    console.log('WebGL: Path count stable at', edgePathCount, '(check', createWebGLGlows.stableCount, 'of 3)');
                    setTimeout(createWebGLGlows, 500);
                    return;
                }}
            }}

            console.log('WebGL: Initializing with', edgePathCount, 'edge paths after', createWebGLGlows.retryCount, 'checks');

            // Create canvas overlay - position it relative to SVG, not container
            const canvas = document.createElement('canvas');
            canvas.style.position = 'absolute';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.pointerEvents = 'none';
            canvas.style.zIndex = '100';  // Higher z-index to ensure visibility

            // Append canvas as sibling to SVG inside mermaid-diagram div
            // This way canvas and SVG are both transformed together
            const mermaidDiagram = document.getElementById('mermaid-diagram');
            mermaidDiagram.appendChild(canvas);
            console.log('WebGL canvas created');

            // Setup WebGL context
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) {{
                console.warn('WebGL not supported, falling back to SVG animations');
                return;
            }}

            // Vertex shader - positions line segments
            const vertexShaderSource = `
                attribute vec2 a_position;
                attribute float a_texCoord;  // Position along line (0 to 1)
                uniform vec2 u_resolution;
                uniform mat3 u_transform;
                varying float v_texCoord;

                void main() {{
                    vec3 transformed = u_transform * vec3(a_position, 1.0);
                    vec2 clipSpace = (transformed.xy / u_resolution) * 2.0 - 1.0;
                    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
                    v_texCoord = a_texCoord;
                }}
            `;

            // Fragment shader - creates flowing fire effect inside line channels
            const fragmentShaderSource = `
                precision mediump float;
                varying float v_texCoord;  // 0 to 1 along the line
                uniform float u_time;

                // Noise functions for fire turbulence
                float rand(vec2 n) {{
                    return fract(sin(dot(n, vec2(12.9898, 12.1414))) * 83758.5453);
                }}

                float noise(vec2 n) {{
                    const vec2 d = vec2(0.0, 1.0);
                    vec2 b = floor(n);
                    vec2 f = smoothstep(vec2(0.0), vec2(1.0), fract(n));
                    return mix(mix(rand(b), rand(b + d.yx), f.x),
                              mix(rand(b + d.xy), rand(b + d.yy), f.x), f.y);
                }}

                float fire(vec2 n) {{
                    return noise(n) + noise(n * 2.1) * 0.6 + noise(n * 5.4) * 0.42;
                }}

                // Flowing fire shader adapted for line channels
                float shade(vec2 uv, float t) {{
                    uv.x += uv.y < 0.5 ? 23.0 + t * 0.035 : -11.0 + t * 0.03;
                    uv.y = abs(uv.y - 0.5);
                    uv.x *= 35.0;

                    float q = fire(uv - t * 0.013) / 2.0;
                    vec2 r = vec2(fire(uv + q / 2.0 + t - uv.x - uv.y), fire(uv + q - t));

                    return pow((r.y + r.y) * max(0.0, uv.y) + 0.1, 4.0);
                }}

                // Green fire color ramp (adapted from reference shader)
                vec3 ramp(float t) {{
                    // Green channel fire: bright white -> cyan -> emerald -> dark green
                    if (t <= 0.5) {{
                        return vec3(1.0 - t * 1.4, 1.0, 1.05) / t;
                    }} else {{
                        return vec3(0.3 * (1.0 - t) * 2.0, 1.0, 1.05) / t;
                    }}
                }}

                vec3 color(float grad) {{
                    grad = sqrt(grad);
                    vec3 col = ramp(grad);
                    col /= (1.15 + max(vec3(0.0), col));
                    return col;
                }}

                void main() {{
                    // DEBUG: Simple bright green to test if lines render
                    gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);  // Solid bright green

                    // TODO: Re-enable fire shader once we confirm lines are visible
                    /*
                    // Create flowing UV coordinates along the line
                    vec2 uv = vec2(v_texCoord, 0.5);
                    float t = u_time;
                    uv.x -= t * 0.05;
                    float grad = shade(uv, t);
                    vec3 fireColor = color(grad);
                    float intensity = smoothstep(0.0, 0.2, grad) * smoothstep(1.0, 0.7, grad);
                    gl_FragColor = vec4(fireColor * intensity, intensity * 0.9);
                    */
                }}
            `;

            // Compile shaders
            function compileShader(source, type) {{
                const shader = gl.createShader(type);
                gl.shaderSource(shader, source);
                gl.compileShader(shader);
                if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {{
                    console.error('Shader compile error:', gl.getShaderInfoLog(shader));
                    return null;
                }}
                return shader;
            }}

            const vertexShader = compileShader(vertexShaderSource, gl.VERTEX_SHADER);
            const fragmentShader = compileShader(fragmentShaderSource, gl.FRAGMENT_SHADER);

            // Create program
            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);

            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {{
                console.error('Program link error:', gl.getProgramInfoLog(program));
                return;
            }}

            gl.useProgram(program);

            // Get attribute/uniform locations
            const positionLoc = gl.getAttribLocation(program, 'a_position');
            const texCoordLoc = gl.getAttribLocation(program, 'a_texCoord');
            const resolutionLoc = gl.getUniformLocation(program, 'u_resolution');
            const transformLoc = gl.getUniformLocation(program, 'u_transform');
            const timeLoc = gl.getUniformLocation(program, 'u_time');

            // Extract path data from SVG
            const edgePaths = svg.querySelectorAll('.edgePath path');
            const pathData = [];

            console.log('WebGL: Found', edgePaths.length, 'edge paths');

            edgePaths.forEach((path, idx) => {{
                // With WebGL we can animate ALL paths without performance issues
                const length = path.getTotalLength();
                const points = [];
                const step = Math.max(1, Math.floor(length / 50)); // Sample ~50 points

                // Get the transformation matrix from the path to SVG root
                const ctm = path.getCTM();

                for (let i = 0; i <= length; i += step) {{
                    const pt = path.getPointAtLength(i);
                    // Transform point using CTM to get absolute SVG coordinates
                    if (ctm) {{
                        const svgPt = svg.createSVGPoint();
                        svgPt.x = pt.x;
                        svgPt.y = pt.y;
                        const transformed = svgPt.matrixTransform(ctm);
                        points.push([transformed.x, transformed.y]);
                    }} else {{
                        points.push([pt.x, pt.y]);
                    }}
                }}

                // Debug first path
                if (idx === 0) {{
                    console.log('WebGL: First path CTM:', ctm);
                    console.log('WebGL: First path points (first 3):', points.slice(0, 3));
                }}

                pathData.push({{
                    points,
                    length,
                    progress: Math.random() // Start at random position
                }});
            }});

            console.log('WebGL: Created', pathData.length, 'animated paths');

            // Debug: Calculate bounding box of ALL path points
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            pathData.forEach(path => {{
                path.points.forEach(([x, y]) => {{
                    minX = Math.min(minX, x);
                    minY = Math.min(minY, y);
                    maxX = Math.max(maxX, x);
                    maxY = Math.max(maxY, y);
                }});
            }});
            console.log('WebGL: Path points bounding box:', {{
                min: [minX, minY],
                max: [maxX, maxY],
                width: maxX - minX,
                height: maxY - minY
            }});
            console.log('WebGL: SVG viewBox:', {{
                x: svg.viewBox.baseVal.x,
                y: svg.viewBox.baseVal.y,
                width: svg.viewBox.baseVal.width,
                height: svg.viewBox.baseVal.height
            }});

            // Build vertex data for rendering lines with fire texture
            // Each path becomes a LINE_STRIP with texture coordinates
            const lineVertices = [];
            const lineTexCoords = [];
            const lineSegments = []; // Track where each path starts/ends

            pathData.forEach(path => {{
                const startIdx = lineVertices.length / 2;

                path.points.forEach((point, idx) => {{
                    // Add vertex position
                    lineVertices.push(point[0], point[1]);

                    // Add texture coordinate (0-1 along path)
                    const texCoord = idx / (path.points.length - 1);
                    lineTexCoords.push(texCoord);
                }});

                const endIdx = lineVertices.length / 2;
                lineSegments.push({{ start: startIdx, count: endIdx - startIdx }});
            }});

            const positions = new Float32Array(lineVertices);
            const texCoords = new Float32Array(lineTexCoords);

            // Create buffers
            const positionBuffer = gl.createBuffer();
            const texCoordBuffer = gl.createBuffer();

            // Upload static geometry to GPU
            gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

            gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, texCoords, gl.STATIC_DRAW);

            // Resize canvas to match SVG dimensions (not CSS-transformed container)
            function resizeCanvas() {{
                // Use SVG's actual dimensions, not the CSS-transformed container size
                const viewBox = svg.viewBox.baseVal;
                const svgWidth = viewBox.width || svg.width.baseVal.value;
                const svgHeight = viewBox.height || svg.height.baseVal.value;

                // Set canvas to reasonable size based on SVG aspect ratio
                // Use fixed width and calculate height to maintain aspect ratio
                const targetWidth = 2000; // Fixed reference width
                const aspectRatio = svgHeight / svgWidth;
                canvas.width = targetWidth;
                canvas.height = Math.round(targetWidth * aspectRatio);

                gl.viewport(0, 0, canvas.width, canvas.height);
            }}
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            console.log('WebGL: Starting fire channel animation with', lineSegments.length, 'paths');
            console.log('WebGL: Total vertices:', positions.length / 2);

            // Set line width for visibility
            gl.lineWidth(3.0);

            let frameCount = 0;
            // Animation loop
            function animate() {{
                resizeCanvas();
                frameCount++;
                // Clear with transparent background
                gl.clearColor(0, 0, 0, 0);
                gl.clear(gl.COLOR_BUFFER_BIT);
                gl.enable(gl.BLEND);
                gl.blendFunc(gl.SRC_ALPHA, gl.ONE);  // Additive blending for fire glow

                // Bind vertex attributes (static geometry, set once per frame)
                gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
                gl.enableVertexAttribArray(positionLoc);
                gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);

                gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
                gl.enableVertexAttribArray(texCoordLoc);
                gl.vertexAttribPointer(texCoordLoc, 1, gl.FLOAT, false, 0, 0);

                // Set uniforms
                gl.uniform2f(resolutionLoc, canvas.width, canvas.height);
                gl.uniform1f(timeLoc, performance.now() * 0.001); // Time in seconds

                // Get SVG viewBox for proper coordinate transformation
                const viewBox = svg.viewBox.baseVal;
                const svgWidth = viewBox.width || svg.width.baseVal.value;
                const svgHeight = viewBox.height || svg.height.baseVal.value;
                const svgX = viewBox.x || 0;  // ViewBox X offset
                const svgY = viewBox.y || 0;  // ViewBox Y offset

                // Calculate transform from SVG coordinates to canvas pixels
                // Only convert coordinate systems - CSS transform handles pan/zoom
                const scaleX = canvas.width / svgWidth;
                const scaleY = canvas.height / svgHeight;

                // Transform matrix: translate by viewBox offset, then scale
                // (CSS transform on canvas element handles pan/zoom to avoid double transformation)
                const transform = [
                    scaleX, 0, 0,
                    0, scaleY, 0,
                    -svgX * scaleX, -svgY * scaleY, 1
                ];
                gl.uniformMatrix3fv(transformLoc, false, transform);

                // Debug logging on first frame
                if (frameCount === 1) {{
                    console.log('WebGL: First frame rendering fire channels');
                    console.log('WebGL: Canvas size:', canvas.width, 'x', canvas.height);
                    console.log('WebGL: SVG viewBox:', svgX, svgY, svgWidth, 'x', svgHeight);
                    console.log('WebGL: Transform scale:', scaleX, 'x', scaleY);
                    console.log('WebGL: Transform matrix:', transform);
                    console.log('WebGL: Rendering', lineSegments.length, 'fire channels with flowing green fire');

                    // Debug: sample an SVG path point and show expected vs actual
                    const testPath = edgePaths[0];
                    const testPt = testPath.getPointAtLength(0);
                    console.log('WebGL: SVG path start (raw):', testPt.x, testPt.y);
                    const testCTM = testPath.getCTM();
                    if (testCTM) {{
                        const svgPt = svg.createSVGPoint();
                        svgPt.x = testPt.x;
                        svgPt.y = testPt.y;
                        const transformed = svgPt.matrixTransform(testCTM);
                        console.log('WebGL: SVG path start (CTM transformed):', transformed.x, transformed.y);
                    }}

                    // Get actual screen position of path
                    const bbox = testPath.getBBox();
                    console.log('WebGL: SVG path BBox:', bbox.x, bbox.y, bbox.width, 'x', bbox.height);
                }}

                // Draw each path as a LINE_STRIP with flowing fire texture
                lineSegments.forEach(segment => {{
                    gl.drawArrays(gl.LINE_STRIP, segment.start, segment.count);
                }});

                // Check for WebGL errors on first frame
                if (frameCount === 1) {{
                    const err = gl.getError();
                    if (err !== gl.NO_ERROR) {{
                        console.error('WebGL error after first draw:', err);
                    }} else {{
                        console.log('WebGL: First draw completed without errors');
                    }}
                }}

                requestAnimationFrame(animate);
            }}

            animate();
        }}

        // Auto-fit diagram to viewport on load
        function autoFitDiagram() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (!svg) {{
                setTimeout(autoFitDiagram, 100);
                return;
            }}

            const svgBBox = svg.getBBox();
            const containerRect = container.getBoundingClientRect();

            // Add padding to container size
            const paddingPercent = 0.05; // 5% padding
            const availableWidth = containerRect.width * (1 - paddingPercent * 2);
            const availableHeight = containerRect.height * (1 - paddingPercent * 2);

            // Calculate scale to fit entire diagram
            const scaleX = availableWidth / svgBBox.width;
            const scaleY = availableHeight / svgBBox.height;
            scale = Math.min(scaleX, scaleY, 1);

            // Center the diagram accounting for bounding box offset
            const scaledWidth = svgBBox.width * scale;
            const scaledHeight = svgBBox.height * scale;

            // Calculate centering: center of viewport - center of scaled content
            translateX = (containerRect.width - scaledWidth) / 2 / scale - svgBBox.x;
            translateY = (containerRect.height - scaledHeight) / 2 / scale - svgBBox.y;

            updateTransform();
        }}

        // Load mermaid content from base64 to avoid HTML parsing issues
        function loadMermaidContent() {{
            const diagramDiv = document.getElementById('mermaid-diagram');
            const mermaidCodeB64 = diagramDiv.getAttribute('data-mermaid-code-b64');

            if (!mermaidCodeB64) {{
                console.error('No base64 mermaid content found');
                return false;
            }}

            try {{
                // Decode base64 to bytes, then UTF-8 decode for proper emoji support
                const base64Bytes = atob(mermaidCodeB64);
                // Convert binary string to UTF-8 using TextDecoder
                const bytes = new Uint8Array(base64Bytes.length);
                for (let i = 0; i < base64Bytes.length; i++) {{
                    bytes[i] = base64Bytes.charCodeAt(i);
                }}
                const mermaidCode = new TextDecoder('utf-8').decode(bytes);
                diagramDiv.textContent = mermaidCode;
                console.log('Loaded mermaid content:', mermaidCode.length, 'characters');
                return true;
            }} catch (error) {{
                console.error('Failed to decode mermaid content:', error);
                return false;
            }}
        }}

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', async () => {{
            console.log('DOM ready, initializing diagram...');

            // Load content and render diagram
            if (loadMermaidContent()) {{
                try {{
                    // Use mermaid.run() for v10 API - it finds and renders all .mermaid elements
                    await mermaid.run({{
                        querySelector: '.mermaid'
                    }});
                    console.log('Mermaid diagram rendered successfully');

                    // Build tree and effects after diagram is rendered
                    setTimeout(() => {{
                        buildFileTree();
                        createWebGLGlows(); // GPU-accelerated particle effects
                        // Don't auto-fit - it causes off-screen positioning
                        // User can press Reset (0 key) to fit if needed
                    }}, 500);
                }} catch (error) {{
                    console.error('Failed to render mermaid diagram:', error);
                    // Try fallback rendering
                    setTimeout(() => {{
                        buildFileTree();
                        createWebGLGlows(); // GPU-accelerated fallback
                    }}, 1000);
                }}
            }} else {{
                console.error('Failed to load mermaid content');
            }}
        }});

        // Global function to refresh WebGL particles (callable from console or keyboard)
        window.refreshWebGLParticles = function() {{
            console.log('Refreshing WebGL particles...');
            // Remove existing canvas
            const existingCanvas = document.querySelector('#mermaid-diagram canvas');
            if (existingCanvas) {{
                existingCanvas.remove();
            }}
            // Reset retry counters
            createWebGLGlows.lastPathCount = 0;
            createWebGLGlows.retryCount = 0;
            createWebGLGlows.stableCount = 0;
            // Reinitialize
            createWebGLGlows();
        }};

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === '+' || e.key === '=') zoomIn();
            if (e.key === '-' || e.key === '_') zoomOut();
            if (e.key === '0') resetZoom();
            if (e.key === 'f' || e.key === 'F') toggleFullscreen();
            if (e.key === 'r' || e.key === 'R') window.refreshWebGLParticles(); // R to refresh particles
            if (e.key === 'b' || e.key === 'B') toggleSidebar();
        }});

        // Make functions globally accessible for inline onclick handlers
        window.navigateToNode = navigateToNode;
        window.highlightFile = highlightFile;
        window.toggleSidebar = toggleSidebar;
        window.toggleFullscreen = toggleFullscreen;
        window.zoomIn = zoomIn;
        window.zoomOut = zoomOut;
        window.resetZoom = resetZoom;
        window.updateSpacing = updateSpacing;
    </script>
</body>
</html>'''

    try:
        import html
        import base64
        # Encode mermaid code in base64 to avoid HTML escaping issues
        mermaid_code_b64 = base64.b64encode(mermaid_content.encode('utf-8')).decode('ascii')
        html_content = html_template.format(
            title=title,
            mermaid_code_b64=mermaid_code_b64
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
        "%%{init: {'flowchart': {'curve': 'linear', 'defaultRenderer': 'elk', 'nodeSpacing': 100, 'rankSpacing': 100}, 'theme': 'dark'}}%%",
        "graph TD"
    ]

    # Find entry points (functions not called by others)
    called_functions = set()
    for calls in function_calls.values():
        called_functions.update(calls)

    entry_points = [func for func in function_calls.keys()
                   if func not in called_functions][:15]  # Even more entry points

    # Group functions by folder/directory
    functions_by_folder = defaultdict(lambda: defaultdict(list))  # folder -> class -> [functions]
    processed = set()
    node_count = 0
    node_ids = {}  # Map func_name to node_id

    def collect_functions(func_name, depth=0, max_depth=8):
        nonlocal node_count

        if depth > max_depth or func_name in processed or node_count >= 50:
            return

        processed.add(func_name)
        symbol = all_symbols.get(func_name, {})
        scope = symbol.get('scope', '')

        # Get folder path from file path
        file_path = symbol.get('path', '')
        if file_path:
            folder = str(Path(file_path).parent)
            # Normalize path separators and handle current directory
            folder = folder.replace('\\', '/').replace('.', 'root')
        else:
            folder = 'root'

        # Group by folder, then by class or module
        if scope:
            functions_by_folder[folder][scope].append(func_name)
        else:
            # Use file as grouping if no class
            file_name = Path(symbol.get('path', 'global')).stem
            functions_by_folder[folder][f"module_{file_name}"].append(func_name)

        node_count += 1

        # Recursively collect called functions
        calls = function_calls.get(func_name, [])
        for called_func in calls[:3]:  # Limit calls per function for clarity
            if called_func not in processed:
                collect_functions(called_func, depth + 1, max_depth)

    # Collect all functions starting from entry points
    for entry in entry_points:
        if node_count >= 50:
            break
        collect_functions(entry, depth=0, max_depth=8)

    # Transform folder->class into folder->file_component->class for grouping related files
    def group_by_file_components(functions_by_folder, all_symbols):
        """Group related files (e.g., Component.razor + Component.razor.cs) together."""
        file_components = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # Result: file_components[folder][base_file_name][class_name] = [functions]

        for folder, classes_dict in functions_by_folder.items():
            for class_name, funcs in classes_dict.items():
                for func_name in funcs:
                    symbol = all_symbols.get(func_name, {})
                    file_path = symbol.get('path', '')

                    if file_path:
                        path_obj = Path(file_path)
                        base_name = path_obj.stem

                        # Handle compound extensions: Component.razor.cs -> Component
                        if base_name.endswith('.razor'):
                            base_name = base_name[:-6]

                        # Group by base file name
                        file_components[folder][base_name][class_name].append(func_name)
                    else:
                        # Fallback for functions without file path
                        file_components[folder]['unknown'][class_name].append(func_name)

        return file_components

    file_components = group_by_file_components(functions_by_folder, all_symbols)

    # Generate subgraphs for each folder with nested file components
    subgraph_count = 0
    file_sg_count = 0

    for folder, files_dict in sorted(file_components.items())[:20]:  # Limit folders
        if not files_dict:
            continue

        folder_sg_id = f"SG{subgraph_count}"
        subgraph_count += 1

        # Clean folder name for display
        display_folder = folder.replace('root', '📁 .').replace('/', ' / ')
        if not display_folder.startswith('📁'):
            display_folder = f"📁 {display_folder}"

        # Start folder subgraph
        lines.append(f"    subgraph {folder_sg_id}[\"{display_folder}\"]")

        # Iterate through file components in this folder
        for base_file_name, classes_dict in sorted(files_dict.items()):
            if not classes_dict:
                continue

            # Create nested file component subgraph
            file_sg_id = f"FSG{file_sg_count}"
            file_sg_count += 1

            lines.append(f"        subgraph {file_sg_id}[\"📄 {base_file_name}\"]")

            # Add all functions from all classes in this file component
            for class_name, funcs in sorted(classes_dict.items()):
                if not funcs:
                    continue

                for func_name in funcs[:15]:  # Limit functions
                    symbol = all_symbols.get(func_name, {})
                    node_id = f"N{len(node_ids)}"
                    node_ids[func_name] = node_id

                    display_func = func_name.split('.')[-1]
                    file_name = Path(symbol.get('path', '')).name
                    line_start = symbol.get('line', 0)
                    line_end = symbol.get('end', line_start)

                    # Show class/module in node if available
                    class_display = class_name.replace('module_', '')

                    # Create node with class, file, and line numbers (file also shown in subgraph title for context)
                    lines.append(f"            {node_id}[\"{display_func}()<br/>🔧 {class_display}<br/>📄 {file_name}<br/>📍 L{line_start}-{line_end}\"]")

            lines.append("        end")  # Close file component subgraph

        lines.append("    end")  # Close folder subgraph
        lines.append("")

    # Define colors for subgraphs and edges (using very dark shades for subtle backgrounds)
    colors = [
        ("fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px", "#10b981", "emerald"),  # Very dark emerald
        ("fill:#1a1625,stroke:#8b5cf6,color:#8b5cf6,stroke-width:2px", "#8b5cf6", "purple"),   # Very dark purple
        ("fill:#0c1c20,stroke:#06b6d4,color:#06b6d4,stroke-width:2px", "#06b6d4", "cyan"),     # Very dark cyan
        ("fill:#211a0d,stroke:#f59e0b,color:#f59e0b,stroke-width:2px", "#f59e0b", "amber"),    # Very dark amber
        ("fill:#1f0d18,stroke:#ec4899,color:#ec4899,stroke-width:2px", "#ec4899", "pink"),     # Very dark pink
    ]

    # Build node-to-color mapping based on which folder they belong to
    node_to_color = {}
    for i, (folder, files_dict) in enumerate(sorted(file_components.items())[:20]):
        _, edge_color, _ = colors[i % len(colors)]
        for base_file_name, classes_dict in files_dict.items():
            for class_name, funcs in classes_dict.items():
                for func in funcs:
                    full_name = f"{class_name.replace('module_', '')}.{func}" if class_name.startswith('module_') else func
                    # Try both full name and short name
                    for potential_name in [full_name, func]:
                        if potential_name in node_ids:
                            node_to_color[node_ids[potential_name]] = edge_color

    # Add connections with color-coded edges matching destination
    lines.append("    %% Connections")
    link_count = 0
    link_styles = []

    for func_name, calls in function_calls.items():
        if func_name not in node_ids:
            continue

        from_id = node_ids[func_name]
        for called_func in calls[:3]:  # Limit to 3 calls per function for clarity
            if called_func in node_ids:
                to_id = node_ids[called_func]
                edge_color = node_to_color.get(to_id, '#10b981')  # Default to green

                lines.append(f"    {from_id} --> {to_id}")
                link_styles.append(f"    linkStyle {link_count} stroke:{edge_color},stroke-width:3px")
                link_count += 1

    lines.append("")

    # Apply link styles
    for style in link_styles:
        lines.append(style)

    lines.append("")

    # Apply green/black/purple theme styling
    lines.append("    %% Styling - Green/Black/Purple Theme")

    # Style subgraphs with different faded colors
    for i in range(subgraph_count):
        color_style, _, _ = colors[i % len(colors)]
        lines.append(f"    style SG{i} {color_style}")

    # Style nodes with subtle backgrounds
    for func_name, node_id in node_ids.items():
        if func_name in entry_points:
            # Entry points - subtle purple with glow border
            lines.append(f"    style {node_id} fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7")
        else:
            # Regular nodes - very dark with green border
            lines.append(f"    style {node_id} fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Legend",
        "- 🟣 **Purple nodes**: Entry points (functions not called by others)",
        "- 🟢 **Green-bordered nodes**: Called functions",
        "- **Folder Subgraphs**: Group by directory",
        "- **File Subgraphs**: Group related files (e.g., Component.razor + Component.razor.cs)",
        "- **Line numbers**: Show start-end lines in source file",
        "",
        f"## Statistics",
        f"- **Total Functions Mapped**: {len(processed)}",
        f"- **Folders**: {len(file_components)}",
        f"- **File Components**: {sum(len(files) for files in file_components.values())}",
        f"- **Classes/Modules**: {sum(sum(len(classes) for classes in files.values()) for files in file_components.values())}",
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

    # Check if old tags file exists and warn if too large
    if tags_file.exists():
        file_size_mb = tags_file.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:  # Warn if > 50MB
            warning_msg = f"[WARNING] Existing tags file is {file_size_mb:.1f}MB - this may indicate too many files are being scanned"
            if use_color:
                print(colorize(warning_msg, TextColor.YELLOW))
                print(colorize("  Consider adding more exclusions or using --python/--csharp filters", TextColor.YELLOW))
            else:
                print(warning_msg)
                print("  Consider adding more exclusions or using --python/--csharp filters")
            print()

    # Delete old tags file to prevent accumulation
    if tags_file.exists():
        try:
            tags_file.unlink()
            if use_color:
                print(colorize("[INFO] Deleted old tags file", TextColor.BRIGHT_BLUE))
            else:
                print("[INFO] Deleted old tags file")
        except Exception as e:
            if use_color:
                print(colorize(f"[WARNING] Could not delete old tags file: {e}", TextColor.YELLOW))
            else:
                print(f"[WARNING] Could not delete old tags file: {e}")
        print()

    # Generate ctags (in-memory for performance)
    if use_color:
        print(colorize("[PROGRESS] Generating tags...", TextColor.BRIGHT_BLUE))
    else:
        print("[PROGRESS] Generating tags...")

    ignore_gitignore = getattr(args, 'ignore_gitignore', False)
    tags_json = generate_ctags(language, str(tags_file), ctags_exe, ignore_gitignore, in_memory=True)

    if not tags_json:
        error_msg = "[ERROR] Failed to generate ctags"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Optionally write to file for debugging/caching
    try:
        with open(tags_file, 'w', encoding='utf-8') as f:
            f.write(tags_json)
    except Exception:
        pass  # Non-critical if file write fails

    if use_color:
        print(colorize("[SUCCESS] Tags generated successfully", TextColor.GREEN))
    else:
        print("[SUCCESS] Tags generated successfully")

    # Parse and analyze tags (from memory)
    if use_color:
        print(colorize("[PROGRESS] Analyzing symbols...", TextColor.BRIGHT_BLUE))
    else:
        print("[PROGRESS] Analyzing symbols...")

    stats = parse_tags_file(tags_json, from_string=True)

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

    # Gitignore option
    parser.add_argument(
        '--ignore-gitignore',
        action='store_true',
        help='Scan files that would normally be excluded by .gitignore (e.g., bin/, obj/ for C# projects)'
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
