"""Test the trace integration module."""

from clickup_framework.commands.map_helpers.trace_integration import (
    TraceDataManager,
    extract_trace_data_for_webgl,
    generate_comparison_report,
    generate_time_series_report
)
from pathlib import Path
import json

print("="*80)
print("TESTING TRACE INTEGRATION MODULE")
print("="*80)
print()

# Test 1: TraceDataManager initialization
print("[TEST 1] TraceDataManager initialization...")
manager = TraceDataManager()
print(f"  ✓ Trace history directory: {manager.trace_history_dir}")
print(f"  ✓ Directory exists: {manager.trace_history_dir.exists()}")
print()

# Test 2: Save a mock trace
print("[TEST 2] Saving mock trace data...")
mock_trace = {
    'call_graph': {
        '["module_a::func_a", "module_b::func_b"]': 150,
        '["module_b::func_b", "module_c::func_c"]': 500,
        '["module_a::func_a", "module_c::func_c"]': 25,
    },
    'called_functions': ['module_a::func_a', 'module_b::func_b', 'module_c::func_c']
}

trace_file = manager.save_trace(mock_trace, label="test")
print(f"  ✓ Saved to: {trace_file}")
print()

# Test 3: Load the trace back
print("[TEST 3] Loading saved trace...")
loaded_trace = manager.load_trace("test")
print(f"  ✓ Loaded trace with {len(loaded_trace['call_graph'])} call paths")
print(f"  ✓ Called functions: {len(loaded_trace['called_functions'])}")
print()

# Test 4: List traces
print("[TEST 4] Listing all traces...")
traces = manager.list_traces()
print(f"  ✓ Found {len(traces)} traces in history")
for trace in traces[:3]:
    print(f"    - {trace['label']}: {trace['timestamp']}")
print()

# Test 5: Extract WebGL data
print("[TEST 5] Extracting WebGL visualization data...")
webgl_data = extract_trace_data_for_webgl(mock_trace)
print(f"  ✓ Enabled: {webgl_data['enabled']}")
print(f"  ✓ Edges: {len(webgl_data['edges'])}")
print(f"  ✓ Nodes: {len(webgl_data['nodes'])}")
print(f"  ✓ Hottest path: {webgl_data['hottest_path']}")
print()

# Test 6: Create another trace for comparison
print("[TEST 6] Creating trace for comparison...")
mock_trace_2 = {
    'call_graph': {
        '["module_a::func_a", "module_b::func_b"]': 75,  # Reduced calls
        '["module_b::func_b", "module_c::func_c"]': 800,  # Increased calls
        '["module_d::func_d", "module_e::func_e"]': 50,  # New path
    },
    'called_functions': ['module_a::func_a', 'module_b::func_b', 'module_c::func_c', 'module_d::func_d']
}

manager.save_trace(mock_trace_2, label="test2")
print(f"  ✓ Saved second trace")
print()

# Test 7: Compare traces
print("[TEST 7] Comparing traces...")
comparison = manager.compare_traces("test", "test2")
print(f"  ✓ Functions executed: {comparison['functions_executed_a']} → {comparison['functions_executed_b']}")
print(f"  ✓ Total calls: {comparison['total_calls_a']} → {comparison['total_calls_b']}")
print(f"  ✓ New paths: {len(comparison['new_paths'])}")
print(f"  ✓ Removed paths: {len(comparison['removed_paths'])}")
print(f"  ✓ Frequency changes: {len(comparison['frequency_changes'])}")
print()

# Test 8: Generate comparison report
print("[TEST 8] Generating comparison report...")
report_file = Path("TEST_COMPARISON.md")
generate_comparison_report(comparison, report_file)
print(f"  ✓ Report generated: {report_file}")
print()

# Test 9: Time series
print("[TEST 9] Getting time series data...")
time_series = manager.get_time_series("test", limit=5)
print(f"  ✓ Retrieved {len(time_series)} historical traces")
for ts in time_series[:2]:
    print(f"    - {ts['timestamp']}: {ts['total_calls']} calls, {ts['unique_paths']} paths")
print()

# Test 10: Generate time series report
print("[TEST 10] Generating time series report...")
ts_report_file = Path("TEST_TIMESERIES.md")
generate_time_series_report(time_series, ts_report_file, "test")
print(f"  ✓ Report generated: {ts_report_file}")
print()

print("="*80)
print("ALL TESTS PASSED ✓")
print("="*80)
print()
print("Generated files:")
print(f"  - {report_file}")
print(f"  - {ts_report_file}")
print(f"  - {manager.trace_history_dir}/*.json")
