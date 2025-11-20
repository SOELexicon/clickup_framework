# Language-Specific Map Configurations

## Overview

This directory contains language-specific configurations that define how code should be mapped and visualized. Each language can have unique rules for inheritance, composition, relationships, and diagram layouts.

## Config Structure

```
language_configs/
├── README.md
├── base.yaml          # Default/fallback config
├── python.yaml        # Python-specific
├── csharp.yaml        # C#/.NET specific
├── javascript.yaml    # JS/TS specific
├── java.yaml          # Java specific
└── rust.yaml          # Rust specific
```

## Config File Format

Each config file defines:

1. **Language Metadata**
   - Name, extensions, primary patterns

2. **Relationship Types**
   - Inheritance (class A : BaseClass)
   - Implementation (class A : IInterface)
   - Composition (has-a)
   - Dependency (uses)

3. **Parsing Rules**
   - Regex patterns for extracting relationships
   - ctags field mappings
   - AST parsing hints

4. **Visualization Rules**
   - Diagram type preferences
   - Layout algorithms (hierarchical for OOP, flow for procedural)
   - Edge styling per relationship type
   - Grouping strategies

5. **Execution Tracing**
   - Hot path visualization style
   - Method call vs function call handling
   - Virtual method resolution

## Example: C# Config

```yaml
language:
  name: "C#"
  extensions: [".cs", ".csx"]
  paradigm: "object-oriented"

relationships:
  inheritance:
    pattern: "class\\s+(\\w+)\\s*:\\s*(\\w+)"
    style: "solid_arrow"
    color: "#00ff00"
    label: "inherits"

  interface:
    pattern: "class\\s+(\\w+)\\s*:\\s*I(\\w+)"
    style: "dashed_arrow"
    color: "#00ffff"
    label: "implements"

  composition:
    pattern: "private\\s+readonly\\s+(\\w+)\\s+(\\w+)"
    style: "diamond_arrow"
    color: "#ffff00"
    label: "has-a"

visualization:
  default_diagram: "class"

  class_diagram:
    layout: "hierarchical"  # Top-down inheritance tree
    group_by: "namespace"
    show_fields: true
    show_methods: true
    collapse_properties: false

  flow_diagram:
    layout: "force_directed"
    show_calls: true
    highlight_virtual: true  # Show virtual method calls differently

  execution_trace:
    highlight_inheritance_chain: true
    show_polymorphic_calls: true
    color_by_type: true

parsing:
  ctags_options:
    - "--fields=+iaSKz"
    - "--extras=+q"
    - "--c#-kinds=cimMnpg"  # classes, interfaces, methods, properties

  inheritance_field: "inherits"
  interface_field: "interfaces"

  additional_patterns:
    base_constructor: "\\s*:\\s*base\\("
    interface_constraint: "where\\s+\\w+\\s*:\\s*I\\w+"

hot_paths:
  method_call_pattern: "(\\w+)\\.(\\w+)\\("
  distinguish_static: true
  track_virtual_dispatch: true
```

## Usage

The system automatically selects the correct config based on file extensions:

```python
from language_configs import LanguageConfigManager

# Auto-detect language
config = LanguageConfigManager.get_config_for_file("MyClass.cs")

# Use config for parsing
relationships = config.extract_relationships(source_code)

# Apply visualization rules
diagram = config.generate_diagram(relationships, diagram_type="class")
```

## Extending for New Languages

To add support for a new language:

1. Create `language_configs/mylanguage.yaml`
2. Define language metadata and extensions
3. Add relationship extraction patterns
4. Configure visualization preferences
5. Test with sample code

The system falls back to `base.yaml` for undefined rules.
