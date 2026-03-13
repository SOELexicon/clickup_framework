"""Batch diagram generator for pipeline processing.

This module handles batch generation of multiple diagrams from a pipeline configuration.
It manages the execution flow, error handling, and reporting for batch operations.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .pipeline_config import PipelineConfig
from .ctags_utils import generate_ctags, parse_tags_file, get_ctags_executable
from .mermaid.generators import (
    FlowchartGenerator,
    ClassDiagramGenerator,
    PieChartGenerator,
    MindmapGenerator,
    SequenceGenerator,
    CodeFlowGenerator
)


class GenerationResult:
    """Result of a single diagram generation."""

    def __init__(self, name: str, success: bool, output_file: Optional[str] = None,
                 error: Optional[str] = None, duration: float = 0.0):
        """Initialize generation result.

        Args:
            name: Generator name
            success: Whether generation succeeded
            output_file: Path to output file if successful
            error: Error message if failed
            duration: Generation time in seconds
        """
        self.name = name
        self.success = success
        self.output_file = output_file
        self.error = error
        self.duration = duration


class BatchGenerator:
    """Handles batch generation of diagrams from pipeline configuration."""

    # Map diagram types to generator classes
    GENERATOR_MAP = {
        'flowchart': FlowchartGenerator,
        'swim': FlowchartGenerator,  # Alias
        'class': ClassDiagramGenerator,
        'pie': PieChartGenerator,
        'mindmap': MindmapGenerator,
        'sequence': SequenceGenerator,
        'flow': CodeFlowGenerator,
    }

    def __init__(self, config: PipelineConfig, dry_run: bool = False,
                 continue_on_error: bool = True, use_color: bool = False):
        """Initialize batch generator.

        Args:
            config: Pipeline configuration
            dry_run: If True, show planned operations without executing
            continue_on_error: If True, continue processing after errors
            use_color: Whether to use colored console output
        """
        self.config = config
        self.dry_run = dry_run
        self.continue_on_error = continue_on_error
        self.use_color = use_color
        self.results: List[GenerationResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def generate_all(self) -> bool:
        """Generate all diagrams from configuration.

        Returns:
            True if all generations succeeded, False otherwise
        """
        self.start_time = time.time()
        generators = self.config.get_generators()

        if self.dry_run:
            self._print_dry_run_plan(generators)
            return True

        self._print_header(len(generators))

        # Create output directory
        output_dir = self.config.get_output_dir()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._print_error(f"Failed to create output directory {output_dir}: {e}")
            return False

        # Process each generator
        for idx, generator_config in enumerate(generators, 1):
            result = self._generate_diagram(generator_config, idx, len(generators))
            self.results.append(result)

            if not result.success and not self.continue_on_error:
                self._print_error(f"Stopping due to error in generator '{result.name}'")
                break

        self.end_time = time.time()
        return self._print_summary()

    def _generate_diagram(self, generator_config: Dict, index: int, total: int) -> GenerationResult:
        """Generate a single diagram.

        Args:
            generator_config: Generator configuration dictionary
            index: Current generator index (1-based)
            total: Total number of generators

        Returns:
            GenerationResult with generation outcome
        """
        name = generator_config['name']
        diagram_type = generator_config['type']
        source = generator_config['source']
        output = generator_config['output']
        options = self.config.get_generator_options(generator_config)

        self._print_progress(index, total, name, diagram_type)

        start = time.time()

        try:
            # Get ctags executable
            ctags_exe = get_ctags_executable()
            if not ctags_exe:
                raise RuntimeError("ctags not found. Run: cum map --install")

            # Determine language filter from source path
            language = self._infer_language(source)

            # Generate ctags for source
            tags_json = generate_ctags(language, ".tags.json", ctags_exe, in_memory=True)
            if not tags_json:
                raise RuntimeError(f"Failed to generate ctags for {source}")

            # Parse tags
            stats = parse_tags_file(tags_json, from_string=True)
            if not stats:
                raise RuntimeError("Failed to parse ctags output")

            # Prepare output path
            output_dir = self.config.get_output_dir()
            output_file = str(output_dir / output)

            # Get generator class
            generator_class = self.GENERATOR_MAP.get(diagram_type)
            if not generator_class:
                raise ValueError(f"Unknown diagram type: {diagram_type}")

            # Extract theme from options
            theme = options.get('theme', 'dark')

            # Create and run generator
            generator = generator_class(stats, output_file, theme=theme)
            generator.generate()

            duration = time.time() - start
            return GenerationResult(name, True, output_file, duration=duration)

        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            self._print_error(f"Generator '{name}' failed: {error_msg}")
            return GenerationResult(name, False, error=error_msg, duration=duration)

    def _infer_language(self, source: str) -> Optional[str]:
        """Infer language filter from source path.

        Args:
            source: Source path string

        Returns:
            Language string ('python', 'csharp', etc.) or None for all languages
        """
        source_lower = source.lower()
        if '.py' in source_lower or 'python' in source_lower:
            return 'python'
        elif '.cs' in source_lower or 'csharp' in source_lower:
            return 'csharp'
        return None

    def _print_dry_run_plan(self, generators: List[Dict]) -> None:
        """Print dry run execution plan.

        Args:
            generators: List of generator configurations
        """
        self._print_message("\n[DRY RUN] Pipeline Execution Plan")
        self._print_message("=" * 80)
        self._print_message(f"Output directory: {self.config.get_output_dir()}")
        self._print_message(f"Total generators: {len(generators)}")
        self._print_message("")

        for idx, gen in enumerate(generators, 1):
            self._print_message(f"{idx}. {gen['name']}")
            self._print_message(f"   Type: {gen['type']}")
            self._print_message(f"   Source: {gen['source']}")
            self._print_message(f"   Output: {gen['output']}")
            options = self.config.get_generator_options(gen)
            if options:
                self._print_message(f"   Options: {options}")
            self._print_message("")

    def _print_header(self, total: int) -> None:
        """Print batch processing header.

        Args:
            total: Total number of generators
        """
        self._print_message("\n" + "=" * 80)
        self._print_message("Batch Diagram Generation Pipeline")
        self._print_message("=" * 80)
        self._print_message(f"Configuration: {self.config.config_file}")
        self._print_message(f"Output directory: {self.config.get_output_dir()}")
        self._print_message(f"Total generators: {total}")
        self._print_message(f"Continue on error: {self.continue_on_error}")
        self._print_message("=" * 80)
        self._print_message("")

    def _print_progress(self, index: int, total: int, name: str, diagram_type: str) -> None:
        """Print generation progress.

        Args:
            index: Current index (1-based)
            total: Total count
            name: Generator name
            diagram_type: Diagram type
        """
        self._print_message(f"[{index}/{total}] Generating '{name}' ({diagram_type})...")

    def _print_summary(self) -> bool:
        """Print final summary report.

        Returns:
            True if all succeeded, False if any failed
        """
        self._print_message("")
        self._print_message("=" * 80)
        self._print_message("Batch Generation Summary")
        self._print_message("=" * 80)

        # Calculate statistics
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0

        # Print overview
        self._print_message(f"Total generators: {total}")
        self._print_message(f"Successful: {successful}")
        self._print_message(f"Failed: {failed}")
        self._print_message(f"Total time: {total_time:.2f}s")
        self._print_message("")

        # Print individual results
        self._print_message("Results:")
        for result in self.results:
            status = "[PASS]" if result.success else "[FAIL]"
            if self.use_color:
                from clickup_framework.utils.colors import colorize, TextColor
                status_color = TextColor.GREEN if result.success else TextColor.RED
                status = colorize(status, status_color)

            msg = f"  {status} {result.name} ({result.duration:.2f}s)"
            if result.success and result.output_file:
                msg += f" -> {result.output_file}"
            elif result.error:
                msg += f" - {result.error}"
            self._print_message(msg)

        self._print_message("")
        self._print_message("=" * 80)

        if failed == 0:
            self._print_message("[SUCCESS] All diagrams generated successfully")
        else:
            self._print_message(f"[WARNING] {failed} generator(s) failed")

        self._print_message("=" * 80)
        self._print_message("")

        return failed == 0

    def _print_message(self, message: str) -> None:
        """Print message to stdout.

        Args:
            message: Message to print
        """
        print(message)

    def _print_error(self, message: str) -> None:
        """Print error message to stderr.

        Args:
            message: Error message
        """
        if self.use_color:
            from clickup_framework.utils.colors import colorize, TextColor
            message = colorize(f"[ERROR] {message}", TextColor.RED)
        else:
            message = f"[ERROR] {message}"
        print(message, file=sys.stderr)
