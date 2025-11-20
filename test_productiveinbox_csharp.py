"""Test C# subgraph containment on ProductiveInbox.Framework project."""

import sys
from pathlib import Path
from clickup_framework.commands.map_helpers.language_configs import (
    LanguageConfigManager,
    RelationshipGraph
)

def test_csharp_file(file_path: str, manager: LanguageConfigManager):
    """Test a single C# file with subgraph containment."""
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        print(f"Error: File not found: {file_path}")
        return

    # Read file content
    with open(file_path_obj, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Get C# config
    csharp_config = manager.get_config("c#")
    if not csharp_config:
        print("Error: C# config not loaded")
        return

    # Extract relationships
    relationships = csharp_config.extract_relationships(source_code, file_path)

    print("=" * 100)
    print(f"FILE: {file_path_obj.name}")
    print("=" * 100)
    print(f"\nExtracted {len(relationships)} relationships:\n")

    for i, rel in enumerate(relationships, 1):
        print(f"  {i:2}. [{rel.type:25}] {rel.source:30} -> {rel.target}")
        if rel.extra_info:
            field_name = rel.extra_info.get('field_name', '')
            if field_name:
                print(f"                                                  [field: {field_name}]")

    if not relationships:
        print("  (No relationships found)")
        return

    # Build graph
    graph = RelationshipGraph()
    for rel in relationships:
        graph.add_relationship(rel)

    # Generate flat diagram
    print("\n" + "-" * 100)
    print("FLAT CLASS DIAGRAM (traditional)")
    print("-" * 100)
    flat_diagram = graph.to_mermaid_class_diagram()
    print(flat_diagram)

    # Generate subgraph diagram
    print("\n" + "-" * 100)
    print("SUBGRAPH CONTAINMENT DIAGRAM (C# mode)")
    print("-" * 100)
    subgraph_diagram = graph.to_mermaid_class_diagram(csharp_config)
    print(subgraph_diagram)
    print()

def main():
    # Load language configs
    manager = LanguageConfigManager()

    print("\n" + "=" * 100)
    print("C# SUBGRAPH CONTAINMENT TEST - ProductiveInbox.Framework")
    print("=" * 100)
    print()

    # Test files from ProductiveInbox.Framework
    test_files = [
        r"E:\AI-UI\productiveinbox.framework\src\ProductiveInbox.Core\Caching\CachingService.cs",
        r"E:\AI-UI\productiveinbox.framework\src\ProductiveInbox.Core\Data\BaseProductiveInboxDbContext.cs",
        r"E:\AI-UI\productiveinbox.framework\src\ProductiveInbox.Core.Client\BaseClient.cs",
    ]

    for file_path in test_files:
        test_csharp_file(file_path, manager)

    print("=" * 100)
    print("KEY OBSERVATIONS:")
    print("=" * 100)
    print("""
In FLAT mode:
  - Composition relationships shown as external arrows (e.g., CachingService *-- IMemoryCache)
  - Can become cluttered with many dependencies

In SUBGRAPH mode:
  - Fields contained INSIDE their class definition
  - Only structural relationships (inheritance, interfaces) shown as external arrows
  - Cleaner, more hierarchical visualization
  - Matches OOP mental model: "thisvalue.field is part of thisvalue"
    """)

if __name__ == "__main__":
    main()
