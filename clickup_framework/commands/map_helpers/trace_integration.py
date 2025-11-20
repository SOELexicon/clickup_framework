"""
Trace Integration Module

Integrates dynamic execution tracing with static code mapping for enhanced visualizations.
Provides hot path highlighting, trace comparison, and time-series tracking.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class TraceDataManager:
    """Manages execution trace data, comparison, and time-series tracking."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.trace_history_dir = self.project_root / ".trace_history"
        self.trace_history_dir.mkdir(exist_ok=True)

    def save_trace(self, trace_data: Dict[str, Any], label: str = "latest") -> Path:
        """
        Save trace data with timestamp for time-series tracking.

        Args:
            trace_data: Dictionary containing call_graph, called_functions, etc.
            label: Label for this trace (e.g., "before_refactor", "after_refactor")

        Returns:
            Path to saved trace file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{label}_{timestamp}.json"
        trace_file = self.trace_history_dir / filename

        # Add metadata
        trace_data['metadata'] = {
            'timestamp': timestamp,
            'label': label,
            'project_root': str(self.project_root)
        }

        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, indent=2)

        # Also save as "latest" for easy access
        latest_file = self.trace_history_dir / f"trace_{label}_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, indent=2)

        return trace_file

    def load_trace(self, label: str = "latest") -> Optional[Dict[str, Any]]:
        """
        Load trace data by label.

        Args:
            label: Label of trace to load (e.g., "latest", "before_refactor")

        Returns:
            Trace data dictionary or None if not found
        """
        trace_file = self.trace_history_dir / f"trace_{label}_latest.json"
        if not trace_file.exists():
            return None

        with open(trace_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_traces(self) -> List[Dict[str, str]]:
        """
        List all saved traces.

        Returns:
            List of dicts with trace metadata (label, timestamp, file)
        """
        traces = []
        for trace_file in self.trace_history_dir.glob("trace_*.json"):
            if "_latest" not in trace_file.name:
                try:
                    with open(trace_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        traces.append({
                            'label': metadata.get('label', 'unknown'),
                            'timestamp': metadata.get('timestamp', ''),
                            'file': str(trace_file)
                        })
                except Exception:
                    pass

        return sorted(traces, key=lambda x: x['timestamp'], reverse=True)

    def compare_traces(self, label_a: str, label_b: str) -> Dict[str, Any]:
        """
        Compare two traces to identify changes in hot paths.

        Args:
            label_a: Label of first trace (e.g., "before")
            label_b: Label of second trace (e.g., "after")

        Returns:
            Dictionary with comparison results
        """
        trace_a = self.load_trace(label_a)
        trace_b = self.load_trace(label_b)

        if not trace_a or not trace_b:
            return {
                'error': f"Could not load traces: {label_a}, {label_b}",
                'available_traces': [t['label'] for t in self.list_traces()]
            }

        # Convert call_graph lists back to tuples for comparison
        call_graph_a = {tuple(json.loads(k)): v for k, v in trace_a.get('call_graph', {}).items()}
        call_graph_b = {tuple(json.loads(k)): v for k, v in trace_b.get('call_graph', {}).items()}

        # Compare call counts
        new_paths = set(call_graph_b.keys()) - set(call_graph_a.keys())
        removed_paths = set(call_graph_a.keys()) - set(call_graph_b.keys())
        common_paths = set(call_graph_a.keys()) & set(call_graph_b.keys())

        # Calculate changes in call frequency
        frequency_changes = []
        for path in common_paths:
            count_a = call_graph_a[path]
            count_b = call_graph_b[path]
            change_pct = ((count_b - count_a) / count_a * 100) if count_a > 0 else float('inf')
            frequency_changes.append({
                'path': path,
                'before': count_a,
                'after': count_b,
                'change': count_b - count_a,
                'change_pct': change_pct
            })

        frequency_changes.sort(key=lambda x: abs(x['change']), reverse=True)

        return {
            'label_a': label_a,
            'label_b': label_b,
            'timestamp_a': trace_a['metadata']['timestamp'],
            'timestamp_b': trace_b['metadata']['timestamp'],
            'new_paths': list(new_paths),
            'removed_paths': list(removed_paths),
            'frequency_changes': frequency_changes[:20],  # Top 20 changes
            'functions_executed_a': len(trace_a.get('called_functions', [])),
            'functions_executed_b': len(trace_b.get('called_functions', [])),
            'total_calls_a': sum(call_graph_a.values()),
            'total_calls_b': sum(call_graph_b.values())
        }

    def get_time_series(self, label: str = "latest", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get time-series data for a specific trace label.

        Args:
            label: Trace label to get history for
            limit: Maximum number of historical traces to return

        Returns:
            List of trace summaries sorted by timestamp (newest first)
        """
        pattern = f"trace_{label}_*.json"
        traces = []

        for trace_file in self.trace_history_dir.glob(pattern):
            if "_latest" in trace_file.name:
                continue

            try:
                with open(trace_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})

                    # Convert call_graph for summary
                    call_graph = {tuple(json.loads(k)): v for k, v in data.get('call_graph', {}).items()}

                    traces.append({
                        'timestamp': metadata.get('timestamp', ''),
                        'total_calls': sum(call_graph.values()),
                        'unique_paths': len(call_graph),
                        'functions_executed': len(data.get('called_functions', [])),
                        'hottest_path': max(call_graph.items(), key=lambda x: x[1]) if call_graph else None
                    })
            except Exception:
                pass

        traces.sort(key=lambda x: x['timestamp'], reverse=True)
        return traces[:limit]


def extract_trace_data_for_webgl(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format trace data for WebGL visualization.

    Args:
        trace_data: Raw trace data from ExecutionTracer

    Returns:
        Dictionary formatted for HTML template injection
    """
    # Convert call_graph tuples to edge list with weights
    call_graph = trace_data.get('call_graph', {})
    edges = []

    for edge_key, count in call_graph.items():
        try:
            # Parse the JSON string key back to tuple
            caller, callee = json.loads(edge_key) if isinstance(edge_key, str) else edge_key
            edges.append({
                'from': caller,
                'to': callee,
                'weight': count,
                'heat': min(count / 100.0, 1.0)  # Normalize to 0-1 for color intensity
            })
        except (ValueError, TypeError):
            continue

    # Sort by weight (call count) descending
    edges.sort(key=lambda x: x['weight'], reverse=True)

    # Calculate node frequencies (how many times each function was called)
    node_frequencies = defaultdict(int)
    for edge in edges:
        node_frequencies[edge['from']] += edge['weight']
        node_frequencies[edge['to']] += edge['weight']

    # Create node list with heat values
    nodes = []
    for func, freq in node_frequencies.items():
        nodes.append({
            'id': func,
            'frequency': freq,
            'heat': min(freq / 500.0, 1.0)  # Normalize to 0-1
        })

    return {
        'enabled': True,
        'edges': edges[:200],  # Limit to top 200 hottest paths for performance
        'nodes': sorted(nodes, key=lambda x: x['frequency'], reverse=True)[:100],  # Top 100 nodes
        'total_calls': sum(call_graph.values()),
        'total_paths': len(edges),
        'hottest_path': edges[0] if edges else None
    }


def generate_comparison_report(comparison: Dict[str, Any], output_file: Path) -> None:
    """
    Generate a markdown report comparing two traces.

    Args:
        comparison: Comparison data from compare_traces()
        output_file: Path to output markdown file
    """
    md = [f"# Trace Comparison: {comparison['label_a']} vs {comparison['label_b']}\n"]

    md.append("## Summary\n")
    md.append(f"**Before ({comparison['label_a']}):** {comparison['timestamp_a']}")
    md.append(f"**After ({comparison['label_b']}):** {comparison['timestamp_b']}\n")

    md.append("### Execution Statistics\n")
    md.append("| Metric | Before | After | Change |")
    md.append("|--------|--------|-------|--------|")

    funcs_change = comparison['functions_executed_b'] - comparison['functions_executed_a']
    calls_change = comparison['total_calls_b'] - comparison['total_calls_a']

    md.append(f"| Functions Executed | {comparison['functions_executed_a']} | "
              f"{comparison['functions_executed_b']} | {funcs_change:+d} |")
    md.append(f"| Total Calls | {comparison['total_calls_a']:,} | "
              f"{comparison['total_calls_b']:,} | {calls_change:+,} |\n")

    # New paths
    if comparison['new_paths']:
        md.append("## New Call Paths\n")
        md.append(f"Found {len(comparison['new_paths'])} new execution paths:\n")
        for path in comparison['new_paths'][:10]:
            caller, callee = path
            md.append(f"- `{caller.split('::')[1]}()` → `{callee.split('::')[1]}()`")
        md.append("")

    # Removed paths
    if comparison['removed_paths']:
        md.append("## Removed Call Paths\n")
        md.append(f"Found {len(comparison['removed_paths'])} paths no longer executed:\n")
        for path in comparison['removed_paths'][:10]:
            caller, callee = path
            md.append(f"- `{caller.split('::')[1]}()` → `{callee.split('::')[1]}()`")
        md.append("")

    # Frequency changes
    if comparison['frequency_changes']:
        md.append("## Call Frequency Changes\n")
        md.append("Top changes in call frequency:\n")
        md.append("| Path | Before | After | Change | Change % |")
        md.append("|------|--------|-------|--------|----------|")

        for change in comparison['frequency_changes'][:20]:
            caller, callee = change['path']
            caller_short = caller.split('::')[1]
            callee_short = callee.split('::')[1]
            path_str = f"`{caller_short}()` → `{callee_short}()`"
            change_str = f"{change['change']:+,}"
            change_pct = f"{change['change_pct']:+.1f}%" if change['change_pct'] != float('inf') else "NEW"
            md.append(f"| {path_str} | {change['before']:,} | {change['after']:,} | {change_str} | {change_pct} |")

        md.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))


def generate_time_series_report(time_series: List[Dict[str, Any]], output_file: Path, label: str) -> None:
    """
    Generate a markdown report showing time-series trends.

    Args:
        time_series: Time-series data from get_time_series()
        output_file: Path to output markdown file
        label: Trace label for the report title
    """
    md = [f"# Execution Trace Time Series: {label}\n"]

    if not time_series:
        md.append("No historical trace data available.\n")
    else:
        md.append(f"Showing {len(time_series)} most recent traces:\n")

        md.append("## Execution Trends\n")
        md.append("| Timestamp | Total Calls | Unique Paths | Functions Executed |")
        md.append("|-----------|-------------|--------------|-------------------|")

        for trace in time_series:
            ts = trace['timestamp']
            calls = f"{trace['total_calls']:,}"
            paths = f"{trace['unique_paths']:,}"
            funcs = f"{trace['functions_executed']:,}"
            md.append(f"| {ts} | {calls} | {paths} | {funcs} |")

        md.append("\n## Hottest Path Over Time\n")
        for trace in time_series:
            if trace['hottest_path']:
                path, count = trace['hottest_path']
                caller, callee = path
                caller_short = caller.split('::')[1]
                callee_short = callee.split('::')[1]
                md.append(f"- **{trace['timestamp']}**: `{caller_short}()` → `{callee_short}()` ({count:,} calls)")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
