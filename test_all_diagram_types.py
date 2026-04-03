"""Test HTML export with all diagram types."""
import subprocess
import os
from pathlib import Path

print("Testing HTML Export with All Diagram Types")
print("=" * 60)
print()

# All supported diagram types
diagram_types = ['pie', 'flowchart', 'class', 'mindmap', 'sequence', 'flow']

passed = 0
failed = 0

for diagram_type in diagram_types:
    output_file = f'test_{diagram_type}_html.html'
    print(f"Testing {diagram_type} diagram...")
    print(f"  Output: {output_file}")

    # Build command
    cmd = [
        'cum', 'map', '--python',
        '--mer', diagram_type,
        '--theme', 'dark',
        '--html',
        '--output', output_file
    ]

    try:
        # Run command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Check if file exists
            file_path = Path(output_file)
            if file_path.exists():
                file_size = file_path.stat().st_size
                if file_size > 1000:  # Should be at least 1KB
                    print(f"  [PASS] Created {output_file} ({file_size} bytes)")
                    passed += 1
                else:
                    print(f"  [FAIL] File too small: {file_size} bytes")
                    failed += 1
            else:
                print(f"  [FAIL] File not created")
                failed += 1
        else:
            print(f"  [FAIL] Command failed (exit code {result.returncode})")
            if result.stderr:
                error_lines = result.stderr.strip().split('\n')
                print(f"  Error: {error_lines[-1][:100]}")
            failed += 1

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Command timed out")
        failed += 1
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        failed += 1

    print()

print("=" * 60)
print(f"Results: {passed}/{len(diagram_types)} passed")
print()

if passed == len(diagram_types):
    print("[SUCCESS] All diagram types work with HTML export")
    exit(0)
else:
    print(f"[FAILURE] {failed} diagram types failed")
    exit(1)
