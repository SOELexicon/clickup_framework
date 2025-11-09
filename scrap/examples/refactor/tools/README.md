# Test Failure Task Creator

This tool automatically creates tasks in ClickUp for test failures. It parses test output and creates organized tasks with detailed information about each failure.

## Features

- Creates a main task for each test file with failures
- Creates subtasks for each individual test failure
- Includes detailed error messages and stack traces in task descriptions
- Groups related failures by test file
- Integrates with the unit test runner script

## Usage

### Option 1: Run with the Test Runner

The simplest way to use this tool is with the test runner script. Simply add the `--create-tasks` flag when running tests:

```bash
./refactor/run_unit_tests.sh --create-tasks
```

You can customize the task creation with additional options:

```bash
./refactor/run_unit_tests.sh --create-tasks --template path/to/template.json --folder "Testing" --list "Refactor Testing" --parent-task "Fix Test Failures"
```

### Option 2: Standalone Usage

You can also run the task creator script directly if you already have a file with test failure output:

```bash
python3 refactor/tools/test_failure_tasks.py path/to/failed_tests.txt
```

With custom options:

```bash
python3 refactor/tools/test_failure_tasks.py path/to/failed_tests.txt \
  --template path/to/template.json \
  --folder "Testing" \
  --list "Refactor Testing" \
  --parent "Parent Task Name"
```

## Options

The following options are available for both the test runner and the standalone script:

| Option       | Default                        | Description                                      |
|--------------|--------------------------------|--------------------------------------------------|
| --template   | 000_clickup_tasks_template.json| Path to the ClickUp JSON template file           |
| --folder     | Testing                        | Name of the folder to create tasks in            |
| --list       | Refactor Testing               | Name of the list to create tasks in              |
| --parent     | (none)                         | Name of a parent task to associate with          |

## Task Structure

The tool creates the following task structure:

```
"Fix test failures in test_file.py (2023-04-04)" (Task)
├── "Fix 1: test_something_failed (FAIL)" (Subtask)
├── "Fix 2: test_something_else_failed (FAIL)" (Subtask)
└── "Fix 3: test_another_method (ERROR)" (Subtask)
```

Each task includes:
- A descriptive title with test name and failure type
- The full error message and stack trace
- Tags for filtering and categorization

## Example

Running the test runner with task creation:

```bash
./refactor/run_unit_tests.sh --create-tasks
```

Output:
```
Running tests...
...
Creating ClickUp Tasks for Test Failures...
Executing: python3 /path/to/refactor/tools/test_failure_tasks.py /tmp/tmp.abc123/failed_tests.txt --template 000_clickup_tasks_template.json --folder "Testing" --list "Refactor Testing"

--- Task Creation Summary ---
Test files with failures: 2
Total failures: 7
Tasks created: 2
Subtasks created: 7
-----------------------------
Task creation completed successfully
```

## Workflow

The recommended workflow is:

1. Run tests with the `--create-tasks` flag
2. Review the created tasks in ClickUp
3. Assign developers to fix specific failures
4. Track progress through the ClickUp task dashboard
5. Run tests again to verify fixes

## Integration with Git

For best results, combine this feature with Git workflow:

1. Run tests with task creation
2. For each test file failure, create a branch named after the task ID
   - Example: `git checkout -b bugfix/tsk_12345-fix-test-failures`
3. Fix the failing tests
4. Commit and reference the task ID
   - Example: `git commit -m "fix: tsk_12345 Fix failing tests in module X"`
5. Create a pull request referencing the task
6. Update the task status in ClickUp as you progress 