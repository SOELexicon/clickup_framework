"""Test CLI HTML export integration."""
import subprocess
import os
from pathlib import Path

print("Testing CLI HTML Export Integration")
print("=" * 60)
print()

# Test cases: diagram type and expected output file
test_cases = [
    {
        'name': 'Pie Chart (Dark Theme)',
        'command': ['cum', 'map', '--python', '--mer', 'pie', '--theme', 'dark', '--html', '--output', 'test_cli_pie.html'],
        'expected_files': ['test_cli_pie.html', 'docs/codemap/diagram_pie.md']
    },
    {
        'name': 'Flowchart (Light Theme)',
        'command': ['cum', 'map', '--python', '--mer', 'flowchart', '--theme', 'light', '--html', '--output', 'test_cli_flowchart.html'],
        'expected_files': ['test_cli_flowchart.html', 'docs/codemap/diagram_flowchart.md']
    },
    {
        'name': 'Class Diagram (Default Theme)',
        'command': ['cum', 'map', '--python', '--mer', 'class', '--html', '--output', 'test_cli_class.html'],
        'expected_files': ['test_cli_class.html', 'docs/codemap/diagram_class.md']
    }
]

passed = 0
failed = 0

for test_case in test_cases:
    print(f"Test: {test_case['name']}")
    print(f"  Command: {' '.join(test_case['command'])}")

    # Run command
    try:
        result = subprocess.run(
            test_case['command'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Check if expected files exist
            all_files_exist = True
            for expected_file in test_case['expected_files']:
                file_path = Path(expected_file)
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"  [PASS] Created {expected_file} ({file_size} bytes)")
                else:
                    print(f"  [FAIL] Missing {expected_file}")
                    all_files_exist = False

            if all_files_exist:
                print(f"  [PASS] {test_case['name']}")
                passed += 1
            else:
                print(f"  [FAIL] {test_case['name']} - Missing files")
                failed += 1
        else:
            print(f"  [FAIL] Command failed with return code {result.returncode}")
            print(f"  Error output:")
            print(f"    {result.stderr[:200]}")
            failed += 1

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Command timed out")
        failed += 1
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        failed += 1

    print()

print("=" * 60)
print(f"Test Results: {passed} passed, {failed} failed")
print()

if passed == len(test_cases):
    print("[SUCCESS] All CLI HTML export tests passed")
    exit(0)
else:
    print(f"[FAILURE] {failed} out of {len(test_cases)} tests failed")
    exit(1)
