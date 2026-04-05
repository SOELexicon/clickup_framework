"""Tests for the diagram-diff command."""

from types import SimpleNamespace


from clickup_framework.commands.diagram_diff_command import (
    _infer_format,
    diagram_diff_command,
)


def test_infer_format_uses_output_extension():
    assert _infer_format("report.md", None) == "report"
    assert _infer_format("report.html", None) == "html"
    assert _infer_format(None, None) == "text"


def test_diagram_diff_command_writes_markdown_report(tmp_path):
    baseline = tmp_path / "before.mmd"
    current = tmp_path / "after.mmd"
    output = tmp_path / "diagram_diff.md"

    baseline.write_text("graph TD\n    A --> B\n", encoding="utf-8")
    current.write_text("graph TD\n    A --> C\n    C --> D\n", encoding="utf-8")

    args = SimpleNamespace(
        baseline_file=str(baseline),
        current_file=str(current),
        format="report",
        output=str(output),
        baseline_label=None,
        current_label=None,
        context=2,
        max_changes=5,
        no_color=True,
    )

    diagram_diff_command(args)

    content = output.read_text(encoding="utf-8")
    assert "# Diagram Comparison Report" in content
    assert "## Unified Diff" in content
    assert "```mermaid" in content


def test_diagram_diff_command_prints_text_report(tmp_path, capsys):
    baseline = tmp_path / "before.mmd"
    current = tmp_path / "after.mmd"

    baseline.write_text("graph TD\n    A --> B\n", encoding="utf-8")
    current.write_text("graph TD\n    A --> C\n", encoding="utf-8")

    args = SimpleNamespace(
        baseline_file=str(baseline),
        current_file=str(current),
        format="text",
        output=None,
        baseline_label=None,
        current_label=None,
        context=1,
        max_changes=5,
        no_color=True,
    )

    diagram_diff_command(args)

    captured = capsys.readouterr()
    assert "Diagram Comparison Report" in captured.out
    assert "Unified Diff:" in captured.out
    assert "Added lines" in captured.out or "Modified lines" in captured.out


def test_diagram_diff_command_writes_mermaid_visual_report(tmp_path):
    baseline = tmp_path / "before.mmd"
    current = tmp_path / "after.mmd"
    output = tmp_path / "diagram_diff_visual.md"

    baseline.write_text("graph TD\n    A --> B\n", encoding="utf-8")
    current.write_text("graph TD\n    A --> B\n    B --> C\n", encoding="utf-8")

    from types import SimpleNamespace

    args = SimpleNamespace(
        baseline_file=str(baseline),
        current_file=str(current),
        format="mermaid",
        output=str(output),
        baseline_label=None,
        current_label=None,
        context=2,
        max_changes=5,
        no_color=True,
    )

    diagram_diff_command(args)

    content = output.read_text(encoding="utf-8")
    assert "# Diagram Diff Visual Summary" in content
    assert "flowchart TD" in content
    assert "style ADD fill:#dcfce7" in content
