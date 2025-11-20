"""
Test script to trace the map command execution.
This demonstrates real-world usage of the execution tracer.
"""

from execution_graph_generator import trace_execution
from pathlib import Path
import sys

# Simulate running: cum map --python --mer flow --output test.md
class MockArgs:
    """Mock arguments for map command."""
    python = True
    csharp = False
    all_langs = False
    ignore_gitignore = False
    install = False
    mer = 'flow'
    output = None  # Don't export image
    format = None
    html = False  # Don't generate HTML (too slow for test)
    trace = False  # We're tracing from outside

def run_map_command():
    """Run the map command with tracing."""
    # Import inside function to avoid tracing imports
    from clickup_framework.commands.map_command import map_command

    args = MockArgs()

    print("="*80)
    print("TESTING: Tracing cum map --python --mer flow")
    print("="*80)
    print()

    try:
        map_command(args)
        return "success"
    except SystemExit as e:
        if e.code == 0:
            return "success"
        raise

if __name__ == "__main__":
    print("Starting execution trace of map command...")
    print()

    result, report = trace_execution(run_map_command)

    print()
    print("="*80)
    print("TRACE COMPLETE")
    print("="*80)
    print()
    print(f"Result: {result}")
    print()
    print("Generated files:")
    print("  - EXECUTION_ANALYSIS.md (full report)")
    print()
    print("Check the report to see:")
    print("  1. Module dependencies (high-level)")
    print("  2. Function execution flow (detailed)")
    print("  3. Dead code detection")
    print("  4. Hot paths (most frequently called)")
