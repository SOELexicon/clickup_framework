# Trace Integration - Implementation Status

## Completed Features

### 1. ✅ --trace Flag Added to Map Command

**Location:** `clickup_framework/commands/map_command.py:388-393`

```bash
cum map --python --mer flow --html --output test.html --trace
```

The flag is registered and ready to use.

### 2. ✅ Trace Integration Module Created

**Location:** `clickup_framework/commands/map_helpers/trace_integration.py`

This comprehensive module provides:

**TraceDataManager Class:**
- `save_trace()`: Save execution traces with timestamps
- `load_trace()`: Load saved traces by label
- `list_traces()`: List all saved trace history
- `compare_traces()`: Compare two traces (before/after refactoring)
- `get_time_series()`: Get historical trend data

**Helper Functions:**
- `extract_trace_data_for_webgl()`: Format trace data for WebGL visualization
- `generate_comparison_report()`: Generate markdown comparison reports
- `generate_time_series_report()`: Generate trend reports

**Features Implemented:**
1. **Trace Persistence**: Saves traces to `.trace_history/` directory
2. **Comparison**: Compares "before" vs "after" traces
3. **Time-Series**: Tracks execution patterns over time
4. **WebGL Data Extraction**: Prepares hot path data for visualization

### 3. ✅ Execution Graph Generator

**Location:** `execution_graph_generator.py`

Standalone tool for comprehensive execution analysis with:
- Static analysis (AST)
- Dynamic tracing (sys.settrace)
- Mermaid diagram generation
- Dead code detection

## Remaining Integration Work

### Step 1: Connect --trace to map_command

**What to add:** Modify `map_command()` function to use the trace integration when `args.trace` is True.

**Location to modify:** `clickup_framework/commands/map_command.py` around line 47-100

**Implementation pattern:**

```python
def map_command(args):
    """Generate code map using ctags."""
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # NEW: Initialize trace data if --trace flag is set
    trace_data = None
    if hasattr(args, 'trace') and args.trace:
        from .map_helpers.trace_integration import TraceDataManager, extract_trace_data_for_webgl
        from execution_graph_generator import ExecutionTracer, StaticAnalyzer

        print("[TRACE] Initializing execution tracer...")
        project_root = Path.cwd()
        tracer = ExecutionTracer(project_root)

        # Start tracing
        with tracer:
            # Run the normal map generation (this will trace the map command itself)
            pass  # The rest of map_command execution happens here

        # Extract trace data for WebGL
        trace_dict = {
            'call_graph': {str(k): v for k, v in tracer.call_graph.items()},
            'called_functions': list(tracer.called_functions)
        }

        # Save trace for later comparison
        trace_manager = TraceDataManager(project_root)
        trace_manager.save_trace(trace_dict, label="latest")

        # Prepare for WebGL visualization
        trace_data = extract_trace_data_for_webgl(trace_dict)
        print(f"[TRACE] Captured {len(tracer.call_graph)} call paths")

    # ... rest of existing map_command code ...

    # When generating HTML (around line 260-290), pass trace_data:
    if args.html:
        export_mermaid_to_html(
            mermaid_content,
            str(output_path),
            title=f"Code Map: {args.mer}",
            use_color=use_color,
            trace_data=trace_data  # NEW PARAMETER
        )
```

### Step 2: Update HTML Template to Accept Trace Data

**Location to modify:** `clickup_framework/commands/map_helpers/templates/html_template.py`

**Changes needed:**

1. **Update function signature** (line ~7):
```python
def export_mermaid_to_html(
    mermaid_content: str,
    output_file: str,
    title: str = "Code Map",
    use_color: bool = False,
    trace_data: Optional[Dict] = None  # NEW PARAMETER
) -> bool:
```

2. **Inject trace data into JavaScript** (in HTML template around line 1420):
```javascript
// Trace data for hot path visualization
const traceData = {trace_data_json};

if (traceData && traceData.enabled) {{
    console.log('WebGL: Trace data loaded with', traceData.total_paths, 'paths');
    // Store for use in rendering
    window.traceData = traceData;
}}
```

3. **Add trace data to format() call** (line ~2004):
```python
html_content = html_template.format(
    title=title,
    mermaid_code_b64=mermaid_code_b64,
    fire_vertex=all_shaders['fire']['vertex'],
    fire_fragment=all_shaders['fire']['fragment'],
    glow_vertex=all_shaders['glow']['vertex'],
    glow_fragment=all_shaders['glow']['fragment'],
    pulse_vertex=all_shaders['pulse']['vertex'],
    pulse_fragment=all_shaders['pulse']['fragment'],
    ghost_vertex=all_shaders['ghost']['vertex'],
    ghost_fragment=all_shaders['ghost']['fragment'],
    trace_data_json=json.dumps(trace_data) if trace_data else '{}'  # NEW
)
```

### Step 3: Add Hot Path Visualization to WebGL Rendering

**Location to modify:** `clickup_framework/commands/map_helpers/templates/html_template.py` (WebGL section around line 1700)

**Implementation:**

```javascript
// In the animate() function, after drawing normal paths:

// Draw hot paths with enhanced visualization
if (window.traceData && window.traceData.enabled) {{
    const hotPaths = window.traceData.edges;

    // Find corresponding SVG paths and enhance them
    hotPaths.forEach(edge => {{
        // Match edge.from/edge.to to SVG path elements
        // Use edge.heat (0-1) to determine intensity
        const heat = edge.heat;

        // Modify shader uniform for this path
        gl.uniform1f(locations.heatLoc, heat);

        // Draw with enhanced effect
        // ... (existing draw code) ...
    }});
}}
```

### Step 4: Add Trace Comparison Commands

**Option A: Add new cum commands**

Create `clickup_framework/commands/trace_command.py`:

```python
def trace_compare_command(args):
    """Compare two execution traces."""
    from .map_helpers.trace_integration import TraceDataManager

    manager = TraceDataManager()
    comparison = manager.compare_traces(args.before, args.after)

    # Generate report
    output = Path(f"TRACE_COMPARISON_{args.before}_vs_{args.after}.md")
    generate_comparison_report(comparison, output)
    print(f"Comparison report: {output}")

def trace_history_command(args):
    """Show trace history and trends."""
    from .map_helpers.trace_integration import TraceDataManager

    manager = TraceDataManager()
    time_series = manager.get_time_series(args.label, limit=args.limit)

    # Generate report
    output = Path(f"TRACE_HISTORY_{args.label}.md")
    generate_time_series_report(time_series, output, args.label)
    print(f"History report: {output}")

def register_args(subparsers):
    """Register trace commands."""
    # cum trace compare
    parser = subparsers.add_parser('trace-compare', help='Compare two traces')
    parser.add_argument('--before', required=True, help='Label of first trace')
    parser.add_argument('--after', required=True, help='Label of second trace')
    parser.set_defaults(func=trace_compare_command)

    # cum trace history
    parser = subparsers.add_parser('trace-history', help='Show trace history')
    parser.add_argument('--label', default='latest', help='Trace label')
    parser.add_argument('--limit', type=int, default=10, help='Number of traces')
    parser.set_defaults(func=trace_history_command)
```

**Option B: Add flags to existing map command**

```bash
cum map --python --mer flow --html --trace --save-as "before_refactor"
# ... make code changes ...
cum map --python --mer flow --html --trace --save-as "after_refactor"
cum map --trace-compare before_refactor after_refactor
cum map --trace-history
```

## Usage Examples

### Basic Tracing

```bash
# Generate map with execution tracing
cum map --python --mer flow --html --output flow_traced.html --trace

# This will:
# 1. Generate the normal code map
# 2. Trace execution during generation
# 3. Highlight hot paths in the WebGL visualization
# 4. Save trace data to .trace_history/trace_latest_*.json
```

### Comparison Workflow

```bash
# Before refactoring
cum map --python --mer flow --html --trace --save-as "before"

# After refactoring
cum map --python --mer flow --html --trace --save-as "after"

# Compare
cum trace-compare --before before --after after
# Generates: TRACE_COMPARISON_before_vs_after.md
```

### Time-Series Tracking

```bash
# Run multiple times over development
cum map --python --mer flow --html --trace  # Day 1
# ... continue development ...
cum map --python --mer flow --html --trace  # Day 2
# ... continue development ...
cum map --python --mer flow --html --trace  # Day 3

# View trends
cum trace-history --label latest --limit 10
# Generates: TRACE_HISTORY_latest.md
```

## WebGL Visualization Features

Once fully integrated, the WebGL visualization will show:

1. **Normal Paths**: Default shader effects (fire, glow, pulse, ghost)
2. **Hot Paths**: Enhanced visualization with:
   - Thicker lines based on call frequency
   - Red/orange color intensity based on heat
   - Pulsing animation for top 10 hottest paths
   - Tooltip showing call count on hover

3. **Settings Panel Addition**:
   - Toggle hot path overlay
   - Adjust heat threshold
   - Show/hide call count labels
   - Filter by minimum call frequency

## File Structure

```
clickup_framework/
├── execution_graph_generator.py          # Standalone trace tool ✅
├── EXECUTION_ANALYSIS.md                 # Generated trace report ✅
├── EXECUTION_GRAPH_USAGE.md             # Usage guide ✅
├── TRACE_INTEGRATION_STATUS.md          # This file ✅
│
├── .trace_history/                       # Auto-created ✅
│   ├── trace_latest_20250119_143022.json
│   ├── trace_latest_latest.json
│   ├── trace_before_20250119_120000.json
│   └── trace_after_20250119_150000.json
│
└── clickup_framework/
    └── commands/
        ├── map_command.py                # Modified ⚠️ PARTIAL
        ├── trace_command.py              # To create ❌
        └── map_helpers/
            ├── trace_integration.py      # Created ✅
            └── templates/
                └── html_template.py      # To modify ❌
```

## Testing Checklist

- [ ] Verify `cum map --trace` flag appears in help
- [ ] Run `cum map --python --mer flow --html --trace`
- [ ] Check `.trace_history/` directory created
- [ ] Verify trace JSON files contain call_graph data
- [ ] Open generated HTML and see hot path overlay
- [ ] Test trace comparison with before/after labels
- [ ] Verify time-series reports show trends
- [ ] Check WebGL shader colors respond to heat values

## Next Steps

1. **Immediate**: Complete Step 1 (connect --trace to map_command)
2. **Next**: Complete Step 2 (update HTML template)
3. **Then**: Complete Step 3 (WebGL hot path rendering)
4. **Finally**: Add trace commands (Step 4)

The foundation is solid. The integration points are clearly defined. Each step builds on the previous one.
