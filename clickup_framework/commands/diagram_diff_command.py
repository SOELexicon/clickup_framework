"""CLI command for comparing Mermaid diagrams."""

from pathlib import Path

from clickup_framework import get_context_manager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.map_helpers.mermaid.diff import (
    compare_snapshots,
    load_diagram_snapshot,
    render_annotated_mermaid_report,
    render_html_report,
    render_markdown_report,
    render_side_by_side_report,
    render_text_report,
)
from clickup_framework.utils.argparse_helpers import raw_description_formatter
from clickup_framework.commands.utils import add_common_args

COMMAND_METADATA = {
    "category": "📊 Diagram Management",
    "commands": [
        {
            "name": "diagram-diff",
            "args": "<baseline_file> <current_file> [--format FORMAT] [--output-file FILE]",
            "description": "Compare two Mermaid diagrams and summarize structural changes",
        },
    ],
}


def _infer_format(output_path: str | None, explicit_format: str | None) -> str:
    """Infer output format from flags and file extension."""
    if explicit_format:
        return explicit_format
    if not output_path:
        return "text"
    suffix = Path(output_path).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "report"
    if suffix == ".html":
        return "html"
    return "text"


class DiagramDiffCommand(BaseCommand):
    """Compare Mermaid diagrams generically across supported diagram types."""

    def _get_context_manager(self):
        return get_context_manager()

    def _create_client(self):
        return None

    def execute(self):
        output_path = getattr(self.args, 'output_file', None)
        output_format = _infer_format(output_path, self.args.format)
        use_color = bool(output_format == "text" and not output_path and self.use_color and not self.args.no_color)

        baseline = load_diagram_snapshot(
            self.args.baseline_file,
            label=self.args.baseline_label or Path(self.args.baseline_file).name,
        )
        current = load_diagram_snapshot(
            self.args.current_file,
            label=self.args.current_label or Path(self.args.current_file).name,
        )

        result = compare_snapshots(
            baseline,
            current,
            use_color=use_color,
            context_lines=self.args.context,
        )

        if output_format == "text":
            rendered = render_text_report(result, use_color=use_color, max_changes=self.args.max_changes)
        elif output_format == "report":
            rendered = render_markdown_report(result, max_changes=self.args.max_changes)
        elif output_format == "side-by-side":
            rendered = render_side_by_side_report(result, max_changes=self.args.max_changes)
        elif output_format == "html":
            rendered = render_html_report(result, max_changes=self.args.max_changes)
        elif output_format == "mermaid":
            rendered = render_annotated_mermaid_report(result, max_changes=self.args.max_changes)
        else:
            self.error(f"Unsupported format: {output_format}")
            return

        if output_path:
            Path(output_path).write_text(rendered, encoding="utf-8")
            self.print_success(f"Diagram comparison report written to {output_path}")

        self.handle_output(data=result, console_output=rendered)


def diagram_diff_command(args):
    """Backward-compatible function entrypoint."""
    command = DiagramDiffCommand(args, command_name="diagram-diff")
    return command.execute()


def register_command(subparsers):
    """Register the diagram-diff command."""
    parser = subparsers.add_parser(
        "diagram-diff",
        help="Compare two Mermaid diagrams",
        description="Compare two Mermaid diagrams or generated markdown files and report added, removed, and modified elements.",
        formatter_class=raw_description_formatter(),
        epilog="""Examples:
  cum diagram-diff old.mmd new.mmd
  cum diagram-diff docs/old.md docs/new.md --format report --output-file diagram_diff.md
  cum diagram-diff before.mmd after.mmd --format html --output-file diagram_diff.html
  cum diagram-diff before.mmd after.mmd --format mermaid --output-file diagram_diff_visual.md
  cum diagram-diff before.mmd after.mmd --format side-by-side""",
    )
    parser.add_argument("baseline_file", help="Baseline Mermaid file or markdown document containing a Mermaid block")
    parser.add_argument("current_file", help="Current Mermaid file or markdown document containing a Mermaid block")
    parser.add_argument(
        "--format",
        choices=["text", "report", "html", "mermaid", "side-by-side"],
        help="Output format. Defaults to text unless inferred from --output-file",
    )
    parser.add_argument("--output-file", help="Write the comparison report to a file")
    parser.add_argument("--baseline-label", help="Custom display label for the baseline diagram")
    parser.add_argument("--current-label", help="Custom display label for the current diagram")
    parser.add_argument(
        "--context",
        type=int,
        default=3,
        help="Unified diff context lines (default: 3)",
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        default=10,
        help="Maximum added/removed/modified samples to show per section (default: 10)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color in text output",
    )
    add_common_args(parser)
    parser.set_defaults(func=diagram_diff_command)
