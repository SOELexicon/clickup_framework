# Diagram Diff

`cum diagram-diff` compares two Mermaid diagrams or markdown files that contain Mermaid blocks.

## Usage

```bash
cum diagram-diff before.mmd after.mmd
cum diagram-diff before.md after.md --format report --output diagram_diff.md
cum diagram-diff before.mmd after.mmd --format html --output diagram_diff.html
cum diagram-diff before.mmd after.mmd --format mermaid --output diagram_diff_visual.md
```

## Diff Algorithm

The comparison is intentionally line-based so it works across Mermaid diagram types instead of depending on a type-specific AST.

1. Extract Mermaid source from a raw `.mmd` file or the first ````mermaid` fenced block in markdown.
2. Normalize to meaningful non-empty lines while preserving the original source for unified diff output.
3. Classify each line generically as `declaration`, `node`, `edge`, `subgraph`, `style`, `diagram`, or `directive`.
4. Run `difflib.SequenceMatcher` across normalized lines.
5. Treat inserts as added elements, deletes as removed elements, and replacements as modified elements.
6. Compare diagram statistics using the shared Mermaid stats formatter.

This means the command can compare flowcharts, class diagrams, sequence diagrams, mindmaps, and other Mermaid sources without needing separate parsers per type.

## Output Formats

- `text`: console report with colorized added/removed/modified sections and unified diff
- `report`: markdown report with summary, stats comparison, change sections, and both diagrams
- `html`: self-contained HTML report with colored change buckets and side-by-side source panes
- `mermaid`: markdown report with a color-coded Mermaid visual summary diagram
- `side-by-side`: markdown report that focuses on baseline/current diagrams plus modification samples
