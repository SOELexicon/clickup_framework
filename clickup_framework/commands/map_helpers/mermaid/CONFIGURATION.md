# Mermaid Generator Configuration

This document describes the configuration system for Mermaid diagram generators in the ClickUp Framework.

## Overview

All diagram generators now use a centralized configuration system that eliminates magic numbers and provides environment variable overrides. Configuration is managed through the `config.py` module.

## Configuration Classes

### CodeFlowConfig
Controls code execution flow diagram generation.

**Parameters:**
- `max_entry_points` (default: 10) - Maximum entry points to display
- `max_nodes` (default: 80) - Maximum total nodes in diagram
- `max_collection_depth` (default: 8) - Maximum recursion depth for collecting functions
- `tree_depth` (default: 3) - Directory tree scan depth
- `max_functions_per_class` (default: 50) - Maximum functions per class to show
- `max_folders` (default: 20) - Maximum folders to include
- `max_calls_per_function` (default: 5) - Maximum outgoing calls to display per function

**Environment Variables:**
```bash
MERMAID_CODE_FLOW_MAX_ENTRY_POINTS=10
MERMAID_CODE_FLOW_MAX_NODES=80
MERMAID_CODE_FLOW_MAX_COLLECTION_DEPTH=8
MERMAID_CODE_FLOW_TREE_DEPTH=3
MERMAID_CODE_FLOW_MAX_FUNCTIONS_PER_CLASS=50
MERMAID_CODE_FLOW_MAX_FOLDERS=20
MERMAID_CODE_FLOW_MAX_CALLS_PER_FUNCTION=5
```

### SequenceConfig
Controls sequence diagram generation showing execution flow.

**Parameters:**
- `max_entry_functions_fallback` (default: 3) - Functions to check if no entry patterns found
- `max_trace_depth_declaration` (default: 5) - Depth for participant declaration
- `max_trace_depth_actual` (default: 4) - Actual trace depth for diagram
- `max_calls_per_function` (default: 3) - Maximum calls to display per function
- `max_participants` (default: 10) - Maximum participants in sequence

**Environment Variables:**
```bash
MERMAID_SEQUENCE_MAX_ENTRY_FUNCTIONS_FALLBACK=3
MERMAID_SEQUENCE_MAX_TRACE_DEPTH_DECLARATION=5
MERMAID_SEQUENCE_MAX_TRACE_DEPTH_ACTUAL=4
MERMAID_SEQUENCE_MAX_CALLS_PER_FUNCTION=3
MERMAID_SEQUENCE_MAX_PARTICIPANTS=10
```

### ClassDiagramConfig
Controls class diagram generation showing OOP structure.

**Parameters:**
- `max_classes` (default: 20) - Maximum classes to include
- `max_methods_per_class` (default: 15) - Maximum methods per class
- `max_members_per_class` (default: 10) - Maximum member variables per class

**Environment Variables:**
```bash
MERMAID_CLASS_DIAGRAM_MAX_CLASSES=20
MERMAID_CLASS_DIAGRAM_MAX_METHODS_PER_CLASS=15
MERMAID_CLASS_DIAGRAM_MAX_MEMBERS_PER_CLASS=10
```

### FlowchartConfig
Controls flowchart diagram generation showing directory structure.

**Parameters:**
- `max_directories` (default: 10) - Maximum directories to show
- `max_files_per_directory` (default: 5) - Maximum files per directory
- `max_total_files` (default: 30) - Maximum total files in diagram
- `class_detail_threshold` (default: 5) - Show class details when count ≤ threshold

**Environment Variables:**
```bash
MERMAID_FLOWCHART_MAX_DIRECTORIES=10
MERMAID_FLOWCHART_MAX_FILES_PER_DIRECTORY=5
MERMAID_FLOWCHART_MAX_TOTAL_FILES=30
MERMAID_FLOWCHART_CLASS_DETAIL_THRESHOLD=5
```

### MindmapConfig
Controls mindmap diagram generation showing hierarchical structure.

**Parameters:**
- `max_languages` (default: 5) - Maximum languages to include
- `max_files_per_language` (default: 5) - Maximum files per language

**Environment Variables:**
```bash
MERMAID_MINDMAP_MAX_LANGUAGES=5
MERMAID_MINDMAP_MAX_FILES_PER_LANGUAGE=5
```

### ValidationConfig
Controls diagram validation thresholds.

**Parameters:**
- `max_nodes` (default: 200) - Maximum nodes for renderable diagram
- `max_edges` (default: 1000) - Maximum edges for renderable diagram
- `max_subgraphs` (default: 50) - Maximum subgraphs for renderable diagram
- `max_text_size` (default: 50000) - Maximum character count

**Environment Variables:**
```bash
MERMAID_VALIDATION_MAX_NODES=200
MERMAID_VALIDATION_MAX_EDGES=1000
MERMAID_VALIDATION_MAX_SUBGRAPHS=50
MERMAID_VALIDATION_MAX_TEXT_SIZE=50000
```

## Usage Examples

### Using Default Configuration

All generators automatically use default configuration values:

```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator

generator = CodeFlowGenerator(stats, theme='dark')
generator.generate(output_file='diagram.md')
# Uses all default values
```

### Overriding via Environment Variables

Set environment variables before running your application:

```bash
# Increase node limit for larger codebases
export MERMAID_CODE_FLOW_MAX_NODES=150
export MERMAID_CODE_FLOW_MAX_ENTRY_POINTS=20

# Run diagram generation
python -m clickup_framework.cli map --python --mer code_flow
```

### Programmatic Configuration

For advanced use cases, override the global configuration:

```python
from clickup_framework.commands.map_helpers.mermaid.config import (
    MermaidConfig,
    CodeFlowConfig,
    set_config
)

# Create custom configuration
custom_config = MermaidConfig(
    code_flow=CodeFlowConfig(
        max_nodes=150,
        max_entry_points=20,
        tree_depth=5
    )
)

# Set as global configuration
set_config(custom_config)

# All subsequent generator instances use this configuration
generator = CodeFlowGenerator(stats)
generator.generate(output_file='large_diagram.md')
```

### Temporary Configuration Override

Use context-specific configuration without affecting global state:

```python
from clickup_framework.commands.map_helpers.mermaid.config import (
    get_config,
    reset_config,
    set_config
)

# Save current config
original_config = get_config()

try:
    # Use custom config temporarily
    custom = MermaidConfig.from_env()
    custom.code_flow.max_nodes = 200
    set_config(custom)

    # Generate with custom config
    generator = CodeFlowGenerator(stats)
    generator.generate(output_file='large.md')
finally:
    # Restore original configuration
    set_config(original_config)
```

## Best Practices

1. **Use Environment Variables for Production**: Override configuration via environment variables for deployment flexibility without code changes.

2. **Keep Default Values Conservative**: Default values are tuned for good performance and readability. Increase limits only when needed.

3. **Test Configuration Changes**: After adjusting limits, verify diagrams still render correctly in your Mermaid viewer.

4. **Document Custom Values**: If setting non-default values, document why in your deployment configuration.

5. **Monitor Diagram Complexity**: Large diagrams may fail to render. Use validation thresholds to catch oversized diagrams early.

## Troubleshooting

### Diagram Too Large to Render

If you get "Too many nodes" validation errors:

1. Reduce `max_nodes` or `max_entry_points`
2. Increase `tree_depth` to group more functions into subgraphs
3. Reduce `max_calls_per_function` to simplify call graphs

### Missing Expected Content

If diagrams are missing expected functions or classes:

1. Increase `max_entry_points` to capture more entry functions
2. Increase `max_collection_depth` to traverse deeper call chains
3. Increase `max_functions_per_class` to show more methods

### Performance Issues

If generation is slow:

1. Reduce `max_collection_depth` to limit recursion
2. Reduce `max_nodes` to process fewer functions
3. Reduce `tree_depth` to scan fewer directory levels

## Configuration Architecture

The configuration system uses:

- **Dataclasses**: Type-safe configuration with default values
- **Environment Variables**: Runtime overrides without code changes
- **Singleton Pattern**: Single configuration instance shared across generators
- **Composition**: Specialized configs grouped under central `MermaidConfig`

All configuration is immutable after creation, ensuring thread-safe access across generators.

## Migration from Magic Numbers

This configuration system replaces 28 hard-coded magic numbers that were previously scattered across 6 generator files and 1 validator. All existing behavior is preserved with default values matching the original magic numbers.
