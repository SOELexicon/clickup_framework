# Hierarchy Command Test Suite

Automated tests for the `cum h` (hierarchy) command display features.

## Overview

This test suite validates all the hierarchy command improvements:
- Container hierarchy display (workspace/folder/list)
- Current task highlighting with 👉 emoji
- Attachment display with 📎 icon
- Tree line rendering with proper Unicode box-drawing characters
- Subtask hierarchy view with automatic parent fetching
- Tree line connectivity and alignment
- Status icons and emoji display
- Subtask completion counts

## Running the Tests

### Quick Run
```bash
python3 tests/test_hierarchy_display.py
```

### From Project Root
```bash
cd /home/user/clickup_framework
python3 tests/test_hierarchy_display.py
```

### Make Executable and Run
```bash
chmod +x tests/test_hierarchy_display.py
./tests/test_hierarchy_display.py
```

## Test Coverage

### Test 1: Parent Task Hierarchy
Tests the hierarchy view when viewing a parent task with subtasks:
- ✓ Container hierarchy shows folder
- ✓ Container hierarchy shows list
- ✓ Current task is highlighted with 👉
- ✓ Tree branch characters present (├─, └─)
- ✓ Tree vertical line characters present (│)
- ✓ Subtasks are displayed
- ✓ Vertical line continues through multi-line content
- ✓ Attachment display
- ✓ Tree lines connect siblings

### Test 2: Subtask Hierarchy View
Tests viewing a subtask (which requires fetching missing parents):
- ✓ Missing parent task is fetched
- ✓ Parent task is displayed in hierarchy
- ✓ Current subtask is highlighted with 👉
- ✓ Container hierarchy shows for subtask
- ✓ Subtask's children are displayed
- ✓ Tree indentation is correct
- ✓ No "No tasks found" error

### Test 3: Tree Line Alignment
Tests proper alignment of tree lines:
- ✓ Tree lines present with proper alignment
- ✓ Multi-line content aligned with vertical lines

### Test 4: Status and Emoji Display
Tests visual indicators:
- ✓ Status icons are displayed (⚙️, ⬜, ✓)
- ✓ Task type emoji displayed (📝)
- ✓ Date emoji displayed (📅)

### Test 5: Subtask Completion Counts
Tests completion tracking:
- ✓ Subtask completion counts displayed (X/Y complete)

## Test Output

### Success Output
```
============================================================
🧪 HIERARCHY COMMAND TEST SUITE
============================================================

🧪 Test 1: Parent Task Hierarchy (task 86c6g88be)
============================================================
  ✓ Container hierarchy shows folder
  ✓ Container hierarchy shows list
  ...

============================================================
📊 TEST SUMMARY
============================================================
✓ Passed: 23
✗ Failed: 0
Total: 23

✅ ALL TESTS PASSED!
```

### Failure Output
```
============================================================
📊 TEST SUMMARY
============================================================
✓ Passed: 20
✗ Failed: 3
Total: 23

❌ FAILURES:
  1. Pattern not found: ...
  2. Incorrect indentation: ...

❌ SOME TESTS FAILED
```

## Customizing Tests

### Testing Different Tasks

You can modify the test to use different task IDs by editing the default parameters:

```python
# In test_hierarchy_display.py
runner.test_parent_task_hierarchy(task_id="YOUR_TASK_ID")
runner.test_subtask_hierarchy(subtask_id="YOUR_SUBTASK_ID", parent_id="PARENT_ID")
```

### Adding New Tests

To add a new test, create a method in the `HierarchyTestRunner` class:

```python
def test_my_feature(self):
    """Test description."""
    print(f"\n🧪 Test X: My Feature")
    print("=" * 60)

    output = self.run_command("cum h <task_id>")

    self.assert_contains(
        output,
        r"pattern_to_match",
        "Test name"
    )
```

Then add it to `run_all_tests()`:

```python
def run_all_tests(self):
    self.test_parent_task_hierarchy()
    self.test_subtask_hierarchy()
    # ... existing tests ...
    self.test_my_feature()  # Add your test here
```

## Test Assertions

The test suite provides these assertion methods:

### `assert_contains(output, pattern, test_name)`
Verifies that a regex pattern exists in the output.

```python
self.assert_contains(
    output,
    r"👉.*\[86c6g88be\]",
    "Current task is highlighted"
)
```

### `assert_not_contains(output, pattern, test_name)`
Verifies that a regex pattern does NOT exist in the output.

```python
self.assert_not_contains(
    output,
    r"No tasks found",
    "No error message"
)
```

### `count_occurrences(output, pattern)`
Counts how many times a pattern appears.

```python
vertical_lines = self.count_occurrences(output, r"│")
if vertical_lines > 10:
    print(f"Found {vertical_lines} vertical lines")
```

## Continuous Integration

To integrate with CI/CD:

### GitHub Actions
```yaml
- name: Run Hierarchy Tests
  run: python3 tests/test_hierarchy_display.py
```

### GitLab CI
```yaml
test:hierarchy:
  script:
    - python3 tests/test_hierarchy_display.py
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

This allows CI systems to detect test failures automatically.

## Maintenance

When updating the hierarchy command:
1. Run the test suite to ensure no regressions
2. Update tests if new features are added
3. Add new test cases for new functionality
4. Document any changes in this README

## Related Files

- `clickup_framework/commands/hierarchy.py` - Main hierarchy command
- `clickup_framework/components/tree.py` - Tree rendering logic
- `clickup_framework/components/task_formatter.py` - Task formatting
- `clickup_framework/components/hierarchy.py` - Task organization
- `clickup_framework/components/options.py` - Format options

## Troubleshooting

### "No tasks found" during tests
- Ensure you have tasks in your ClickUp workspace
- Check that task IDs in the test are valid
- Verify API credentials are configured

### Pattern matching failures
- Check the actual output with: `cum h <task_id>`
- Compare with the regex pattern in the test
- Update patterns if output format has changed

### Permission errors
- Ensure the test file is executable: `chmod +x tests/test_hierarchy_display.py`
- Check that Python 3 is available: `python3 --version`

## Contributing

When contributing changes to the hierarchy command:
1. Ensure all existing tests pass
2. Add new tests for new features
3. Update this README if test behavior changes
4. Run tests before submitting PR

## License

Part of the ClickUp Framework project.
