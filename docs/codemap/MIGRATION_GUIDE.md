# Migration Guide: Procedural to Class-Based Generators

This guide helps you migrate from the legacy procedural API (`generate_mermaid_*` functions) to the new class-based generator API.

## Why Migrate?

The new class-based API provides:

- **Better extensibility**: Easily customize generation behavior by subclassing
- **Type safety**: Full type hints and IDE autocomplete support
- **Advanced features**: Theme management, metadata export, custom styling
- **Consistent patterns**: All generators follow the same template method pattern
- **Better error messages**: Detailed validation errors with context
- **Performance**: Optimized building strategies for complex diagrams

## Quick Migration Path

### Import Changes

**Old (deprecated):**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import (
    generate_mermaid_flowchart,
    generate_mermaid_class,
    generate_mermaid_pie,
    generate_mermaid_mindmap,
    generate_mermaid_sequence,
    generate_codeflow_mermaid
)
```

**New (recommended):**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import (
    FlowchartGenerator,
    ClassDiagramGenerator,
    PieChartGenerator,
    MindmapGenerator,
    SequenceGenerator,
    CodeFlowGenerator
)
```

### API Changes

The new API uses instantiation followed by a `generate()` call instead of direct function calls.

**General pattern:**
```python
# Old
generate_mermaid_TYPE(stats, output_file, theme='dark')

# New
generator = TYPEGenerator(stats, output_file, theme='dark')
generator.generate()
```

## Generator-by-Generator Migration

### 1. Flowchart Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_mermaid_flowchart

stats = parse_tags_file('tags.txt')
generate_mermaid_flowchart(stats, 'diagram_flowchart.md', theme='dark')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator

stats = parse_tags_file('tags.txt')
generator = FlowchartGenerator(stats, 'diagram_flowchart.md', theme='dark')
result_path = generator.generate()
print(f"Generated: {result_path}")
```

**Benefits:**
- Access to metadata export: `generator.metadata_store.export_json()`
- Theme customization: Pass custom `ColorScheme` instances
- Configuration: Adjust max_depth, show_symbols via `get_config()`

### 2. Class Diagram Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_mermaid_class

stats = parse_tags_file('tags.txt')
generate_mermaid_class(stats, 'diagram_class.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import ClassDiagramGenerator

stats = parse_tags_file('tags.txt')
generator = ClassDiagramGenerator(stats, 'diagram_class.md', theme='dark')
result_path = generator.generate()
```

**Benefits:**
- Theme support: Now accepts `theme` parameter (old API didn't)
- Consistent error handling: DataValidationError with detailed context
- Extensibility: Subclass to customize inheritance rendering

### 3. Pie Chart Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_mermaid_pie

stats = parse_tags_file('tags.txt')
generate_mermaid_pie(stats, 'diagram_pie.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator

stats = parse_tags_file('tags.txt')
generator = PieChartGenerator(stats, 'diagram_pie.md', theme='light')
result_path = generator.generate()
```

**Benefits:**
- Theme support: Control colors via theme parameter
- Better validation: Clear error messages for missing `by_language` data
- Title customization: Override `_get_diagram_title()` in subclass

### 4. Mindmap Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_mermaid_mindmap

stats = parse_tags_file('tags.txt')
generate_mermaid_mindmap(stats, 'diagram_mindmap.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import MindmapGenerator

stats = parse_tags_file('tags.txt')
generator = MindmapGenerator(stats, 'diagram_mindmap.md', theme='dark')
result_path = generator.generate()
```

**Benefits:**
- Configurable limits: Top 5 languages and files (customizable via subclassing)
- Sorted output: Alphabetical language ordering, symbol count file ordering
- Complex path handling: Automatic filename extraction from paths

### 5. Sequence Diagram Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_mermaid_sequence

stats = parse_tags_file('tags.txt')
generate_mermaid_sequence(stats, 'diagram_sequence.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator

stats = parse_tags_file('tags.txt')
generator = SequenceGenerator(stats, 'diagram_sequence.md', theme='dark')
result_path = generator.generate()
```

**Benefits:**
- Intelligent entry point detection: Finds `main`, `__init__`, `run` patterns
- Recursion depth control: Prevents infinite loops in circular call graphs
- Call limiting: Max 3 calls per function for readability
- Custom footer: Includes entry point and execution flow description

### 6. Code Flow Generator

**Old API:**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import generate_codeflow_mermaid

stats = parse_tags_file('tags.txt')
generate_codeflow_mermaid(stats, 'diagram_flow.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator

stats = parse_tags_file('tags.txt')
generator = CodeFlowGenerator(stats, 'diagram_flow.md', theme='dark')
result_path = generator.generate()
```

**Benefits:**
- Metadata export: Full call graph data in JSON format
- Node management: Automatic ID generation and deduplication
- Subgraph building: Hierarchical module organization
- Performance: Builder pattern for efficient construction
- Limits: Configurable max_nodes (80) and max_depth (8)

## Advanced Migration Patterns

### Pattern 1: Custom Theme

**Old API** (not possible):
```python
# No way to customize colors beyond 'dark' or 'light'
generate_mermaid_flowchart(stats, output_file, theme='dark')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.styling.color_schemes import ColorScheme
from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator

# Create custom color scheme
custom_colors = ColorScheme(
    directory='#FF6B6B',
    file='#4ECDC4',
    function='#45B7D1',
    class_='#FFA07A'
)

generator = FlowchartGenerator(stats, output_file, theme=custom_colors)
generator.generate()
```

### Pattern 2: Metadata Export

**Old API** (not possible):
```python
# No metadata export capability
generate_codeflow_mermaid(stats, output_file)
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator
import json

generator = CodeFlowGenerator(stats, 'diagram_flow.md')
generator.generate()

# Export metadata
if generator.metadata_store.has_data():
    metadata_json = generator.metadata_store.export_json()
    with open('diagram_flow_metadata.json', 'w') as f:
        f.write(metadata_json)

    # Or work with dict directly
    metadata_dict = json.loads(metadata_json)
    print(f"Exported {len(metadata_dict)} nodes")
```

### Pattern 3: Custom Validation

**Old API** (not possible):
```python
# No way to add custom validation
generate_mermaid_sequence(stats, output_file)
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError

class ValidatedSequenceGenerator(SequenceGenerator):
    def validate_inputs(self, **kwargs):
        # Run base validation
        super().validate_inputs(**kwargs)

        # Add custom validation
        if len(self.stats.get('function_calls', {})) < 5:
            raise DataValidationError(
                "Sequence diagram requires at least 5 function calls",
                generator_type='sequence',
                stats_keys=list(self.stats.keys())
            )

generator = ValidatedSequenceGenerator(stats, output_file)
generator.generate()
```

### Pattern 4: Custom Header/Footer

**Old API** (not possible):
```python
# No way to customize header or footer
generate_mermaid_mindmap(stats, output_file)
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import MindmapGenerator

class CustomMindmapGenerator(MindmapGenerator):
    def _get_diagram_title(self):
        """Custom title generation."""
        return f"Project Code Map - {self.stats.get('project_name', 'Unknown')}"

    def _add_footer(self):
        """Add custom footer information."""
        super()._add_footer()
        self._add_line("\n## Custom Metrics")
        self._add_line(f"- Complexity Score: {self._calculate_complexity()}")

    def _calculate_complexity(self):
        # Custom logic
        return len(self.stats.get('all_symbols', {})) * 1.5

generator = CustomMindmapGenerator(stats, output_file)
generator.generate()
```

### Pattern 5: Batch Generation

**Old API:**
```python
# Manual iteration
for diagram_type, generator_func in [
    ('flowchart', generate_mermaid_flowchart),
    ('class', generate_mermaid_class),
    ('pie', generate_mermaid_pie)
]:
    generator_func(stats, f'diagram_{diagram_type}.md')
```

**New API:**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import (
    FlowchartGenerator, ClassDiagramGenerator, PieChartGenerator
)

generators = [
    FlowchartGenerator(stats, 'diagram_flowchart.md', theme='dark'),
    ClassDiagramGenerator(stats, 'diagram_class.md', theme='dark'),
    PieChartGenerator(stats, 'diagram_pie.md', theme='dark')
]

results = []
for generator in generators:
    try:
        result_path = generator.generate()
        results.append(('success', result_path))
    except Exception as e:
        results.append(('error', str(e)))

# Print results
for status, info in results:
    print(f"[{status.upper()}] {info}")
```

## Breaking Changes

### No Breaking Changes in Core API

The legacy function-based API is **still available** for backward compatibility. It now wraps the new class-based API internally.

**However**, there are some differences to be aware of:

1. **Return Values**: Old API returned `None`, new API returns the output file path
   ```python
   # Old (no return value)
   generate_mermaid_flowchart(stats, output_file)

   # New (returns path)
   path = FlowchartGenerator(stats, output_file).generate()
   ```

2. **Error Types**: New API raises specific exception types
   ```python
   # Old (generic exceptions)
   try:
       generate_mermaid_pie(stats, output_file)
   except Exception as e:
       print(f"Error: {e}")

   # New (specific exceptions)
   from clickup_framework.commands.map_helpers.mermaid.exceptions import (
       DataValidationError, FileOperationError, MermaidValidationError
   )

   try:
       PieChartGenerator(stats, output_file).generate()
   except DataValidationError as e:
       print(f"Data validation failed: {e}")
   except FileOperationError as e:
       print(f"File operation failed: {e}")
   ```

3. **Theme Parameter**: `ClassDiagramGenerator` now supports `theme` parameter (old `generate_mermaid_class` did not)
   ```python
   # Old (no theme support)
   generate_mermaid_class(stats, output_file)

   # New (theme supported)
   ClassDiagramGenerator(stats, output_file, theme='light').generate()
   ```

## Configuration System

The new generators support centralized configuration via `get_config()`:

```python
from clickup_framework.commands.map_helpers.mermaid.config.generator_config import get_config

# Access configuration
config = get_config()

# Flowchart settings
print(f"Max depth: {config.FLOWCHART.max_depth}")
print(f"Show symbols: {config.FLOWCHART.show_symbols}")

# Code flow settings
print(f"Max nodes: {config.CODE_FLOW.max_nodes}")
print(f"Max depth: {config.CODE_FLOW.max_depth}")
```

You can customize configuration by modifying the config object before generator instantiation (for advanced users).

## Deprecation Timeline

- **Current Release**: Legacy API available with deprecation warnings
- **Next Major Release**: Legacy API will be removed
- **Migration Window**: 6 months minimum

To suppress deprecation warnings during migration:

```python
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='clickup_framework.commands.map_helpers.mermaid_generators')

# Your legacy code here
generate_mermaid_flowchart(stats, output_file)
```

## Migration Checklist

- [ ] Update imports to use new generator classes
- [ ] Replace function calls with class instantiation + `generate()` calls
- [ ] Update error handling to catch specific exception types
- [ ] Consider using metadata export for advanced use cases
- [ ] Explore theme customization options
- [ ] Test with existing stats dictionaries
- [ ] Update documentation and examples
- [ ] Review configuration options for your use case
- [ ] Remove deprecation warning suppressions after migration

## Need Help?

- **Architecture Overview**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: See [GENERATORS.md](GENERATORS.md)
- **Adding Custom Generators**: See [ADDING_GENERATORS.md](ADDING_GENERATORS.md)
- **Theme Customization**: See [THEME_CUSTOMIZATION.md](THEME_CUSTOMIZATION.md)
- **Issue Tracker**: Report bugs or request features on GitHub

## Example: Complete Migration

**Before (legacy API):**
```python
from clickup_framework.commands.map_helpers.mermaid_generators import (
    generate_mermaid_flowchart,
    generate_mermaid_class,
    generate_mermaid_pie
)

stats = parse_tags_file('tags.txt')

generate_mermaid_flowchart(stats, 'output/flowchart.md', theme='dark')
generate_mermaid_class(stats, 'output/class.md')
generate_mermaid_pie(stats, 'output/pie.md')
```

**After (new API):**
```python
from clickup_framework.commands.map_helpers.mermaid.generators import (
    FlowchartGenerator,
    ClassDiagramGenerator,
    PieChartGenerator
)

stats = parse_tags_file('tags.txt')

# Generate with consistent theme and error handling
generators = [
    ('flowchart', FlowchartGenerator(stats, 'output/flowchart.md', theme='dark')),
    ('class', ClassDiagramGenerator(stats, 'output/class.md', theme='dark')),
    ('pie', PieChartGenerator(stats, 'output/pie.md', theme='dark'))
]

for name, generator in generators:
    try:
        result = generator.generate()
        print(f"✓ Generated {name}: {result}")

        # Export metadata if available
        if generator.metadata_store.has_data():
            metadata_path = result.replace('.md', '_metadata.json')
            with open(metadata_path, 'w') as f:
                f.write(generator.metadata_store.export_json())
            print(f"  └─ Metadata: {metadata_path}")
    except Exception as e:
        print(f"✗ Failed to generate {name}: {e}")
```
