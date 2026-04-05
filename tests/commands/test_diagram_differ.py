"""Tests for Mermaid diagram diff helpers."""

from clickup_framework.commands.map_helpers.mermaid.diff import (
    build_snapshot_from_text,
    compare_snapshots,
    extract_mermaid_source,
    render_annotated_mermaid_report,
    render_html_report,
    render_markdown_report,
)


def test_extract_mermaid_source_from_markdown_block():
    markdown = """# Diagram

```mermaid
graph TD
    A --> B
```
"""

    assert extract_mermaid_source(markdown) == "graph TD\n    A --> B"


def test_compare_snapshots_tracks_added_removed_and_modified_lines():
    baseline = build_snapshot_from_text(
        "graph TD\n    A[Start] --> B[Old]\n    B --> C[Stable]\n",
        label="before.mmd",
    )
    current = build_snapshot_from_text(
        "graph TD\n    A[Start] --> B[New]\n    B --> C[Stable]\n    C --> D[Added]\n",
        label="after.mmd",
    )

    result = compare_snapshots(baseline, current, use_color=False, context_lines=1)

    assert len(result.modified_lines) == 1
    assert result.modified_lines[0].before.normalized == "A[Start] --> B[Old]"
    assert result.modified_lines[0].after.normalized == "A[Start] --> B[New]"
    assert [line.normalized for line in result.added_lines] == ["C --> D[Added]"]
    assert result.removed_lines == []
    assert result.has_changes() is True


def test_render_reports_include_key_change_sections():
    baseline = build_snapshot_from_text("graph TD\n    A --> B\n", label="before.mmd")
    current = build_snapshot_from_text("graph TD\n    A --> C\n    C --> D\n", label="after.mmd")
    result = compare_snapshots(baseline, current, use_color=False, context_lines=2)

    markdown = render_markdown_report(result, max_changes=5)
    html = render_html_report(result, max_changes=5)

    assert "## Unified Diff" in markdown
    assert "Diagram Comparison Report" in markdown
    assert "<title>Diagram Comparison Report</title>" in html
    assert "Baseline Diagram" in html
    assert "Current Diagram" in html


def test_sequence_diagrams_compare_generically_and_mermaid_summary_renders():
    baseline = build_snapshot_from_text(
        "sequenceDiagram\n    participant A\n    participant B\n    A->>B: Hello\n",
        label="before.mmd",
    )
    current = build_snapshot_from_text(
        "sequenceDiagram\n    participant A\n    participant B\n    A->>B: Hello there\n    B-->>A: Ack\n",
        label="after.mmd",
    )

    result = compare_snapshots(baseline, current, use_color=False, context_lines=2)
    annotated = render_annotated_mermaid_report(result, max_changes=5)

    assert result.modified_lines
    assert result.added_lines
    assert "```mermaid" in annotated
    assert "style ADD fill:#dcfce7" in annotated
