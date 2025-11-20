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

# Import map helper modules
from .map_helpers import (
    get_ctags_executable,
    check_ctags_available,
    install_ctags_locally,
    generate_ctags,
    parse_tags_file,
    generate_mermaid_flowchart,
    generate_mermaid_class,
    generate_mermaid_pie,
    generate_mermaid_mindmap,
    generate_mermaid_code_flow,
    generate_mermaid_sequence,
    check_mmdc_available,
    export_mermaid_to_image
)
from .map_helpers.templates import export_mermaid_to_html

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

    # Handle list themes request
    if args.list_themes:
        from .map_helpers.mermaid.styling.color_schemes import list_themes

        if use_color:
            print()
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print(colorize("Available Themes", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print()
        else:
            print()
            print("=" * 80)
            print("Available Themes")
            print("=" * 80)
            print()

        themes = list_themes()
        for theme_name, theme_info in themes.items():
            if use_color:
                print(colorize(f"{theme_name}:", TextColor.BRIGHT_GREEN, TextStyle.BOLD))
                print(f"  {theme_info['description']}")
                print(f"  Colors: {theme_info['colors']}")
                print(f"  Best for: {theme_info['best_for']}")
            else:
                print(f"{theme_name}:")
                print(f"  {theme_info['description']}")
                print(f"  Colors: {theme_info['colors']}")
                print(f"  Best for: {theme_info['best_for']}")
            print()

        sys.exit(0)

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
        # Validate theme before generating diagrams
        from .map_helpers.mermaid.styling import ThemeManager
        theme_manager = ThemeManager(args.theme)
        # Check if the requested theme was actually set (not fallen back to default)
        if theme_manager.current_theme != args.theme:
            error_msg = f"ERROR: Invalid theme '{args.theme}'. Use --list-themes to see available themes."
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)
            sys.exit(1)

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
            print(colorize(f"[PROGRESS] Generating {args.mer} mermaid diagram with {args.theme} theme...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Generating {args.mer} mermaid diagram with {args.theme} theme...")

        # Pass theme parameter to generators that support it
        if args.mer in ['flowchart', 'swim', 'flow']:
            generator(stats, str(mermaid_file), theme=args.theme)
        else:
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

    # Execution trace option
    parser.add_argument(
        '--trace',
        action='store_true',
        help='Enable dynamic execution tracing with hot path visualization (highlights frequently called functions)'
    )

    # Theme selection
    parser.add_argument(
        '--theme',
        type=str,
        default='dark',
        help='Color theme for diagram styling (default: dark). Use --list-themes to see available options'
    )

    # List available themes
    parser.add_argument(
        '--list-themes',
        action='store_true',
        help='List all available color themes and exit'
    )

    parser.set_defaults(func=map_command)
