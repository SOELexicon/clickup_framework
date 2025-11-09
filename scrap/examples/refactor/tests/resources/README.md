# Test Resources

This directory contains resources used by the test suite for the ClickUp JSON Manager.

## Contents

- `sample_template.json`: Basic template file used for simple tests
- `complex_template.json`: Complex template file with multiple entities and relationships

## Usage

Test resources can be accessed using the utility functions in `tests/utils/test_helpers.py`:

```python
from refactor.tests.utils.test_helpers import get_test_resources_dir, get_sample_template_path

# Get the path to the resources directory
resources_dir = get_test_resources_dir()

# Get the path to the sample template file
sample_template_path = get_sample_template_path()
```

## Creating Test Data

Test data fixtures can be created using the `TestFixtureFactory` class:

```python
from refactor.tests.utils.test_helpers import TestFixtureFactory

# Create a task
task = TestFixtureFactory.create_task(
    name="Test Task",
    status="in progress",
    priority=1
)

# Create a space
space = TestFixtureFactory.create_space(
    name="Test Space"
)

# Create a folder
folder = TestFixtureFactory.create_folder(
    name="Test Folder",
    space_id=space["id"]
)

# Create a list
list_entity = TestFixtureFactory.create_list(
    name="Test List",
    folder_id=folder["id"]
)
```

## Test Files

For temporary test files, use the `TestFileManager` class:

```python
from refactor.tests.utils.test_helpers import TestFileManager

# Create a temporary directory
temp_dir = TestFileManager.create_temp_dir()

# Create a temporary file
temp_file = TestFileManager.create_temp_file(content='{"key": "value"}')

# Create a test template file
template_path = TestFileManager.create_test_template()

# Clean up when done
TestFileManager.cleanup_temp_file(temp_file)
TestFileManager.cleanup_temp_dir(temp_dir)
```

## Adding New Resources

When adding new resources to this directory:

1. Make sure the resource is needed by multiple tests
2. Document the resource in this README
3. Add utility functions to access the resource if needed
4. Consider using fixtures instead for test-specific resources 