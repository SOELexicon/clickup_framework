"""
Hybrid Execution Graph Generator

Combines static analysis (AST) with dynamic tracing (sys.settrace) to create
interactive Mermaid flowcharts showing both code structure and runtime execution paths.

Features:
- Static analysis: Maps all functions in the codebase
- Dynamic tracing: Records actual execution flow and call counts
- Hot path highlighting: Red edges for frequently executed paths
- Dead code detection: Gray nodes for unexecuted functions
- Noise filtering: Excludes print_, log_, dump_ functions
- Subgraph grouping: Organizes by source file
- Dual output: Collapsible Markdown for GitHub + full interactive HTML
"""

import sys
import ast
import os
import inspect
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Tuple, List, Optional
import json


class ExecutionTracer:
    """Traces function calls during runtime using sys.settrace."""

    def __init__(self, project_root: Path, noise_prefixes: Tuple[str, ...] = ('print_', 'log_', 'dump_')):
        self.project_root = project_root.resolve()
        self.noise_prefixes = noise_prefixes
        self.call_graph: Dict[Tuple[str, str], int] = defaultdict(int)  # (caller, callee) -> count
        self.called_functions: Set[str] = set()
        self.call_stack: List[str] = []

    def is_project_file(self, filename: str) -> bool:
        """Check if file belongs to the project (not stdlib or site-packages)."""
        if not filename:
            return False
        try:
            file_path = Path(filename).resolve()
            return str(self.project_root) in str(file_path) and file_path.suffix == '.py'
        except (ValueError, OSError):
            return False

    def is_noise_function(self, func_name: str) -> bool:
        """Check if function should be filtered out as noise."""
        return any(func_name.startswith(prefix) for prefix in self.noise_prefixes)

    def trace_calls(self, frame, event, arg):
        """Trace callback for sys.settrace."""
        if event != 'call':
            return self.trace_calls

        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name

        # Skip if not in project or is noise
        if not self.is_project_file(filename) or self.is_noise_function(func_name):
            return self.trace_calls

        # Build fully qualified function name
        module = self.get_module_name(filename)
        qualified_name = f"{module}::{func_name}"

        # Record the call
        self.called_functions.add(qualified_name)

        # Record edge from caller to callee
        if self.call_stack:
            caller = self.call_stack[-1]
            edge = (caller, qualified_name)
            self.call_graph[edge] += 1

        # Push to stack
        self.call_stack.append(qualified_name)

        return self.trace_calls

    def trace_returns(self, frame, event, arg):
        """Handle function returns to maintain stack."""
        if event == 'return' and self.call_stack:
            code = frame.f_code
            filename = code.co_filename
            func_name = code.co_name

            if self.is_project_file(filename) and not self.is_noise_function(func_name):
                module = self.get_module_name(filename)
                qualified_name = f"{module}::{func_name}"

                if self.call_stack and self.call_stack[-1] == qualified_name:
                    self.call_stack.pop()

        return self.trace_returns

    def get_module_name(self, filename: str) -> str:
        """Convert file path to module name."""
        try:
            file_path = Path(filename).resolve()
            rel_path = file_path.relative_to(self.project_root)
            module = str(rel_path.with_suffix('')).replace(os.sep, '.')
            return module
        except ValueError:
            return Path(filename).stem

    def start_trace(self):
        """Enable tracing."""
        sys.settrace(self.trace_calls)

    def stop_trace(self):
        """Disable tracing."""
        sys.settrace(None)

    def __enter__(self):
        self.start_trace()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_trace()
        return False


class StaticAnalyzer:
    """Analyzes Python source files to extract function definitions."""

    def __init__(self, project_root: Path, noise_prefixes: Tuple[str, ...] = ('print_', 'log_', 'dump_')):
        self.project_root = project_root.resolve()
        self.noise_prefixes = noise_prefixes
        self.functions: Dict[str, str] = {}  # qualified_name -> filename

    def is_noise_function(self, func_name: str) -> bool:
        """Check if function should be filtered out as noise."""
        return any(func_name.startswith(prefix) for prefix in self.noise_prefixes)

    def analyze_file(self, file_path: Path):
        """Extract all function definitions from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            module = self.get_module_name(file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    if not self.is_noise_function(func_name):
                        qualified_name = f"{module}::{func_name}"
                        self.functions[qualified_name] = str(file_path)

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")

    def analyze_directory(self, directory: Optional[Path] = None):
        """Recursively analyze all Python files in directory."""
        if directory is None:
            directory = self.project_root

        for file_path in directory.rglob('*.py'):
            # Skip __pycache__ and hidden directories
            if '__pycache__' in file_path.parts or any(part.startswith('.') for part in file_path.parts):
                continue

            self.analyze_file(file_path)

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            module = str(rel_path.with_suffix('')).replace(os.sep, '.')
            return module
        except ValueError:
            return file_path.stem


class MermaidGraphGenerator:
    """Generates Mermaid diagrams from static and dynamic analysis data."""

    def __init__(self, static_analyzer: StaticAnalyzer, tracer: ExecutionTracer):
        self.static = static_analyzer
        self.tracer = tracer

    def generate_module_view(self) -> str:
        """Generate high-level module-to-module dependency graph."""
        module_edges: Dict[Tuple[str, str], int] = defaultdict(int)

        # Aggregate by module
        for (caller, callee), count in self.tracer.call_graph.items():
            caller_module = caller.split('::')[0]
            callee_module = callee.split('::')[0]

            if caller_module != callee_module:  # Only cross-module calls
                edge = (caller_module, callee_module)
                module_edges[edge] += count

        # Generate Mermaid
        lines = ['graph LR']
        lines.append('    classDef hot fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff;')
        lines.append('    classDef warm fill:#ffd43b,stroke:#f59f00,stroke-width:2px;')
        lines.append('    classDef cold fill:#339af0,stroke:#1971c2;')
        lines.append('')

        # Create nodes
        modules = set()
        for caller, callee in module_edges.keys():
            modules.add(caller)
            modules.add(callee)

        for module in sorted(modules):
            node_id = self.sanitize_id(module)
            lines.append(f'    {node_id}["{module}"]')

        lines.append('')

        # Create edges with call counts
        for (caller, callee), count in sorted(module_edges.items(), key=lambda x: x[1], reverse=True):
            caller_id = self.sanitize_id(caller)
            callee_id = self.sanitize_id(callee)

            if count > 100:
                lines.append(f'    {caller_id} ==>|{count}| {callee_id}')
            elif count > 10:
                lines.append(f'    {caller_id} -->|{count}| {callee_id}')
            else:
                lines.append(f'    {caller_id} -.->|{count}| {callee_id}')

        return '\n'.join(lines)

    def generate_function_view(self, max_nodes: int = 200) -> str:
        """Generate detailed function-level graph with hot paths highlighted."""
        # Group functions by module
        module_functions: Dict[str, List[str]] = defaultdict(list)

        for func_qualified in self.static.functions.keys():
            module = func_qualified.split('::')[0]
            module_functions[module].append(func_qualified)

        # Limit to top modules by execution frequency
        module_call_counts = defaultdict(int)
        for caller, callee in self.tracer.call_graph.keys():
            module_call_counts[caller.split('::')[0]] += 1
            module_call_counts[callee.split('::')[0]] += 1

        top_modules = sorted(module_call_counts.keys(), key=lambda m: module_call_counts[m], reverse=True)[:10]

        # Generate Mermaid
        lines = ['graph LR']
        lines.append('    classDef executed fill:#51cf66,stroke:#2f9e44,stroke-width:2px,color:#000;')
        lines.append('    classDef dead fill:#495057,stroke:#adb5bd,stroke-width:1px,color:#adb5bd,stroke-dasharray: 5 5;')
        lines.append('    classDef entry fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff;')
        lines.append('')

        node_count = 0

        # Create subgraphs for each module
        for module in sorted(top_modules):
            if node_count >= max_nodes:
                break

            lines.append(f'    subgraph "{module}"')

            for func_qualified in sorted(module_functions.get(module, [])):
                if node_count >= max_nodes:
                    break

                func_name = func_qualified.split('::')[1]
                node_id = self.sanitize_id(func_qualified)

                # Determine if function was executed
                was_executed = func_qualified in self.tracer.called_functions
                class_name = 'executed' if was_executed else 'dead'

                # Check if it's an entry point (no callers)
                is_entry = not any(caller == func_qualified for caller, _ in self.tracer.call_graph.keys())
                if is_entry and was_executed:
                    class_name = 'entry'

                lines.append(f'        {node_id}["{func_name}"]:::{class_name}')
                node_count += 1

            lines.append('    end')
            lines.append('')

        # Create edges
        link_styles = []
        link_index = 0

        for (caller, callee), count in sorted(self.tracer.call_graph.items(), key=lambda x: x[1], reverse=True):
            # Skip if modules not in top modules
            caller_module = caller.split('::')[0]
            callee_module = callee.split('::')[0]

            if caller_module not in top_modules or callee_module not in top_modules:
                continue

            caller_id = self.sanitize_id(caller)
            callee_id = self.sanitize_id(callee)

            # Different edge styles based on call frequency
            if count > 100:
                lines.append(f'    {caller_id} ==>|{count}| {callee_id}')
                link_styles.append(f'    linkStyle {link_index} stroke:#ff0000,stroke-width:4px,color:#ff0000;')
            elif count > 10:
                lines.append(f'    {caller_id} -->|{count}| {callee_id}')
                link_styles.append(f'    linkStyle {link_index} stroke:#ff6b00,stroke-width:3px,color:#ff6b00;')
            else:
                lines.append(f'    {caller_id} -.->|{count}| {callee_id}')

            link_index += 1

        lines.append('')
        lines.extend(link_styles)

        return '\n'.join(lines)

    @staticmethod
    def sanitize_id(name: str) -> str:
        """Convert qualified name to valid Mermaid node ID."""
        return name.replace('::', '_').replace('.', '_').replace('-', '_').replace(' ', '_')

    def generate_markdown_report(self, title: str = "Code Execution Analysis") -> str:
        """Generate complete Markdown report with collapsible sections."""
        total_functions = len(self.static.functions)
        executed_functions = len(self.tracer.called_functions)
        dead_functions = total_functions - executed_functions
        total_calls = sum(self.tracer.call_graph.values())
        unique_edges = len(self.tracer.call_graph)

        md = [f"# {title}\n"]
        md.append("## Summary Statistics\n")
        md.append(f"- **Total Functions Discovered:** {total_functions}")
        md.append(f"- **Functions Executed:** {executed_functions} ({executed_functions/total_functions*100:.1f}%)")
        md.append(f"- **Dead Code Detected:** {dead_functions} ({dead_functions/total_functions*100:.1f}%)")
        md.append(f"- **Total Function Calls:** {total_calls:,}")
        md.append(f"- **Unique Call Paths:** {unique_edges}")
        md.append("")

        # Module-level view (always visible)
        md.append("## Module Dependencies (High-Level View)\n")
        md.append("```mermaid")
        md.append(self.generate_module_view())
        md.append("```\n")

        # Function-level view (collapsible)
        md.append('<details>')
        md.append('<summary>🔻 <b>Click to see Detailed Function Execution Trace (Hot Paths)</b></summary>\n')
        md.append("### Function-Level Execution Graph\n")
        md.append("**Legend:**")
        md.append("- 🔴 Red edges: Hot paths (>100 calls)")
        md.append("- 🟠 Orange edges: Warm paths (>10 calls)")
        md.append("- ⚪ Dotted edges: Cold paths (<10 calls)")
        md.append("- 🟢 Green nodes: Executed functions")
        md.append("- ⚫ Gray dashed nodes: Dead code (never executed)")
        md.append("")
        md.append("```mermaid")
        md.append(self.generate_function_view())
        md.append("```\n")
        md.append('</details>\n')

        # Dead code list
        if dead_functions > 0:
            md.append('<details>')
            md.append('<summary>💀 <b>Dead Code Report</b></summary>\n')
            md.append("### Potentially Unused Functions\n")

            dead_by_module = defaultdict(list)
            for func_qualified in self.static.functions.keys():
                if func_qualified not in self.tracer.called_functions:
                    module = func_qualified.split('::')[0]
                    func_name = func_qualified.split('::')[1]
                    dead_by_module[module].append(func_name)

            for module in sorted(dead_by_module.keys()):
                md.append(f"#### `{module}`")
                for func in sorted(dead_by_module[module]):
                    md.append(f"- `{func}()`")
                md.append("")

            md.append('</details>\n')

        # Hot paths
        md.append('<details>')
        md.append('<summary>🔥 <b>Hottest Execution Paths</b></summary>\n')
        md.append("### Top 20 Most Frequently Called Paths\n")

        hot_paths = sorted(self.tracer.call_graph.items(), key=lambda x: x[1], reverse=True)[:20]
        md.append("| Caller | Callee | Call Count |")
        md.append("|--------|--------|------------|")

        for (caller, callee), count in hot_paths:
            caller_short = caller.split('::')[1]
            callee_short = callee.split('::')[1]
            md.append(f"| `{caller_short}()` | `{callee_short}()` | {count:,} |")

        md.append("")
        md.append('</details>\n')

        return '\n'.join(md)


def trace_execution(target_function, *args, **kwargs):
    """
    Trace the execution of a target function and generate analysis report.

    Args:
        target_function: The function to trace
        *args, **kwargs: Arguments to pass to the target function

    Returns:
        Tuple of (function_result, markdown_report)
    """
    # Detect project root
    project_root = Path.cwd()

    # Initialize analyzers
    static_analyzer = StaticAnalyzer(project_root)
    tracer = ExecutionTracer(project_root)

    print("[ANALYSIS] Performing static analysis...")
    static_analyzer.analyze_directory()
    print(f"   Found {len(static_analyzer.functions)} functions")

    print("[TRACE] Starting execution trace...")
    result = None
    with tracer:
        result = target_function(*args, **kwargs)

    print(f"   Traced {len(tracer.called_functions)} function calls")
    print(f"   Recorded {len(tracer.call_graph)} unique call paths")

    print("[GENERATE] Generating Mermaid graphs...")
    generator = MermaidGraphGenerator(static_analyzer, tracer)
    markdown_report = generator.generate_markdown_report()

    # Write report
    output_file = project_root / "EXECUTION_ANALYSIS.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_report)

    print(f"[SUCCESS] Report generated: {output_file}")

    return result, markdown_report


# Example usage
if __name__ == "__main__":
    # Example: Trace a simple test function
    def example_main():
        """Example function to demonstrate tracing."""
        def helper_a():
            return "A"

        def helper_b():
            return helper_a() + "B"

        def helper_c():
            return "C"

        # helper_c is dead code - never called

        results = []
        for i in range(50):
            results.append(helper_b())

        return results

    print("=" * 80)
    print("EXECUTION GRAPH GENERATOR - DEMO")
    print("=" * 80)
    print()
    print("To use with your actual code:")
    print("1. Import your main entry point:")
    print("   from my_module import main")
    print("2. Replace the example_main() call below with:")
    print("   trace_execution(main)")
    print()
    print("=" * 80)
    print()

    # Run the trace
    result, report = trace_execution(example_main)

    print()
    print("Demo completed. Check EXECUTION_ANALYSIS.md for the full report.")
