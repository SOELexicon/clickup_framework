"""Generic Mermaid diagram diffing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import difflib
import re

from clickup_framework.commands.map_helpers.mermaid.formatters.stats_formatter import (
    DiagramStats,
    StatsFormatter,
)
from clickup_framework.utils.diff import diff_strings

_MERMAID_BLOCK_RE = re.compile(r"```mermaid\r?\n(.*?)\n```", re.DOTALL)
_DECLARATION_PREFIXES = (
    "graph ",
    "flowchart ",
    "sequenceDiagram",
    "classDiagram",
    "pie",
    "mindmap",
    "gantt",
    "journey",
    "gitGraph",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "timeline",
)
_EDGE_TOKENS = (
    "-->",
    "---",
    "-.->",
    "==>",
    "<-->",
    "->>",
    "-->>",
    "-x",
    "x-",
    "<|--",
    "--|>",
    "..>",
)


@dataclass(frozen=True)
class DiagramLine:
    """A meaningful Mermaid source line."""

    line_no: int
    raw: str
    normalized: str
    kind: str
    identifier: Optional[str] = None


@dataclass(frozen=True)
class ModifiedLine:
    """A before/after line replacement."""

    before: DiagramLine
    after: DiagramLine


@dataclass
class DiagramSnapshot:
    """Parsed Mermaid source with lightweight structural metadata."""

    label: str
    source: str
    raw_text: str
    diagram_type: str
    lines: List[DiagramLine]
    stats: DiagramStats

    @property
    def meaningful_line_count(self) -> int:
        """Return the count of non-empty Mermaid lines."""
        return len(self.lines)


@dataclass
class DiagramDiffResult:
    """Comparison result between two Mermaid snapshots."""

    baseline: DiagramSnapshot
    current: DiagramSnapshot
    added_lines: List[DiagramLine]
    removed_lines: List[DiagramLine]
    modified_lines: List[ModifiedLine]
    unified_diff: str
    context_lines: int

    def has_changes(self) -> bool:
        """Return True when any added, removed, or modified lines exist."""
        return bool(self.added_lines or self.removed_lines or self.modified_lines)

    def summarize_lines_by_kind(self, lines: List[DiagramLine]) -> Dict[str, int]:
        """Summarize line counts by Mermaid line classification."""
        counts: Dict[str, int] = {}
        for line in lines:
            counts[line.kind] = counts.get(line.kind, 0) + 1
        return counts

    def summarize_modified_by_kind(self) -> Dict[str, int]:
        """Summarize modified line counts by the baseline line classification."""
        counts: Dict[str, int] = {}
        for change in self.modified_lines:
            counts[change.before.kind] = counts.get(change.before.kind, 0) + 1
        return counts


def extract_mermaid_source(text: str) -> str:
    """Extract Mermaid source from markdown or return raw Mermaid text."""
    if not text:
        return ""

    match = _MERMAID_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def load_diagram_snapshot(file_path: str, label: Optional[str] = None) -> DiagramSnapshot:
    """Load and parse a Mermaid diagram file."""
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    return build_snapshot_from_text(text, label=label or path.name)


def build_snapshot_from_text(text: str, label: str = "diagram") -> DiagramSnapshot:
    """Parse Mermaid text into a reusable snapshot object."""
    source = extract_mermaid_source(text)
    raw_lines = source.splitlines()
    meaningful_lines: List[DiagramLine] = []

    for index, raw_line in enumerate(raw_lines, start=1):
        normalized = raw_line.strip()
        if not normalized:
            continue
        kind = _classify_line(normalized)
        meaningful_lines.append(
            DiagramLine(
                line_no=index,
                raw=raw_line.rstrip(),
                normalized=normalized,
                kind=kind,
                identifier=_extract_identifier(normalized, kind),
            )
        )

    stats_input = ["```mermaid", *raw_lines, "```"] if source else []
    stats = StatsFormatter.collect_from_lines(stats_input) if stats_input else DiagramStats()
    return DiagramSnapshot(
        label=label,
        source=source,
        raw_text=text,
        diagram_type=_detect_diagram_type(source),
        lines=meaningful_lines,
        stats=stats,
    )


def compare_snapshots(
    baseline: DiagramSnapshot,
    current: DiagramSnapshot,
    *,
    use_color: bool = False,
    context_lines: int = 3,
) -> DiagramDiffResult:
    """Compare two Mermaid snapshots generically across diagram types."""
    baseline_lines = [line.normalized for line in baseline.lines]
    current_lines = [line.normalized for line in current.lines]
    matcher = difflib.SequenceMatcher(a=baseline_lines, b=current_lines, autojunk=False)

    added_lines: List[DiagramLine] = []
    removed_lines: List[DiagramLine] = []
    modified_lines: List[ModifiedLine] = []

    for opcode, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if opcode == "equal":
            continue
        if opcode == "insert":
            added_lines.extend(current.lines[new_start:new_end])
            continue
        if opcode == "delete":
            removed_lines.extend(baseline.lines[old_start:old_end])
            continue

        old_chunk = baseline.lines[old_start:old_end]
        new_chunk = current.lines[new_start:new_end]
        shared_length = min(len(old_chunk), len(new_chunk))
        for index in range(shared_length):
            modified_lines.append(ModifiedLine(before=old_chunk[index], after=new_chunk[index]))
        if len(old_chunk) > shared_length:
            removed_lines.extend(old_chunk[shared_length:])
        if len(new_chunk) > shared_length:
            added_lines.extend(new_chunk[shared_length:])

    unified_diff = diff_strings(
        baseline.source,
        current.source,
        old_label=baseline.label,
        new_label=current.label,
        context_lines=context_lines,
        use_color=use_color,
    )

    return DiagramDiffResult(
        baseline=baseline,
        current=current,
        added_lines=added_lines,
        removed_lines=removed_lines,
        modified_lines=modified_lines,
        unified_diff=unified_diff,
        context_lines=context_lines,
    )


def _detect_diagram_type(source: str) -> str:
    """Detect Mermaid diagram type from the first meaningful line."""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        head = stripped.split(maxsplit=1)[0]
        return head
    return "unknown"


def _classify_line(line: str) -> str:
    """Classify a Mermaid line in a diagram-type-agnostic way."""
    if line.startswith("%%") or line.startswith("%%{"):
        return "directive"
    if line.startswith(_DECLARATION_PREFIXES):
        return "declaration"
    if line.startswith("subgraph "):
        return "subgraph"
    if line == "end":
        return "subgraph-end"
    if line.startswith(("style ", "classDef ", "class ", "linkStyle ", "click ")):
        return "style"
    if line.startswith(("participant ", "actor ", "note ", "alt ", "opt ", "loop ", "rect ", "activate ", "deactivate ")):
        return "diagram"
    if any(token in line for token in _EDGE_TOKENS):
        return "edge"
    return "node"


def _extract_identifier(line: str, kind: str) -> Optional[str]:
    """Extract a best-effort logical identifier for reporting."""
    if kind == "subgraph":
        match = re.match(r"subgraph\s+([^\s\[]+)", line)
        return match.group(1) if match else None
    if kind in {"node", "style"}:
        match = re.match(r"([A-Za-z_][\w.-]*)", line)
        return match.group(1) if match else None
    return None
