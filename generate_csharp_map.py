"""
Generate C# code map with language config integration.

This demonstrates the full integration of:
1. ctags for symbol discovery
2. Language configs for relationship extraction
3. Interactive HTML visualization with subgraph containment
"""

import json
import sys
from pathlib import Path
from clickup_framework.commands.map_helpers.language_configs import (
    LanguageConfigManager,
    RelationshipGraph
)
from clickup_framework.commands.map_helpers.templates import export_mermaid_to_html

def find_csharp_files(root_dir: Path, limit: int = 20):
    """Find C# files in the project."""
    csharp_files = []
    for cs_file in root_dir.rglob("*.cs"):
        if "obj" not in cs_file.parts and "bin" not in cs_file.parts:
            csharp_files.append(cs_file)
            if len(csharp_files) >= limit:
                break
    return csharp_files

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_csharp_map.py <project_directory>")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    if not project_dir.exists():
        print(f"Error: Directory not found: {project_dir}")
        sys.exit(1)

    print("=" * 80)
    print("C# Code Map Generator with Language Config Integration")
    print("=" * 80)
    print()

    # Load language config manager
    print("[1/5] Loading language configurations...")
    manager = LanguageConfigManager()
    csharp_config = manager.get_config("c#")

    if not csharp_config:
        print("Error: C# config not loaded")
        sys.exit(1)

    print("      [OK] C# language config loaded")
    print()

    # Find C# files
    print("[2/5] Scanning for C# files...")
    csharp_files = find_csharp_files(project_dir, limit=30)
    print(f"      [OK] Found {len(csharp_files)} C# files")
    print()

    # Extract relationships from all files
    print("[3/5] Extracting relationships from source code...")
    all_relationships = []
    files_processed = 0

    for cs_file in csharp_files:
        try:
            with open(cs_file, 'r', encoding='utf-8') as f:
                source_code = f.read()

            relationships = csharp_config.extract_relationships(source_code, str(cs_file))
            if relationships:
                all_relationships.extend(relationships)
                files_processed += 1
                print(f"      - {cs_file.name}: {len(relationships)} relationships")
        except Exception as e:
            print(f"      ! Skipped {cs_file.name}: {e}")

    print(f"      [OK] Extracted {len(all_relationships)} total relationships from {files_processed} files")
    print()

    # Build relationship graph
    print("[4/5] Building relationship graph...")
    graph = RelationshipGraph()
    for rel in all_relationships:
        graph.add_relationship(rel)

    print(f"      [OK] Graph contains {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print()

    # Generate Mermaid diagrams
    print("[5/5] Generating Mermaid diagrams...")

    # Generate with subgraph containment (C# mode)
    mermaid_code = graph.to_mermaid_class_diagram(csharp_config)

    print("      [OK] Subgraph containment diagram generated")
    print()

    # Export to HTML
    output_file = project_dir / "csharp-lang-config-map.html"
    title = f"C# Code Map - {project_dir.name} (Language Config Enhanced)"

    try:
        success = export_mermaid_to_html(
            mermaid_content=mermaid_code,
            output_file=str(output_file),
            title=title
        )

        if success:
            print("=" * 80)
            print(f"[SUCCESS] Interactive HTML generated:")
            print(f"  {output_file}")
            print("=" * 80)
            print()
            print("Key Features:")
            print("  - Inheritance relationships extracted from source code")
            print("  - Interface implementations detected")
            print("  - Composition relationships (private fields) identified")
            print("  - Subgraph containment: fields shown INSIDE their class")
            print("  - Interactive visualization with WebGL fire shader effects")
            print()

            # Show statistics
            inheritance_count = sum(1 for r in all_relationships if r.type == 'inheritance')
            interface_count = sum(1 for r in all_relationships if r.type == 'interface_implementation')
            composition_count = sum(1 for r in all_relationships if r.type == 'composition')

            print("Relationship Statistics:")
            print(f"  - Inheritance: {inheritance_count}")
            print(f"  - Interface Implementation: {interface_count}")
            print(f"  - Composition (fields): {composition_count}")
            print(f"  - Total: {len(all_relationships)}")
            print()

        else:
            print("Error: Failed to generate HTML")
            sys.exit(1)

    except Exception as e:
        print(f"Error generating HTML: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
