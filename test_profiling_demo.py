"""Demo script to test performance profiling."""

import json
from clickup_framework.commands.map_helpers.mermaid.config import (
    MermaidConfig,
    ProfilingConfig,
    set_config,
    reset_config
)
from clickup_framework.commands.map_helpers.mermaid.generators import (
    MindmapGenerator,
    ClassDiagramGenerator
)

# Load stats from existing tags file (JSONL format - take first line)
with open('.tags.json', 'r', encoding='utf-8') as f:
    first_line = f.readline()
    stats = json.loads(first_line)

print("=" * 80)
print("PROFILING DEMO: Testing Performance Profiling System")
print("=" * 80)
print()

# Configure profiling
config = MermaidConfig(
    profiling=ProfilingConfig(
        enabled=True,
        print_reports=True,
        save_reports=False
    )
)
set_config(config)

print("Testing MindmapGenerator with profiling enabled...")
print()

# Generate mindmap with profiling
generator1 = MindmapGenerator(
    stats=stats,
    output_file='test_profile_mindmap.md',
    theme='dark'
)
generator1.generate()

print("\nTesting ClassDiagramGenerator with profiling enabled...")
print()

# Generate class diagram with profiling
generator2 = ClassDiagramGenerator(
    stats=stats,
    output_file='test_profile_class.md',
    theme='dark'
)
generator2.generate()

print("\n" + "=" * 80)
print("PROFILING DEMO COMPLETE")
print("=" * 80)
print()
print("Summary:")
print(f"  MindmapGenerator: {generator1._profile_report.total_time:.4f}s")
print(f"  ClassDiagramGenerator: {generator2._profile_report.total_time:.4f}s")
print()

# Reset config
reset_config()
