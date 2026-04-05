"""Render Mermaid diff results in text, markdown, or HTML."""

from __future__ import annotations

from html import escape
import re
from typing import Dict, Iterable

from clickup_framework.commands.map_helpers.mermaid.formatters.stats_formatter import StatsFormatter
from clickup_framework.utils.colors import TextColor, colorize

from .diagram_differ import DiagramDiffResult, DiagramLine, ModifiedLine


def render_text_report(
    result: DiagramDiffResult,
    *,
    use_color: bool = False,
    max_changes: int = 10,
) -> str:
    """Render a terminal-friendly Mermaid diff report."""
    lines = [
        _decorate("Diagram Comparison Report", TextColor.BRIGHT_CYAN, use_color),
        _decorate("=" * 32, TextColor.BRIGHT_CYAN, use_color),
        f"Baseline: {result.baseline.label} ({result.baseline.diagram_type}, {result.baseline.stats.node_count} nodes, {result.baseline.stats.edge_count} edges)",
        f"Current:  {result.current.label} ({result.current.diagram_type}, {result.current.stats.node_count} nodes, {result.current.stats.edge_count} edges)",
        "",
        "Changes:",
        _decorate(f"  + Added lines: {len(result.added_lines)}", TextColor.GREEN, use_color),
        _decorate(f"  - Removed lines: {len(result.removed_lines)}", TextColor.RED, use_color),
        _decorate(f"  ~ Modified lines: {len(result.modified_lines)}", TextColor.BRIGHT_YELLOW, use_color),
        "",
        "Stats:",
        StatsFormatter.compare_stats(result.baseline.stats, result.current.stats).strip(),
    ]

    _append_summary(lines, "Added Elements", result.added_lines, result.summarize_lines_by_kind(result.added_lines), use_color, max_changes)
    _append_summary(lines, "Removed Elements", result.removed_lines, result.summarize_lines_by_kind(result.removed_lines), use_color, max_changes)
    _append_modified_summary(lines, result.modified_lines, result.summarize_modified_by_kind(), use_color, max_changes)

    lines.extend([
        "",
        "Unified Diff:",
        result.unified_diff.rstrip(),
        "",
    ])
    return "\n".join(lines)


def render_markdown_report(result: DiagramDiffResult, *, max_changes: int = 10) -> str:
    """Render a markdown Mermaid diff report."""
    lines = [
        "# Diagram Comparison Report",
        "",
        "## Summary",
        "",
        f"- **Baseline:** `{result.baseline.label}` (`{result.baseline.diagram_type}`)",
        f"- **Current:** `{result.current.label}` (`{result.current.diagram_type}`)",
        f"- **Added lines:** {len(result.added_lines)}",
        f"- **Removed lines:** {len(result.removed_lines)}",
        f"- **Modified lines:** {len(result.modified_lines)}",
        "",
        "## Stats Comparison",
        "",
        "```text",
        StatsFormatter.compare_stats(result.baseline.stats, result.current.stats).strip(),
        "```",
    ]

    _append_markdown_lines(lines, "Added Elements", result.added_lines, result.summarize_lines_by_kind(result.added_lines), max_changes)
    _append_markdown_lines(lines, "Removed Elements", result.removed_lines, result.summarize_lines_by_kind(result.removed_lines), max_changes)
    _append_markdown_modifications(lines, result.modified_lines, result.summarize_modified_by_kind(), max_changes)

    lines.extend([
        "",
        "## Unified Diff",
        "",
        "```diff",
        _strip_ansi(result.unified_diff).rstrip(),
        "```",
        "",
        "## Baseline Diagram",
        "",
        "```mermaid",
        result.baseline.source,
        "```",
        "",
        "## Current Diagram",
        "",
        "```mermaid",
        result.current.source,
        "```",
        "",
    ])
    return "\n".join(lines)


def render_side_by_side_report(result: DiagramDiffResult, *, max_changes: int = 10) -> str:
    """Render a markdown side-by-side comparison report."""
    lines = [
        "# Diagram Side-by-Side Comparison",
        "",
        "## Change Summary",
        "",
        f"- **Added lines:** {len(result.added_lines)} ({_format_kind_counts(result.summarize_lines_by_kind(result.added_lines))})",
        f"- **Removed lines:** {len(result.removed_lines)} ({_format_kind_counts(result.summarize_lines_by_kind(result.removed_lines))})",
        f"- **Modified lines:** {len(result.modified_lines)} ({_format_kind_counts(result.summarize_modified_by_kind())})",
        "",
        "## Baseline",
        "",
        "```mermaid",
        result.baseline.source,
        "```",
        "",
        "## Current",
        "",
        "```mermaid",
        result.current.source,
        "```",
    ]

    _append_markdown_modifications(lines, result.modified_lines, result.summarize_modified_by_kind(), max_changes)
    return "\n".join(lines) + "\n"


def render_html_report(result: DiagramDiffResult, *, max_changes: int = 10) -> str:
    """Render a self-contained HTML Mermaid diff report."""
    unified_diff = _strip_ansi(result.unified_diff).splitlines()
    diff_html = []
    for line in unified_diff:
        css_class = "ctx"
        if line.startswith("+++ ") or line.startswith("--- "):
            css_class = "meta"
        elif line.startswith("@@"):
            css_class = "hunk"
        elif line.startswith("+"):
            css_class = "add"
        elif line.startswith("-"):
            css_class = "remove"
        diff_html.append(f'<span class="{css_class}">{escape(line)}</span>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Diagram Comparison Report</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 2rem; color: #1f2937; background: #f8fafc; }}
    h1, h2, h3 {{ color: #0f172a; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0 2rem; }}
    .card {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 1rem; }}
    .card strong {{ display: block; font-size: 1.5rem; margin-top: 0.25rem; }}
    .kind {{ color: #475569; font-size: 0.95rem; }}
    .added {{ border-left: 4px solid #16a34a; padding-left: 0.75rem; }}
    .removed {{ border-left: 4px solid #dc2626; padding-left: 0.75rem; }}
    .modified {{ border-left: 4px solid #ca8a04; padding-left: 0.75rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; }}
    pre {{ background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; }}
    .diff span {{ display: block; }}
    .diff .meta {{ color: #cbd5e1; }}
    .diff .hunk {{ color: #7dd3fc; }}
    .diff .add {{ color: #86efac; }}
    .diff .remove {{ color: #fca5a5; }}
    .diff .ctx {{ color: #e2e8f0; }}
  </style>
</head>
<body>
  <h1>Diagram Comparison Report</h1>
  <p><strong>Baseline:</strong> {escape(result.baseline.label)} ({escape(result.baseline.diagram_type)})<br>
     <strong>Current:</strong> {escape(result.current.label)} ({escape(result.current.diagram_type)})</p>

  <div class="summary">
    <div class="card added">Added lines<strong>{len(result.added_lines)}</strong><div class="kind">{escape(_format_kind_counts(result.summarize_lines_by_kind(result.added_lines)))}</div></div>
    <div class="card removed">Removed lines<strong>{len(result.removed_lines)}</strong><div class="kind">{escape(_format_kind_counts(result.summarize_lines_by_kind(result.removed_lines)))}</div></div>
    <div class="card modified">Modified lines<strong>{len(result.modified_lines)}</strong><div class="kind">{escape(_format_kind_counts(result.summarize_modified_by_kind()))}</div></div>
  </div>

  <h2>Stats Comparison</h2>
  <pre>{escape(StatsFormatter.compare_stats(result.baseline.stats, result.current.stats).strip())}</pre>

  <h2>Unified Diff</h2>
  <pre class="diff">{''.join(diff_html)}</pre>

  <div class="grid">
    <section>
      <h2>Baseline Diagram</h2>
      <pre>{escape(result.baseline.source)}</pre>
    </section>
    <section>
      <h2>Current Diagram</h2>
      <pre>{escape(result.current.source)}</pre>
    </section>
  </div>

  <h2>Change Samples</h2>
  <div class="grid">
    <section>
      <h3>Added</h3>
      {_render_html_line_list(result.added_lines, max_changes)}
    </section>
    <section>
      <h3>Removed</h3>
      {_render_html_line_list(result.removed_lines, max_changes, css_class="removed")}
    </section>
    <section>
      <h3>Modified</h3>
      {_render_html_modifications(result.modified_lines, max_changes)}
    </section>
  </div>
</body>
</html>
"""


def render_annotated_mermaid_report(result: DiagramDiffResult, *, max_changes: int = 10) -> str:
    """Render a markdown report with a Mermaid visual summary diagram."""
    added = len(result.added_lines)
    removed = len(result.removed_lines)
    modified = len(result.modified_lines)
    baseline_label = _escape_mermaid_label(result.baseline.label)
    current_label = _escape_mermaid_label(result.current.label)
    baseline_type = _escape_mermaid_label(result.baseline.diagram_type)
    current_type = _escape_mermaid_label(result.current.diagram_type)
    summary_diagram = [
        "flowchart TD",
        f'    BASE["Baseline\\n{baseline_label}\\n{baseline_type}\\n{result.baseline.stats.node_count} nodes / {result.baseline.stats.edge_count} edges"]',
        f'    CUR["Current\\n{current_label}\\n{current_type}\\n{result.current.stats.node_count} nodes / {result.current.stats.edge_count} edges"]',
        f'    ADD["Added\\n{added}\\n{_escape_mermaid_label(_format_kind_counts(result.summarize_lines_by_kind(result.added_lines)))}"]',
        f'    REM["Removed\\n{removed}\\n{_escape_mermaid_label(_format_kind_counts(result.summarize_lines_by_kind(result.removed_lines)))}"]',
        f'    MOD["Modified\\n{modified}\\n{_escape_mermaid_label(_format_kind_counts(result.summarize_modified_by_kind()))}"]',
        "    BASE --> CUR",
        "    CUR --> ADD",
        "    CUR --> REM",
        "    CUR --> MOD",
        "    style ADD fill:#dcfce7,stroke:#16a34a,color:#166534",
        "    style REM fill:#fee2e2,stroke:#dc2626,color:#991b1b",
        "    style MOD fill:#fef3c7,stroke:#ca8a04,color:#92400e",
    ]

    lines = [
        "# Diagram Diff Visual Summary",
        "",
        "This report renders a Mermaid summary diagram with color-coded change buckets.",
        "",
        "```mermaid",
        *summary_diagram,
        "```",
    ]
    _append_markdown_lines(lines, "Added Elements", result.added_lines, result.summarize_lines_by_kind(result.added_lines), max_changes)
    _append_markdown_lines(lines, "Removed Elements", result.removed_lines, result.summarize_lines_by_kind(result.removed_lines), max_changes)
    _append_markdown_modifications(lines, result.modified_lines, result.summarize_modified_by_kind(), max_changes)
    lines.extend([
        "",
        "## Unified Diff",
        "",
        "```diff",
        _strip_ansi(result.unified_diff).rstrip(),
        "```",
        "",
    ])
    return "\n".join(lines)


def _append_summary(
    lines: list[str],
    title: str,
    change_lines: Iterable[DiagramLine],
    kind_counts: Dict[str, int],
    use_color: bool,
    max_changes: int,
) -> None:
    change_lines = list(change_lines)
    if not change_lines:
        return
    lines.extend([
        "",
        title + f" ({_format_kind_counts(kind_counts)})",
    ])
    for line in change_lines[:max_changes]:
        lines.append(_decorate(f"  • L{line.line_no} [{line.kind}] {line.normalized}", _title_color(title), use_color))
    if len(change_lines) > max_changes:
        lines.append(f"  ... {len(change_lines) - max_changes} more")


def _append_modified_summary(
    lines: list[str],
    modifications: Iterable[ModifiedLine],
    kind_counts: Dict[str, int],
    use_color: bool,
    max_changes: int,
) -> None:
    modifications = list(modifications)
    if not modifications:
        return
    lines.extend([
        "",
        f"Modified Elements ({_format_kind_counts(kind_counts)})",
    ])
    for change in modifications[:max_changes]:
        before = f"L{change.before.line_no} [{change.before.kind}] {change.before.normalized}"
        after = f"L{change.after.line_no} [{change.after.kind}] {change.after.normalized}"
        lines.append(_decorate(f"  ~ {before}", TextColor.BRIGHT_YELLOW, use_color))
        lines.append(_decorate(f"    -> {after}", TextColor.BRIGHT_YELLOW, use_color))
    if len(modifications) > max_changes:
        lines.append(f"  ... {len(modifications) - max_changes} more")


def _append_markdown_lines(
    lines: list[str],
    title: str,
    change_lines: Iterable[DiagramLine],
    kind_counts: Dict[str, int],
    max_changes: int,
) -> None:
    change_lines = list(change_lines)
    if not change_lines:
        return
    lines.extend(["", f"## {title}", "", f"- **Kinds:** {_format_kind_counts(kind_counts)}"])
    for line in change_lines[:max_changes]:
        lines.append(f"- `L{line.line_no}` [{line.kind}] `{line.normalized}`")
    if len(change_lines) > max_changes:
        lines.append(f"- ... {len(change_lines) - max_changes} more")


def _append_markdown_modifications(
    lines: list[str],
    modifications: Iterable[ModifiedLine],
    kind_counts: Dict[str, int],
    max_changes: int,
) -> None:
    modifications = list(modifications)
    if not modifications:
        return
    lines.extend(["", "## Modified Elements", "", f"- **Kinds:** {_format_kind_counts(kind_counts)}"])
    for change in modifications[:max_changes]:
        lines.append(f"- `L{change.before.line_no}` `{change.before.normalized}`")
        lines.append(f"  - becomes `L{change.after.line_no}` `{change.after.normalized}`")
    if len(modifications) > max_changes:
        lines.append(f"- ... {len(modifications) - max_changes} more")


def _render_html_line_list(lines: Iterable[DiagramLine], max_changes: int, css_class: str = "added") -> str:
    lines = list(lines)
    if not lines:
        return "<p>No changes.</p>"
    items = []
    for line in lines[:max_changes]:
        items.append(f'<li class="{css_class}">L{line.line_no} [{escape(line.kind)}] <code>{escape(line.normalized)}</code></li>')
    if len(lines) > max_changes:
        items.append(f"<li>... {len(lines) - max_changes} more</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _render_html_modifications(modifications: Iterable[ModifiedLine], max_changes: int) -> str:
    modifications = list(modifications)
    if not modifications:
        return "<p>No changes.</p>"
    items = []
    for change in modifications[:max_changes]:
        items.append(
            "<li class=\"modified\">"
            f"Before: <code>{escape(change.before.normalized)}</code><br>"
            f"After: <code>{escape(change.after.normalized)}</code>"
            "</li>"
        )
    if len(modifications) > max_changes:
        items.append(f"<li>... {len(modifications) - max_changes} more</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _format_kind_counts(kind_counts: Dict[str, int]) -> str:
    if not kind_counts:
        return "none"
    return ", ".join(f"{kind}:{count}" for kind, count in sorted(kind_counts.items()))


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _escape_mermaid_label(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")


def _decorate(text: str, color: TextColor, use_color: bool) -> str:
    if use_color:
        return colorize(text, color)
    return text


def _title_color(title: str) -> TextColor:
    if title.startswith("Added"):
        return TextColor.GREEN
    if title.startswith("Removed"):
        return TextColor.RED
    return TextColor.BRIGHT_YELLOW
