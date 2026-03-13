# Generators API Reference

Complete API reference for all Mermaid diagram generators.

## Table of Contents

- [BaseGenerator](#basegenerator) (abstract base class)
- [FlowchartGenerator](#flowchartgenerator)
- [ClassDiagramGenerator](#classdiagramgenerator)
- [PieChartGenerator](#piechartgenerator)
- [MindmapGenerator](#mindmapgenerator)
- [SequenceGenerator](#sequencegenerator)
- [CodeFlowGenerator](#codeflowgenerator)
- [Common Exceptions](#exceptions)
- [Theme System](#theme-system)
- [Metadata Store](#metadata-store)

---

## BaseGenerator

Abstract base class for all diagram generators. Implements the template method pattern.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import BaseGenerator
```

### Constructor

```python
BaseGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

**Parameters:**
- `stats` (Dict): Statistics dictionary from `parse_tags_file()`
- `output_file` (str): Path to output markdown file
- `theme` (str | ColorScheme): Theme name ('dark' or 'light') or custom `ColorScheme` instance
- `metadata_store` (MetadataStore, optional): Custom metadata store instance

### Abstract Methods

Subclasses must implement:

```python
def validate_inputs(self, **kwargs) -> None:
    """Validate generator-specific input requirements."""
    pass

def generate_body(self, **kwargs) -> None:
    """Generate the diagram body content."""
    pass
```

### Public Methods

#### `generate(**kwargs) -> str`

Generate the complete diagram and write to file.

**Returns:** Path to the generated output file

**Raises:**
- `DataValidationError`: If required data is missing
- `FileOperationError`: If file operations fail
- `MermaidValidationError`: If generated diagram has invalid syntax

**Example:**
```python
generator = ConcreteGenerator(stats, 'output.md')
output_path = generator.generate()
print(f"Generated: {output_path}")
```

### Protected Methods

Available to subclasses:

#### `_add_diagram_declaration(declaration: str) -> None`

Add the diagram type declaration (e.g., `"graph TD"`, `"pie title ..."`).

#### `_add_line(line: str) -> None`

Add a single line to the diagram output.

#### `_add_lines(lines: List[str]) -> None`

Add multiple lines to the diagram output.

#### `_add_header() -> None`

Add markdown header and opening mermaid fence. Called automatically.

#### `_add_footer() -> None`

Add closing fence and statistics section. Called automatically. Can be overridden.

#### `_get_diagram_title() -> str`

Generate diagram title from output filename. Can be overridden.

#### `_validate_diagram() -> None`

Validate generated mermaid syntax. Called automatically.

#### `_write_files() -> None`

Write markdown and optional metadata files. Called automatically.

#### `_handle_error(error: Exception) -> None`

Handle and log generation errors. Called automatically.

### Attributes

- `stats` (Dict): The statistics dictionary
- `output_file` (str): Output file path
- `lines` (List[str]): Generated diagram lines
- `theme_manager` (ThemeManager): Theme management instance
- `metadata_store` (MetadataStore): Metadata storage instance

---

## FlowchartGenerator

Generate flowchart diagrams showing directory structure with symbol details.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator
```

### Constructor

```python
FlowchartGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `symbols_by_file`: Dict mapping file paths to lists of symbols
- `by_language`: Dict with language breakdown

### Configuration

Configurable via `get_config().FLOWCHART`:
- `max_depth`: Maximum directory depth to display (default: 3)
- `show_symbols`: Whether to show symbol details (default: True)

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator

stats = parse_tags_file('tags.txt')
generator = FlowchartGenerator(stats, 'diagram_flowchart.md', theme='dark')
output = generator.generate()
```

### Output Format

Generates a `graph TD` flowchart with:
- Directory nodes (styled as rounded rectangles)
- File nodes (styled as rectangles)
- Symbol nodes (functions, classes)
- Hierarchical relationships

---

## ClassDiagramGenerator

Generate UML class diagrams showing inheritance and relationships.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import ClassDiagramGenerator
```

### Constructor

```python
ClassDiagramGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `all_symbols`: Dict with all symbols including classes and their members
- `by_language`: Dict with language breakdown (for validation)

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import ClassDiagramGenerator

stats = parse_tags_file('tags.txt')
generator = ClassDiagramGenerator(stats, 'diagram_class.md', theme='light')
output = generator.generate()
```

### Output Format

Generates a `classDiagram` with:
- Class declarations
- Class members (attributes and methods)
- Inheritance relationships
- Composition relationships (when detectable)

---

## PieChartGenerator

Generate pie chart diagrams showing language distribution.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator
```

### Constructor

```python
PieChartGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `by_language`: Dict mapping language names to symbol counts by type

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator

stats = parse_tags_file('tags.txt')
generator = PieChartGenerator(stats, 'diagram_pie.md', theme='dark')
output = generator.generate()
```

### Output Format

Generates a `pie` chart with:
- Title: "Code Distribution by Language"
- Language slices with total symbol counts
- Alphabetically sorted languages

---

## MindmapGenerator

Generate hierarchical mindmap diagrams showing code organization.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import MindmapGenerator
```

### Constructor

```python
MindmapGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `symbols_by_file`: Dict mapping file paths to symbol lists
- `by_language`: Dict with language breakdown

### Behavior

- Displays top 5 languages (alphabetically sorted)
- Shows top 5 files per language (sorted by symbol count)
- Extracts filenames from paths automatically

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import MindmapGenerator

stats = parse_tags_file('tags.txt')
generator = MindmapGenerator(stats, 'diagram_mindmap.md', theme='dark')
output = generator.generate()
```

### Output Format

Generates a `mindmap` with:
- Root node: "Codebase"
- Language nodes (top 5)
- File nodes with symbol counts (top 5 per language)

---

## SequenceGenerator

Generate sequence diagrams showing execution flow and function calls.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator
```

### Constructor

```python
SequenceGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `function_calls`: Dict mapping function names to lists of called functions
- `all_symbols`: Dict with complete symbol information including scope

### Behavior

- Auto-detects entry points: `main`, `__init__`, `run`, `start`, `execute`
- Falls back to most-called functions if no entry patterns match
- Limits recursion depth to 4 levels
- Shows maximum 3 calls per function

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator

stats = parse_tags_file('tags.txt')
generator = SequenceGenerator(stats, 'diagram_sequence.md', theme='dark')
output = generator.generate()
```

### Output Format

Generates a `sequenceDiagram` with:
- Participant declarations (modules/classes)
- Call arrows (`->>`)
- Return arrows (`-->>`)
- Custom footer with entry point information

---

## CodeFlowGenerator

Generate code flow diagrams with hierarchical subgraphs showing call graphs.

### Import

```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator
```

### Constructor

```python
CodeFlowGenerator(stats: Dict, output_file: str, theme: Union[str, ColorScheme] = 'dark', metadata_store: Optional[MetadataStore] = None)
```

### Required Stats Keys

- `function_calls`: Dict mapping function names to lists of called functions
- `all_symbols`: Dict with complete symbol information

### Configuration

Configurable via `get_config().CODE_FLOW`:
- `max_nodes`: Maximum number of nodes to display (default: 80)
- `max_depth`: Maximum call depth to traverse (default: 8)
- `include_orphans`: Include functions with no callers (default: True)

### Metadata Export

This generator exports rich metadata including:
- Node details (id, label, type, scope)
- Call relationships (from, to, call_type)
- Hierarchy information (parent_module, depth)

### Example

```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator

stats = parse_tags_file('tags.txt')
generator = CodeFlowGenerator(stats, 'diagram_flow.md', theme='dark')
output = generator.generate()

# Export metadata
if generator.metadata_store.has_data():
    metadata_json = generator.metadata_store.export_json()
    with open('diagram_flow_metadata.json', 'w') as f:
        f.write(metadata_json)
```

### Output Format

Generates a `graph TD` with:
- Hierarchical subgraphs (modules/classes)
- Function nodes with styling
- Call relationships with arrows
- Orphan functions (if enabled)

---

## Exceptions

### DataValidationError

Raised when required statistics data is missing or invalid.

```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError

try:
    generator.generate()
except DataValidationError as e:
    print(f"Missing data: {e}")
    print(f"Required field: {e.field_name}")
    print(f"Generator type: {e.generator_type}")
```

**Attributes:**
- `field_name`: Name of the missing field
- `generator_type`: Type of generator that failed
- `stats_keys`: Available keys in stats dict

### FileOperationError

Raised when file writing or directory operations fail.

```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import FileOperationError

try:
    generator.generate()
except FileOperationError as e:
    print(f"File error: {e}")
    print(f"Operation: {e.operation}")
    print(f"File path: {e.file_path}")
```

**Attributes:**
- `operation`: Description of failed operation
- `file_path`: Path to the problematic file

### MermaidValidationError

Raised when generated mermaid syntax is invalid.

```python
from clickup_framework.commands.map_helpers.mermaid_validator import MermaidValidationError

try:
    generator.generate()
except MermaidValidationError as e:
    print(f"Invalid mermaid: {e}")
    print(f"Error details: {e.details}")
```

---

## Theme System

### ThemeManager

Manages color schemes for diagram styling.

```python
from clickup_framework.commands.map_helpers.mermaid.styling.theme_manager import ThemeManager

# Get current theme
theme_manager = ThemeManager(theme='dark')
print(theme_manager.current_theme)  # 'dark'

# Get node style
style = theme_manager.get_node_style('function')
print(style)  # 'fill:#4A90E2,stroke:#2E5C8A,color:#FFFFFF'

# Get color
color = theme_manager.get_color('function')
print(color)  # '#4A90E2'
```

### ColorScheme

Define custom color schemes.

```python
from clickup_framework.commands.map_helpers.mermaid.styling.color_schemes import ColorScheme

custom_scheme = ColorScheme(
    directory='#FF6B6B',
    file='#4ECDC4',
    function='#45B7D1',
    class_='#FFA07A',
    method='#96CEB4',
    variable='#FFEAA7'
)

generator = FlowchartGenerator(stats, output_file, theme=custom_scheme)
```

**Available node types:**
- `directory`: Directory nodes
- `file`: File nodes
- `function`: Function nodes
- `class_`: Class nodes
- `method`: Method nodes
- `variable`: Variable nodes
- `default`: Fallback color

---

## Metadata Store

### MetadataStore

Store and export diagram metadata in JSON format.

```python
from clickup_framework.commands.map_helpers.mermaid.core.metadata_store import MetadataStore

# Create store
store = MetadataStore()

# Add node metadata
store.add_node('node_1', {
    'label': 'MyFunction',
    'type': 'function',
    'scope': 'MyModule',
    'line_number': 42
})

# Check if data exists
if store.has_data():
    # Export as JSON string
    json_str = store.export_json()

    # Or get as dict
    data = store.get_all_metadata()
```

### Using Custom MetadataStore

```python
from clickup_framework.commands.map_helpers.mermaid.core.metadata_store import MetadataStore
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator

# Create custom store
custom_store = MetadataStore()

# Pass to generator
generator = CodeFlowGenerator(stats, output_file, metadata_store=custom_store)
generator.generate()

# Access metadata
metadata = custom_store.get_all_metadata()
for node_id, node_data in metadata.items():
    print(f"{node_id}: {node_data['label']}")
```

---

## Configuration System

### Accessing Configuration

```python
from clickup_framework.commands.map_helpers.mermaid.config.generator_config import get_config

config = get_config()

# Flowchart configuration
print(config.FLOWCHART.max_depth)        # 3
print(config.FLOWCHART.show_symbols)     # True

# Code flow configuration
print(config.CODE_FLOW.max_nodes)        # 80
print(config.CODE_FLOW.max_depth)        # 8
print(config.CODE_FLOW.include_orphans)  # True
```

### Configuration Values

**FlowchartConfig:**
- `max_depth` (int): Maximum directory depth (default: 3)
- `show_symbols` (bool): Show symbol details (default: True)

**CodeFlowConfig:**
- `max_nodes` (int): Maximum nodes in diagram (default: 80)
- `max_depth` (int): Maximum call depth (default: 8)
- `include_orphans` (bool): Include orphan functions (default: True)

---

## Usage Patterns

### Pattern 1: Basic Generation

```python
from clickup_framework.commands.map_helpers.mermaid.generators import PieChartGenerator

stats = parse_tags_file('tags.txt')
generator = PieChartGenerator(stats, 'output.md')
output_path = generator.generate()
```

### Pattern 2: Custom Theme

```python
from clickup_framework.commands.map_helpers.mermaid.generators import FlowchartGenerator
from clickup_framework.commands.map_helpers.mermaid.styling.color_schemes import ColorScheme

custom_colors = ColorScheme(
    directory='#FF6B6B',
    file='#4ECDC4',
    function='#45B7D1'
)

generator = FlowchartGenerator(stats, output_file, theme=custom_colors)
generator.generate()
```

### Pattern 3: Error Handling

```python
from clickup_framework.commands.map_helpers.mermaid.generators import SequenceGenerator
from clickup_framework.commands.map_helpers.mermaid.exceptions import (
    DataValidationError, FileOperationError, MermaidValidationError
)

try:
    generator = SequenceGenerator(stats, output_file)
    generator.generate()
except DataValidationError as e:
    print(f"Missing required data: {e.field_name}")
except FileOperationError as e:
    print(f"File operation failed: {e.operation}")
except MermaidValidationError as e:
    print(f"Invalid mermaid syntax: {e}")
```

### Pattern 4: Metadata Export

```python
from clickup_framework.commands.map_helpers.mermaid.generators import CodeFlowGenerator
import json

generator = CodeFlowGenerator(stats, 'diagram.md')
generator.generate()

if generator.metadata_store.has_data():
    metadata = json.loads(generator.metadata_store.export_json())
    print(f"Exported {len(metadata)} nodes")

    # Find entry points
    entry_points = [
        node_id for node_id, data in metadata.items()
        if data.get('label') in ['main', 'run', 'start']
    ]
    print(f"Entry points: {entry_points}")
```

### Pattern 5: Batch Generation

```python
from clickup_framework.commands.map_helpers.mermaid.generators import (
    FlowchartGenerator, ClassDiagramGenerator, PieChartGenerator
)

generators = [
    ('flowchart', FlowchartGenerator(stats, 'flowchart.md', theme='dark')),
    ('class', ClassDiagramGenerator(stats, 'class.md', theme='dark')),
    ('pie', PieChartGenerator(stats, 'pie.md', theme='dark'))
]

for name, generator in generators:
    try:
        result = generator.generate()
        print(f"✓ {name}: {result}")
    except Exception as e:
        print(f"✗ {name}: {e}")
```

---

## See Also

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Architecture overview and design patterns
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**: Migrating from legacy API
- **[ADDING_GENERATORS.md](ADDING_GENERATORS.md)**: Creating custom generators
- **[THEME_CUSTOMIZATION.md](THEME_CUSTOMIZATION.md)**: Theme system details
