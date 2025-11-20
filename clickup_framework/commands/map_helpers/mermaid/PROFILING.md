# Performance Profiling Guide

This document describes the performance profiling system for Mermaid diagram generators in the ClickUp Framework.

## Overview

The profiling system provides detailed performance metrics for diagram generation:
- **Execution Time Tracking**: Measure time spent in each generation phase
- **Memory Usage Monitoring**: Track memory consumption throughout generation
- **Checkpoint System**: Record performance at specific points in the workflow
- **Flexible Reporting**: Output reports to console, files, or programmatically access them

Profiling is **disabled by default** for production use and can be enabled via environment variables or programmatic configuration.

## Quick Start

### Enable Profiling

**Via Environment Variables** (Recommended for Development):

```bash
# Enable profiling
export MERMAID_PROFILING_ENABLED=true

# Optional: Print reports to console
export MERMAID_PROFILING_PRINT_REPORTS=true

# Optional: Save reports to files
export MERMAID_PROFILING_SAVE_REPORTS=true
export MERMAID_PROFILING_OUTPUT_DIR=profiling_reports

# Generate diagrams as usual
cum map --python --mer code_flow --output diagram.md
```

**Via Programmatic Configuration**:

```python
from clickup_framework.commands.map_helpers.mermaid.config import (
    MermaidConfig,
    ProfilingConfig,
    set_config
)

# Create config with profiling enabled
config = MermaidConfig(
    profiling=ProfilingConfig(
        enabled=True,
        print_reports=True,
        save_reports=True,
        output_dir='my_profiles'
    )
)

# Set as global config
set_config(config)

# Generate diagrams - profiling will be active
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator

generator = CodeFlowGenerator(stats, output_file='diagram.md')
generator.generate()
```

## Configuration Options

### ProfilingConfig

All profiling behavior is controlled through `ProfilingConfig`:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `False` | Enable/disable profiling |
| `print_reports` | bool | `False` | Print reports to stdout after generation |
| `save_reports` | bool | `False` | Save reports to JSON files |
| `output_dir` | str | `'profiling_reports'` | Directory for saved report files |

### Environment Variables

| Variable | Values | Default |
|----------|--------|---------|
| `MERMAID_PROFILING_ENABLED` | `true`, `1`, `yes`, `on` / `false`, `0`, `no`, `off` | `false` |
| `MERMAID_PROFILING_PRINT_REPORTS` | Same as above | `false` |
| `MERMAID_PROFILING_SAVE_REPORTS` | Same as above | `false` |
| `MERMAID_PROFILING_OUTPUT_DIR` | Any directory path | `profiling_reports` |

## Performance Report Format

### Text Format

When `print_reports=True`, reports are printed to stdout:

```
======================================================================
Performance Profile: CodeFlowGenerator.generate
======================================================================
Total Time: 1.2345s
Memory Delta: +5.23 MB
Peak Memory: 245.67 MB

Checkpoints:
Name                           Elapsed      Delta        Memory
----------------------------------------------------------------------
start                            0.0000s     0.0000s     240.44MB
validation_complete              0.0123s     0.0123s     240.55MB
header_added                     0.0145s     0.0022s     240.56MB
body_generated                   1.1890s     1.1745s     245.32MB
footer_added                     1.2001s     0.0111s     245.45MB
diagram_validated                1.2123s     0.0122s     245.56MB
files_written                    1.2345s     0.0222s     245.67MB
end                              1.2345s     0.0000s     245.67MB

Metadata:
  generator: CodeFlowGenerator
  output_file: diagram.md
  total_symbols: 523
======================================================================
```

### JSON Format

When `save_reports=True`, reports are saved as JSON files:

```json
{
  "operation_name": "CodeFlowGenerator.generate",
  "total_time_seconds": 1.2345,
  "total_memory_delta_mb": 5.23,
  "peak_memory_mb": 245.67,
  "checkpoints": [
    {
      "name": "start",
      "elapsed_since_start": 0.0,
      "elapsed_since_prev": 0.0,
      "memory_mb": 240.44
    },
    {
      "name": "validation_complete",
      "elapsed_since_start": 0.0123,
      "elapsed_since_prev": 0.0123,
      "memory_mb": 240.55
    }
  ],
  "metadata": {
    "generator": "CodeFlowGenerator",
    "output_file": "diagram.md",
    "total_symbols": 523
  }
}
```

## Profiling Workflow

The profiling system automatically tracks the following checkpoints in the generation workflow:

1. **start** - Generation begins
2. **validation_complete** - Input validation finished
3. **header_added** - Diagram header added
4. **body_generated** - Diagram body generated (main work)
5. **footer_added** - Statistics footer added
6. **diagram_validated** - Mermaid syntax validation complete
7. **files_written** - Output files written to disk
8. **end** - Generation complete

Each checkpoint records:
- **Timestamp**: When the checkpoint occurred
- **Elapsed Since Start**: Total time from generation start
- **Elapsed Since Previous**: Time since last checkpoint (useful for identifying bottlenecks)
- **Memory Usage**: Current process memory in MB

## Accessing Profile Data Programmatically

### From Generator Instance

After generation, access the profile report directly:

```python
generator = CodeFlowGenerator(stats, output_file='diagram.md')
generator.generate()

# Access the profile report
if generator._profile_report:
    report = generator._profile_report
    print(f"Total time: {report.total_time}s")
    print(f"Memory delta: {report.total_memory_delta}MB")

    # Iterate checkpoints
    for checkpoint in report.checkpoints:
        print(f"{checkpoint.name}: {checkpoint.elapsed_since_start}s")
```

### From Global Registry

All profile reports are registered globally:

```python
from clickup_framework.commands.map_helpers.mermaid.profiling import (
    get_registered_profiles,
    clear_registry
)

# Generate multiple diagrams
generator1.generate()
generator2.generate()
generator3.generate()

# Access all profiles
profiles = get_registered_profiles()
for name, report in profiles.items():
    print(f"{name}: {report.total_time}s")

# Clear registry when done
clear_registry()
```

## Advanced Usage

### Custom Profiling in Extensions

You can use the profiling system in custom code:

```python
from clickup_framework.commands.map_helpers.mermaid.profiling import (
    PerformanceProfiler,
    profile_method,
    profile_section
)

# As context manager
with PerformanceProfiler('my_operation', enabled=True) as profiler:
    profiler.add_metadata('custom_key', 'custom_value')

    # Do work
    process_data()
    profiler.checkpoint('data_processed')

    # More work
    generate_output()
    profiler.checkpoint('output_generated')

# Get report
report = profiler.get_report()
print(report.format_text())

# As decorator
class MyGenerator:
    @profile_method('custom_generation')
    def generate(self):
        # Implementation
        pass

# Profile code sections
with PerformanceProfiler('parent_operation') as parent:
    with profile_section('initialization', parent):
        initialize()

    with profile_section('processing', parent):
        process()
```

### Temporary Profiling Override

Enable profiling for specific operations without changing global config:

```python
from clickup_framework.commands.map_helpers.mermaid.config import (
    get_config,
    set_config,
    ProfilingConfig,
    MermaidConfig
)

# Save original config
original_config = get_config()

try:
    # Create temporary config with profiling
    temp_config = MermaidConfig(
        profiling=ProfilingConfig(enabled=True, print_reports=True)
    )
    set_config(temp_config)

    # Generate with profiling
    generator.generate()
finally:
    # Restore original config
    set_config(original_config)
```

## Performance Optimization Tips

Use profiling to identify bottlenecks:

### 1. Long Body Generation

If `body_generated` checkpoint shows high elapsed time:
- Reduce `max_nodes` configuration
- Decrease `max_collection_depth` to limit recursion
- Reduce `max_calls_per_function` for simpler diagrams

### 2. High Memory Usage

If `peak_memory` or `total_memory_delta` are concerning:
- Reduce `max_entry_points` to process fewer functions
- Lower `max_functions_per_class` to limit per-class detail
- Decrease `tree_depth` to scan fewer directory levels

### 3. Slow Validation

If `diagram_validated` checkpoint is slow:
- Check for very large diagrams (many nodes/edges)
- Review validation thresholds in `ValidationConfig`
- Consider breaking into multiple smaller diagrams

## Integration with CI/CD

### Save Profiles for Analysis

```bash
# In CI pipeline
export MERMAID_PROFILING_ENABLED=true
export MERMAID_PROFILING_SAVE_REPORTS=true
export MERMAID_PROFILING_OUTPUT_DIR=ci_profiles

# Generate diagrams
cum map --python --mer code_flow

# Archive profiles
tar -czf profiles.tar.gz ci_profiles/
```

### Performance Regression Detection

```python
import json
from pathlib import Path

def check_performance_regression(current_profile, baseline_profile):
    """Compare current profile against baseline."""
    with open(current_profile) as f:
        current = json.load(f)
    with open(baseline_profile) as f:
        baseline = json.load(f)

    current_time = current['total_time_seconds']
    baseline_time = baseline['total_time_seconds']

    # Fail if >20% slower
    if current_time > baseline_time * 1.2:
        raise ValueError(
            f"Performance regression: {current_time}s vs baseline {baseline_time}s"
        )
```

## Troubleshooting

### Profiling Not Working

1. **Check if profiling is enabled**:
   ```python
   from clickup_framework.commands.map_helpers.mermaid.config import get_config
   print(get_config().profiling.enabled)
   ```

2. **Verify environment variables are set**:
   ```bash
   echo $MERMAID_PROFILING_ENABLED
   ```

3. **Check for errors in output**: Profiling failures are logged to stderr

### Reports Not Printing

Ensure `print_reports=True`:
```bash
export MERMAID_PROFILING_PRINT_REPORTS=true
```

### Reports Not Saving

1. Check `save_reports=True` and directory is writable
2. Look for warnings in stderr about file write failures
3. Verify `output_dir` path is correct:
   ```bash
   ls -la $MERMAID_PROFILING_OUTPUT_DIR
   ```

## Best Practices

1. **Keep Profiling Disabled in Production**: Profiling adds ~1-5% overhead. Only enable for development and performance analysis.

2. **Use Environment Variables**: Configure profiling via environment variables to avoid code changes between environments.

3. **Archive Profile Reports**: Save profile reports alongside generated diagrams for historical performance tracking.

4. **Compare Across Generators**: Profile different diagram types to understand their relative performance:
   ```bash
   # Profile all generator types
   for type in code_flow sequence class flowchart mindmap; do
       cum map --python --mer $type --output test_$type.md
   done
   ```

5. **Monitor Memory for Large Codebases**: Use profiling to tune configuration for codebases that push memory limits.

6. **Automate Performance Testing**: Integrate profiling into CI/CD to catch performance regressions early.

## See Also

- [CONFIGURATION.md](CONFIGURATION.md) - Configuration system documentation
- [base_generator.py](generators/base_generator.py) - BaseGenerator implementation with profiling
- [profiling.py](profiling.py) - Core profiling module source
- [test_profiling.py](../../../tests/test_profiling.py) - Profiling system tests
