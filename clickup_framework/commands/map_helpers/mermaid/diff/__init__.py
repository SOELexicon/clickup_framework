"""Generic Mermaid diagram diffing helpers."""

from .diagram_differ import (
    DiagramDiffResult,
    DiagramLine,
    DiagramSnapshot,
    ModifiedLine,
    build_snapshot_from_text,
    compare_snapshots,
    extract_mermaid_source,
    load_diagram_snapshot,
)
from .diff_visualizer import (
    render_annotated_mermaid_report,
    render_html_report,
    render_markdown_report,
    render_side_by_side_report,
    render_text_report,
)

__all__ = [
    "DiagramDiffResult",
    "DiagramLine",
    "DiagramSnapshot",
    "ModifiedLine",
    "build_snapshot_from_text",
    "compare_snapshots",
    "extract_mermaid_source",
    "load_diagram_snapshot",
    "render_annotated_mermaid_report",
    "render_html_report",
    "render_markdown_report",
    "render_side_by_side_report",
    "render_text_report",
]
