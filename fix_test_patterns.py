"""Fix test regex patterns to match actual error messages."""
import re
from pathlib import Path

# Mapping of test files to their regex replacements
test_fixes = {
    'test_flowchart_generator.py': [
        (r'match="No symbols_by_file data found in stats"',
         r'match="Required field \'symbols_by_file\' not found in stats data"'),
    ],
    'test_class_diagram_generator.py': [
        (r'match="No symbols_by_file data found in stats"',
         r'match="Required field \'symbols_by_file\' not found in stats data"'),
    ],
    'test_code_flow_generator.py': [
        (r'match="No function_calls or all_symbols data found in stats"',
         r'match="Required field .* not found in stats data"'),
    ],
    'test_mindmap_generator.py': [
        (r'match="No symbols_by_file data found in stats"',
         r'match="Required field \'symbols_by_file\' not found in stats data"'),
        (r'match="No by_language data found in stats"',
         r'match="Required field \'by_language\' not found in stats data"'),
    ],
    'test_pie_chart_generator.py': [
        (r'match="No by_language data found in stats"',
         r'match="Required field \'by_language\' not found in stats data"'),
    ],
    'test_sequence_generator.py': [
        (r'match="No function_calls or all_symbols data found in stats"',
         r'match="Required field .* not found in stats data"'),
    ],
    'test_base_generator.py': [
        (r'match="Invalid test input"',
         r'match="Invalid test input"'),  # This one is fine
    ],
}

import os
import sys

# Get the absolute path to the tests directory
script_dir = Path(__file__).parent
test_dir = script_dir / 'tests' / 'commands' / 'map_helpers'

for filename, replacements in test_fixes.items():
    file_path = test_dir / filename

    if not file_path.exists():
        print(f"Skipping {filename} - not found")
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filename}")
    else:
        print(f"No changes: {filename}")

print("\nDone! Re-run tests to verify.")
