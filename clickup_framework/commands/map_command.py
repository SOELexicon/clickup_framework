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
            "args": "[--python|--csharp|--all-langs] [--swim] [--output OUTPUT] [--install]",
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
    Parse ctags JSON output and collect statistics.

    Args:
        tags_file: Path to tags JSON file

    Returns:
        Dictionary with statistics and symbol data
    """
    stats = defaultdict(lambda: defaultdict(int))
    symbols_by_file = defaultdict(list)
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

                    stats[lang][kind] += 1
                    total += 1
                    files.add(path)

                    # Store symbol info for diagram generation
                    symbols_by_file[path].append({
                        'name': name,
                        'kind': kind,
                        'language': lang,
                        'line': line_num,
                        'scope': data.get('scope', ''),
                        'scopeKind': data.get('scopeKind', '')
                    })
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        return {
            'total_symbols': total,
            'files_analyzed': len(files),
            'by_language': dict(stats),
            'symbols_by_file': dict(symbols_by_file),
            'files': sorted(files)
        }
    except Exception as e:
        print(f"Error parsing tags file: {e}", file=sys.stderr)
        return {}


def generate_mermaid_swimlane(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid flowchart/swimlane diagram from code map statistics.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    # Build mermaid diagram
    lines = [
        "# Code Map Diagram",
        "",
        "```mermaid",
        "graph TB"
    ]

    # Add language nodes
    lang_nodes = {}
    for idx, lang in enumerate(sorted(by_language.keys())):
        node_id = f"L{idx}"
        lang_nodes[lang] = node_id
        lines.append(f"    {node_id}[{lang}]")

    lines.append("")

    # Add file nodes grouped by language
    file_count = 0
    file_nodes = {}
    for file_path, symbols in sorted(symbols_by_file.items()):
        if not symbols:
            continue

        # Get language from first symbol
        lang = symbols[0].get('language', 'Unknown')

        # Create file node
        file_id = f"F{file_count}"
        file_nodes[file_path] = file_id
        file_name = Path(file_path).name

        # Count symbols by kind
        kind_counts = defaultdict(int)
        for sym in symbols:
            kind_counts[sym.get('kind', 'other')] += 1

        # Create label with counts
        kind_summary = ", ".join(f"{k}:{v}" for k, v in sorted(kind_counts.items()))
        lines.append(f"    {file_id}[\"{file_name}<br/>{kind_summary}\"]")

        # Link to language
        if lang in lang_nodes:
            lines.append(f"    {lang_nodes[lang]} --> {file_id}")

        file_count += 1

        # Limit files to avoid overwhelming diagram
        if file_count >= 20:
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
    if args.swim:
        if args.output:
            mermaid_file = Path(args.output)
        else:
            mermaid_file = Path('docs/codemap/diagram.md')

        # Create parent directory if needed
        mermaid_file.parent.mkdir(parents=True, exist_ok=True)

        if use_color:
            print(colorize("[PROGRESS] Generating mermaid diagram...", TextColor.BRIGHT_BLUE))
        else:
            print("[PROGRESS] Generating mermaid diagram...")

        generate_mermaid_swimlane(stats, str(mermaid_file))

        if use_color:
            print(colorize(f"[SUCCESS] Mermaid diagram: {mermaid_file}", TextColor.GREEN))
        else:
            print(f"[SUCCESS] Mermaid diagram: {mermaid_file}")
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
    if args.swim:
        print(f"  - {mermaid_file} (Mermaid diagram)")
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
        '--swim',
        action='store_true',
        help='Generate mermaid swimlane diagram'
    )

    # Output file option
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for mermaid diagram (default: docs/codemap/diagram.md)'
    )

    parser.set_defaults(func=map_command)
