"""Mermaid diagram processing commands for ClickUp Framework CLI."""

import sys
import os
from pathlib import Path
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.commands.base_command import BaseCommand
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


class MermaidCommand(BaseCommand):
    """Process markdown files and generate Mermaid diagram images."""

    def _get_context_manager(self):
        """Use module-local factories so tests can patch them if needed."""
        return get_context_manager()

    def _create_client(self):
        """Use module-local factories so tests can patch them if needed."""
        return ClickUpClient()

    def execute(self):
        """Execute the mermaid command."""
        input_file = Path(self.args.input_file)
        if not input_file.exists():
            if self.use_color:
                print(f"Error: Input file not found: {colorize(str(input_file), TextColor.RED)}", file=sys.stderr)
            else:
                print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        if self.args.output:
            output_file = Path(self.args.output)
        else:
            output_file = input_file.parent / f"{input_file.stem}_processed{input_file.suffix}"

        if self.args.cache_dir:
            cache_dir = Path(self.args.cache_dir)
        else:
            cache_dir = input_file.parent / ".mermaid_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            content = input_file.read_text(encoding='utf-8')
        except Exception as e:
            if self.use_color:
                print(f"Error reading input file: {colorize(str(e), TextColor.RED)}", file=sys.stderr)
            else:
                print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)

        if self.use_color:
            self.print(f"📄 Processing: {colorize(str(input_file), TextColor.BRIGHT_CYAN)}")
            self.print(f"💾 Output: {colorize(str(output_file), TextColor.BRIGHT_CYAN)}")
            self.print(f"📦 Cache: {colorize(str(cache_dir), TextColor.BRIGHT_CYAN)}")
        else:
            self.print(f"Processing: {input_file}")
            self.print(f"Output: {output_file}")
            self.print(f"Cache: {cache_dir}")

        processor = ContentProcessor(
            context=ParserContext.COMMENT,
            cache_dir=str(cache_dir)
        )

        image_format = self.args.format.lower() if self.args.format else 'png'
        background_color = self.args.background if self.args.background else 'transparent'
        theme = self.args.theme.lower() if self.args.theme else 'dark'
        width = self.args.width if self.args.width else None
        height = self.args.height if self.args.height else None

        try:
            result = processor.process(
                content,
                format_markdown=self.args.markdown,
                process_mermaid=True,
                convert_mermaid_to_images=True,
                embed_above=self.args.embed_above,
                image_format=image_format,
                theme=theme,
                background_color=background_color,
                width=width,
                height=height
            )

            mermaid_blocks = result.get('mermaid_blocks', [])
            generated_images = result.get('generated_images', [])

            if self.use_color:
                self.print("\n✅ Processing complete!")
                self.print(f"   Found {colorize(str(len(mermaid_blocks)), TextColor.BRIGHT_YELLOW)} mermaid diagram(s)")
                self.print(f"   Generated {colorize(str(len(generated_images)), TextColor.BRIGHT_YELLOW)} image(s)")
            else:
                self.print("\nProcessing complete!")
                self.print(f"   Found {len(mermaid_blocks)} mermaid diagram(s)")
                self.print(f"   Generated {len(generated_images)} image(s)")

            if generated_images:
                self.print("\n📸 Generated images:" if self.use_color else "\nGenerated images:")
                for img_info in generated_images:
                    img_path = img_info.get('path', 'N/A')
                    img_hash = img_info.get('hash', 'N/A')[:16]
                    if self.use_color:
                        self.print(f"   • {colorize(str(img_path), TextColor.BRIGHT_GREEN)} (hash: {img_hash}...)")
                    else:
                        self.print(f"   • {img_path} (hash: {img_hash}...)")

            try:
                output_file.write_text(result['content'], encoding='utf-8')
                if self.use_color:
                    self.print(f"\n💾 Saved processed markdown to: {colorize(str(output_file), TextColor.BRIGHT_CYAN)}")
                else:
                    self.print(f"\nSaved processed markdown to: {output_file}")
            except Exception as e:
                if self.use_color:
                    print(f"Warning: Failed to save output file: {colorize(str(e), TextColor.YELLOW)}", file=sys.stderr)
                else:
                    print(f"Warning: Failed to save output file: {e}", file=sys.stderr)

            from clickup_framework.utils.mermaid_cli import is_mermaid_available
            if not is_mermaid_available():
                if self.use_color:
                    self.print("\n⚠️  Warning: Mermaid CLI (mmdc) not found. Images were not generated.")
                    self.print(f"   Install with: {colorize('npm install -g @mermaid-js/mermaid-cli', TextColor.BRIGHT_YELLOW)}")
                else:
                    self.print("\nWarning: Mermaid CLI (mmdc) not found. Images were not generated.")
                    self.print("   Install with: npm install -g @mermaid-js/mermaid-cli")
            elif len(mermaid_blocks) > 0 and len(generated_images) == 0:
                if self.use_color:
                    self.print("\n⚠️  Warning: Mermaid CLI found but no images were generated.")
                    self.print("   This may be due to:")
                    self.print(f"   - Missing {colorize('PUPPETEER_EXECUTABLE_PATH', TextColor.BRIGHT_YELLOW)} environment variable")
                    self.print("   - Chrome/Chromium not found in default location")
                    self.print(f"   - Set {colorize('PUPPETEER_EXECUTABLE_PATH', TextColor.BRIGHT_YELLOW)} to your Chrome headless shell path")
                else:
                    self.print("\nWarning: Mermaid CLI found but no images were generated.")
                    self.print("   This may be due to:")
                    self.print("   - Missing PUPPETEER_EXECUTABLE_PATH environment variable")
                    self.print("   - Chrome/Chromium not found in default location")
                    self.print("   - Set PUPPETEER_EXECUTABLE_PATH to your Chrome headless shell path")

            return 0
        except Exception as e:
            if self.use_color:
                print(f"\n❌ Error during processing: {colorize(str(e), TextColor.RED)}", file=sys.stderr)
            else:
                print(f"\nError during processing: {e}", file=sys.stderr)
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def mermaid_command(args):
    """Command function wrapper for backward compatibility."""
    command = MermaidCommand(args, command_name='mermaid')
    return command.execute()


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
