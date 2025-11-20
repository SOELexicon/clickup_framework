"""Base generator class for all Mermaid diagram types.

This module implements the template method pattern to define a standard workflow
for all diagram generators. Subclasses override specific methods to customize
diagram generation while inheriting common functionality like validation,
file I/O, and metadata export.

Template Method Pattern:
    generate() defines the workflow: validate → header → body → footer → validate → write
    Subclasses override generate_body() and validate_inputs() only.

Usage:
    class MyGenerator(BaseGenerator):
        def validate_inputs(self, **kwargs):
            # Validate specific inputs for your diagram type
            pass

        def generate_body(self, **kwargs):
            # Generate diagram-specific content
            self._add_diagram_declaration('graph TD')
            # Add nodes, edges, etc.
"""

import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ..core.metadata_store import MetadataStore
from ..styling import ThemeManager
from ..profiling import PerformanceProfiler, register_profile
from ..config import get_config
from ...mermaid_validator import validate_and_raise


class BaseGenerator(ABC):
    """Abstract base class for all Mermaid diagram generators.

    This class provides:
    - Template method pattern for generation workflow
    - Common utilities (validation, file I/O, metadata)
    - Theme management integration
    - Error handling with context

    Attributes:
        output_file: Path to output markdown file
        theme_manager: Theme manager for styling
        metadata_store: Store for diagram metadata
        lines: List of diagram lines being built
        stats: Statistics dictionary from parsing
    """

    def __init__(
        self,
        stats: Dict[str, Any],
        output_file: str,
        theme: str = 'dark',
        metadata_store: Optional[MetadataStore] = None
    ):
        """Initialize base generator.

        Args:
            stats: Statistics dictionary from tag parsing
            output_file: Output markdown file path
            theme: Color theme ('dark' or 'light')
            metadata_store: Optional metadata store (creates new if None)
        """
        self.stats = stats
        self.output_file = output_file
        self.theme_manager = ThemeManager(theme)
        self.metadata_store = metadata_store or MetadataStore()
        self.lines: List[str] = []
        self._profiler: Optional[PerformanceProfiler] = None
        self._profile_report = None  # Store final report

    def generate(self, **kwargs) -> str:
        """Generate diagram following standard workflow (Template Method).

        This defines the algorithm structure. Subclasses override specific steps
        (validate_inputs and generate_body) but cannot change the overall flow.

        Workflow:
            1. Validate inputs
            2. Add header (title + mermaid fence)
            3. Generate diagram body (abstract - subclass implements)
            4. Add footer (closing fence + statistics)
            5. Validate diagram syntax
            6. Write files (diagram + metadata)

        Args:
            **kwargs: Diagram-specific parameters passed to subclass methods

        Returns:
            Path to generated output file

        Raises:
            Exception: Any error during generation (logged with context)
        """
        # Initialize profiler if enabled
        config = get_config()
        generator_name = self.__class__.__name__
        self._profiler = PerformanceProfiler(
            f"{generator_name}.generate",
            enabled=config.profiling.enabled
        )

        try:
            with self._profiler as profiler:
                profiler.add_metadata('generator', generator_name)
                profiler.add_metadata('output_file', self.output_file)
                profiler.add_metadata('total_symbols', self.stats.get('total_symbols', 0))

                self.validate_inputs(**kwargs)
                profiler.checkpoint('validation_complete')

                self._add_header()
                profiler.checkpoint('header_added')

                self.generate_body(**kwargs)
                profiler.checkpoint('body_generated')

                self._add_footer()
                profiler.checkpoint('footer_added')

                self._validate_diagram()
                profiler.checkpoint('diagram_validated')

                self._write_files()
                profiler.checkpoint('files_written')

                # Store and optionally handle report
                self._profile_report = profiler.get_report()
                self._handle_profile_report()

            return self.output_file
        except Exception as e:
            self._handle_error(e)
            raise

    @abstractmethod
    def validate_inputs(self, **kwargs) -> None:
        """Validate diagram-specific inputs.

        Subclasses must implement this to check:
        - Required parameters are provided
        - Parameters have valid values/types
        - Data structures are not empty

        Raises:
            ValueError: If inputs are invalid
        """
        pass

    @abstractmethod
    def generate_body(self, **kwargs) -> None:
        """Generate diagram-specific content.

        Subclasses must implement this to build diagram body.
        Use helper methods like:
        - _add_diagram_declaration(type)
        - _add_line(content)
        - _add_lines(content_list)

        The implementation should NOT:
        - Add opening/closing code fences (header/footer handles this)
        - Validate diagram (parent handles this)
        - Write files (parent handles this)
        """
        pass

    # Protected helper methods for subclasses

    def _add_diagram_declaration(self, declaration: str) -> None:
        """Add diagram type declaration (e.g., 'graph TD', 'classDiagram').

        Args:
            declaration: Mermaid diagram type declaration
        """
        self.lines.append(declaration)

    def _add_line(self, content: str) -> None:
        """Add a single line to the diagram.

        Args:
            content: Line content
        """
        self.lines.append(content)

    def _add_lines(self, content_list: List[str]) -> None:
        """Add multiple lines to the diagram.

        Args:
            content_list: List of line contents
        """
        self.lines.extend(content_list)

    # Private concrete methods - shared implementation

    def _add_header(self) -> None:
        """Add document header with title and mermaid code fence."""
        title = self._get_diagram_title()
        self.lines.extend([
            f"# {title}",
            "",
            "```mermaid"
        ])

    def _get_diagram_title(self) -> str:
        """Get diagram title (can be overridden by subclasses).

        Returns:
            Default title based on output filename
        """
        filename = Path(self.output_file).stem
        return filename.replace('_', ' ').replace('diagram', '').title().strip()

    def _add_footer(self) -> None:
        """Add closing code fence and statistics section."""
        self.lines.extend([
            "```",
            "",
            "## Statistics",
            ""
        ])

        # Add basic statistics
        total_symbols = self.stats.get('total_symbols', 0)
        files_analyzed = self.stats.get('files_analyzed', 0)
        by_language = self.stats.get('by_language', {})

        self.lines.extend([
            f"- **Total Symbols**: {total_symbols}",
            f"- **Files Analyzed**: {files_analyzed}",
            f"- **Languages**: {len(by_language)}",
            ""
        ])

        # Add language breakdown if available
        if by_language:
            self.lines.append("### By Language")
            self.lines.append("")
            for lang in sorted(by_language.keys()):
                count = sum(by_language[lang].values())
                self.lines.append(f"- **{lang}**: {count} symbols")
                for kind, kind_count in sorted(by_language[lang].items()):
                    self.lines.append(f"  - {kind}: {kind_count}")

    def _validate_diagram(self) -> None:
        """Validate generated diagram meets Mermaid requirements.

        Raises:
            Exception: If diagram validation fails
        """
        validate_and_raise(self.lines)

    def _write_files(self) -> None:
        """Write diagram and metadata files.

        Writes:
            1. Markdown file with diagram
            2. JSON metadata file (if metadata store has data)

        Raises:
            Exception: If file writing fails
        """
        # Write diagram markdown file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
        except Exception as e:
            print(f"Error writing diagram file: {e}", file=sys.stderr)
            raise

        # Write metadata file if metadata exists
        if self.metadata_store and self.metadata_store.has_data():
            metadata_file = str(Path(self.output_file).with_suffix('')) + '_metadata.json'
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    f.write(self.metadata_store.export_json(indent=2))
            except Exception as e:
                print(f"Warning: Could not write metadata file: {e}", file=sys.stderr)

    def _handle_error(self, error: Exception) -> None:
        """Log error with helpful context.

        Args:
            error: The exception that occurred
        """
        print(f"[ERROR] Diagram generation failed: {error}", file=sys.stderr)
        print(f"[INFO] Output file: {self.output_file}", file=sys.stderr)
        print(f"[INFO] Lines generated: {len(self.lines)}", file=sys.stderr)

    def _handle_profile_report(self) -> None:
        """Handle performance profile report based on configuration.

        Actions:
        - Register report in global registry
        - Print report to stdout if configured
        - Save report to file if configured
        """
        if not self._profile_report:
            return

        config = get_config()

        # Always register for potential later access
        register_profile(self._profile_report)

        # Print report if configured
        if config.profiling.print_reports:
            print(self._profile_report.format_text())

        # Save report to file if configured
        if config.profiling.save_reports:
            self._save_profile_report()

    def _save_profile_report(self) -> None:
        """Save performance profile report to file."""
        if not self._profile_report:
            return

        config = get_config()
        output_dir = Path(config.profiling.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from output file
        base_name = Path(self.output_file).stem
        profile_file = output_dir / f"{base_name}_profile.json"

        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(self._profile_report.to_dict(), f, indent=2)
            print(f"[INFO] Profile saved to: {profile_file}", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Could not save profile report: {e}", file=sys.stderr)
