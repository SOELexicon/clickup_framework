"""Batch diagram generation command for ClickUp Framework CLI.

This command provides batch diagram generation capabilities using YAML
configuration files. It supports:
- Batch processing of multiple diagram types
- Configuration-driven generation
- Dry-run mode for previewing operations
- Watch mode for auto-regeneration
- Continue-on-error for robust pipelines
"""

import sys
import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from .map_helpers.pipeline_config import PipelineConfig
from .map_helpers.batch_generator import BatchGenerator


# Metadata for automatic help generation
COMMAND_METADATA = {
    "category": "🛠️  Utility Commands",
    "commands": [
        {
            "name": "batch-diagram",
            "args": "[--config FILE] [--init] [--dry-run] [--watch] [--stop-on-error]",
            "description": "Generate multiple diagrams from YAML pipeline configuration"
        },
    ]
}


class PipelineFileHandler(FileSystemEventHandler):
    """File system event handler for watch mode."""

    def __init__(self, config_file: str, batch_generator_factory, debounce_seconds: float = 2.0):
        """Initialize file handler.

        Args:
            config_file: Path to configuration file
            batch_generator_factory: Function to create BatchGenerator
            debounce_seconds: Minimum seconds between regenerations
        """
        super().__init__()
        self.config_file = Path(config_file)
        self.batch_generator_factory = batch_generator_factory
        self.debounce_seconds = debounce_seconds
        self.last_run = 0

    def on_modified(self, event):
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Check if it's a relevant file (Python, C#, or config file)
        file_path = Path(event.src_path)
        relevant_extensions = {'.py', '.cs', '.yaml', '.yml'}
        if file_path.suffix not in relevant_extensions:
            return

        # Debounce: ignore if too soon after last run
        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return

        self.last_run = current_time

        print(f"\n[WATCH] Detected change in {file_path.name}, regenerating...")
        print("=" * 80)

        try:
            # Reload config and regenerate
            config = PipelineConfig(str(self.config_file))
            generator = self.batch_generator_factory(config)
            generator.generate_all()
        except Exception as e:
            print(f"[ERROR] Regeneration failed: {e}", file=sys.stderr)


def batch_diagram_command(args):
    """Generate multiple diagrams from YAML pipeline configuration.

    Args:
        args: Command line arguments from argparse
    """
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Handle --init: create example configuration
    if args.init:
        output_file = args.config if args.config else '.diagram-pipeline.yaml'
        if use_color:
            print()
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print(colorize("Creating Example Pipeline Configuration", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print()
        else:
            print()
            print("=" * 80)
            print("Creating Example Pipeline Configuration")
            print("=" * 80)
            print()

        PipelineConfig.create_example_config(output_file)
        if use_color:
            print()
            print(colorize(f"Configuration created: {output_file}", TextColor.GREEN))
            print(colorize(f"Edit the file and run: cum batch-diagram --config {output_file}", TextColor.YELLOW))
        else:
            print()
            print(f"Configuration created: {output_file}")
            print(f"Edit the file and run: cum batch-diagram --config {output_file}")
        print()
        sys.exit(0)

    # Require configuration file
    config_file = args.config if args.config else '.diagram-pipeline.yaml'
    if not Path(config_file).exists():
        error_msg = f"Configuration file not found: {config_file}"
        if use_color:
            print(colorize(f"[ERROR] {error_msg}", TextColor.RED), file=sys.stderr)
            print(colorize("Create one with: cum batch-diagram --init", TextColor.YELLOW), file=sys.stderr)
        else:
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            print("Create one with: cum batch-diagram --init", file=sys.stderr)
        sys.exit(1)

    # Load and validate configuration
    try:
        config = PipelineConfig(config_file)
    except Exception as e:
        error_msg = f"Failed to load configuration: {e}"
        if use_color:
            print(colorize(f"[ERROR] {error_msg}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] {error_msg}", file=sys.stderr)
        sys.exit(1)

    # Determine error handling mode
    continue_on_error = not args.stop_on_error

    # Create batch generator
    def create_generator(cfg):
        return BatchGenerator(
            config=cfg,
            dry_run=args.dry_run,
            continue_on_error=continue_on_error,
            use_color=use_color
        )

    generator = create_generator(config)

    # Handle watch mode
    if args.watch:
        if args.dry_run:
            error_msg = "Cannot use --watch with --dry-run"
            if use_color:
                print(colorize(f"[ERROR] {error_msg}", TextColor.RED), file=sys.stderr)
            else:
                print(f"[ERROR] {error_msg}", file=sys.stderr)
            sys.exit(1)

        if use_color:
            print()
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print(colorize("Watch Mode Enabled", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print(colorize("Monitoring for file changes...", TextColor.YELLOW))
            print(colorize("Press Ctrl+C to stop", TextColor.YELLOW))
            print(colorize("=" * 80, TextColor.BRIGHT_CYAN))
            print()
        else:
            print()
            print("=" * 80)
            print("Watch Mode Enabled")
            print("=" * 80)
            print("Monitoring for file changes...")
            print("Press Ctrl+C to stop")
            print("=" * 80)
            print()

        # Initial generation
        success = generator.generate_all()

        # Set up file watcher
        event_handler = PipelineFileHandler(config_file, create_generator)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            if use_color:
                print()
                print(colorize("\n[INFO] Watch mode stopped", TextColor.YELLOW))
            else:
                print()
                print("\n[INFO] Watch mode stopped")

        observer.join()
        sys.exit(0 if success else 1)

    # Standard batch generation
    success = generator.generate_all()
    sys.exit(0 if success else 1)


def register_command(subparsers):
    """Register the batch-diagram command with the CLI parser.

    Args:
        subparsers: Argparse subparsers object
    """
    parser = subparsers.add_parser(
        'batch-diagram',
        help='Generate multiple diagrams from YAML pipeline configuration'
    )

    # Configuration file
    parser.add_argument(
        '--config',
        type=str,
        default='.diagram-pipeline.yaml',
        help='Path to pipeline configuration file (default: .diagram-pipeline.yaml)'
    )

    # Initialize configuration
    parser.add_argument(
        '--init',
        action='store_true',
        help='Create example pipeline configuration file'
    )

    # Dry run mode
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show planned operations without executing them'
    )

    # Watch mode
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Watch for file changes and auto-regenerate diagrams'
    )

    # Error handling
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop processing on first error (default: continue on error)'
    )

    parser.set_defaults(func=batch_diagram_command)
