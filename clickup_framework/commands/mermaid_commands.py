"""Mermaid diagram processing commands for ClickUp Framework CLI."""

import sys
import os
from pathlib import Path
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.parsers import ContentProcessor, ParserContext

# Metadata for automatic help generation
COMMAND_METADATA = {
    "category": "📊 Diagram Management",
    "commands": [
        {
            "name": "mermaid",
            "args": "<input_file> [--output OUTPUT] [options]",
            "description": "Process markdown file and generate mermaid diagram images"
        },
    ]
}


def mermaid_command(args):
    """Process markdown file and generate mermaid diagram images."""
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Validate input file
    input_file = Path(args.input_file)
    if not input_file.exists():
        if use_color:
            print(f"Error: Input file not found: {colorize(str(input_file), TextColor.RED)}", file=sys.stderr)
        else:
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Default: add _processed suffix before extension
        stem = input_file.stem
        suffix = "_processed"
        output_file = input_file.parent / f"{stem}{suffix}{input_file.suffix}"

    # Determine cache directory
    if args.cache_dir:
        cache_dir = Path(args.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Default: use .mermaid_cache in same directory as input file
        cache_dir = input_file.parent / ".mermaid_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

    # Read input file
    try:
        content = input_file.read_text(encoding='utf-8')
    except Exception as e:
        if use_color:
            print(f"Error reading input file: {colorize(str(e), TextColor.RED)}", file=sys.stderr)
        else:
            print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Display status
    if use_color:
        print(f"📄 Processing: {colorize(str(input_file), TextColor.BRIGHT_CYAN)}")
        print(f"💾 Output: {colorize(str(output_file), TextColor.BRIGHT_CYAN)}")
        print(f"📦 Cache: {colorize(str(cache_dir), TextColor.BRIGHT_CYAN)}")
    else:
        print(f"Processing: {input_file}")
        print(f"Output: {output_file}")
        print(f"Cache: {cache_dir}")

    # Create processor
    processor = ContentProcessor(
        context=ParserContext.COMMENT,
        cache_dir=str(cache_dir)
    )

    # Process options
    image_format = args.format.lower() if args.format else 'png'
    background_color = args.background if args.background else 'transparent'
    theme = args.theme.lower() if args.theme else 'dark'
    width = args.width if args.width else None
    height = args.height if args.height else None

    # Process the content
    try:
        result = processor.process(
            content,
            format_markdown=args.markdown,
            process_mermaid=True,
            convert_mermaid_to_images=True,
            embed_above=args.embed_above,
            image_format=image_format,
            theme=theme,
            background_color=background_color,
            width=width,
            height=height
        )

        # Display results
        mermaid_blocks = result.get('mermaid_blocks', [])
        generated_images = result.get('generated_images', [])

        if use_color:
            print(f"\n✅ Processing complete!")
            print(f"   Found {colorize(str(len(mermaid_blocks)), TextColor.BRIGHT_YELLOW)} mermaid diagram(s)")
            print(f"   Generated {colorize(str(len(generated_images)), TextColor.BRIGHT_YELLOW)} image(s)")
        else:
            print(f"\nProcessing complete!")
            print(f"   Found {len(mermaid_blocks)} mermaid diagram(s)")
            print(f"   Generated {len(generated_images)} image(s)")

        # Show generated images
        if generated_images:
            if use_color:
                print(f"\n📸 Generated images:")
            else:
                print(f"\nGenerated images:")
            for img_info in generated_images:
                img_path = img_info.get('path', 'N/A')
                img_hash = img_info.get('hash', 'N/A')[:16]
                if use_color:
                    print(f"   • {colorize(str(img_path), TextColor.BRIGHT_GREEN)} (hash: {img_hash}...)")
                else:
                    print(f"   • {img_path} (hash: {img_hash}...)")

        # Save processed output
        try:
            output_file.write_text(result['content'], encoding='utf-8')
            if use_color:
                print(f"\n💾 Saved processed markdown to: {colorize(str(output_file), TextColor.BRIGHT_CYAN)}")
            else:
                print(f"\nSaved processed markdown to: {output_file}")
        except Exception as e:
            if use_color:
                print(f"Warning: Failed to save output file: {colorize(str(e), TextColor.YELLOW)}", file=sys.stderr)
            else:
                print(f"Warning: Failed to save output file: {e}", file=sys.stderr)

        # Check for mermaid CLI availability and image generation
        from clickup_framework.utils.mermaid_cli import is_mermaid_available
        if not is_mermaid_available():
            if use_color:
                print(f"\n⚠️  Warning: Mermaid CLI (mmdc) not found. Images were not generated.")
                print(f"   Install with: {colorize('npm install -g @mermaid-js/mermaid-cli', TextColor.BRIGHT_YELLOW)}")
            else:
                print(f"\nWarning: Mermaid CLI (mmdc) not found. Images were not generated.")
                print(f"   Install with: npm install -g @mermaid-js/mermaid-cli")
        elif len(mermaid_blocks) > 0 and len(generated_images) == 0:
            # mmdc is available but no images were generated
            if use_color:
                print(f"\n⚠️  Warning: Mermaid CLI found but no images were generated.")
                print(f"   This may be due to:")
                print(f"   - Missing {colorize('PUPPETEER_EXECUTABLE_PATH', TextColor.BRIGHT_YELLOW)} environment variable")
                print(f"   - Chrome/Chromium not found in default location")
                print(f"   - Set {colorize('PUPPETEER_EXECUTABLE_PATH', TextColor.BRIGHT_YELLOW)} to your Chrome headless shell path")
            else:
                print(f"\nWarning: Mermaid CLI found but no images were generated.")
                print(f"   This may be due to:")
                print(f"   - Missing PUPPETEER_EXECUTABLE_PATH environment variable")
                print(f"   - Chrome/Chromium not found in default location")
                print(f"   - Set PUPPETEER_EXECUTABLE_PATH to your Chrome headless shell path")

        return 0

    except Exception as e:
        if use_color:
            print(f"\n❌ Error during processing: {colorize(str(e), TextColor.RED)}", file=sys.stderr)
        else:
            print(f"\nError during processing: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def register_command(subparsers):
    """Register mermaid command with argument parser."""
    mermaid_parser = subparsers.add_parser(
        'mermaid',
        help='Process markdown file and generate mermaid diagram images',
        description='Process markdown file containing mermaid diagrams and generate images from them.',
        epilog='''Examples:
  Process markdown file: cum mermaid document.md
  Specify output file: cum mermaid document.md --output processed.md
  Use PNG format: cum mermaid document.md --format png
  Use SVG format: cum mermaid document.md --format svg
  Custom theme: cum mermaid document.md --theme dark
  Custom background: cum mermaid document.md --background white
  Custom cache: cum mermaid document.md --cache-dir ./images
  Custom size: cum mermaid document.md --width 1920 --height 1080

Requirements:
  - Mermaid CLI (mmdc) must be installed: npm install -g @mermaid-js/mermaid-cli
  - Chrome/Chromium for rendering (mmdc uses Puppeteer)
  - Set PUPPETEER_EXECUTABLE_PATH if Chrome is not in default location'''
    )

    mermaid_parser.add_argument(
        'input_file',
        help='Input markdown file containing mermaid diagrams'
    )
    mermaid_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: <input>_processed.md)'
    )
    mermaid_parser.add_argument(
        '--format', '-f',
        choices=['png', 'svg', 'PNG', 'SVG'],
        default='png',
        help='Image format (default: png)'
    )
    mermaid_parser.add_argument(
        '--theme', '-t',
        choices=['default', 'dark', 'forest', 'neutral'],
        default='dark',
        help='Mermaid theme (default: dark)'
    )
    mermaid_parser.add_argument(
        '--background', '-b',
        default='transparent',
        help='Background color (default: transparent)'
    )
    mermaid_parser.add_argument(
        '--width', '-w',
        type=int,
        help='Image width in pixels (optional)'
    )
    mermaid_parser.add_argument(
        '--height', '-H',
        type=int,
        help='Image height in pixels (optional)'
    )
    mermaid_parser.add_argument(
        '--cache-dir',
        help='Directory for image cache (default: .mermaid_cache in input file directory)'
    )
    mermaid_parser.add_argument(
        '--no-markdown',
        dest='markdown',
        action='store_false',
        help='Disable markdown formatting (only process mermaid diagrams)'
    )
    mermaid_parser.add_argument(
        '--no-embed',
        dest='embed_above',
        action='store_false',
        help='Do not embed image references above mermaid code blocks'
    )
    mermaid_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose error messages'
    )

    mermaid_parser.set_defaults(func=mermaid_command)

