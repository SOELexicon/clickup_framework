# ClickUp Framework Tests

Comprehensive test suite for the ClickUp Framework with API coverage tracking.

## Setup

### Prerequisites

1. **ClickUp API Token**: Set your ClickUp API token as an environment variable:
   ```bash
   export CLICKUP_API_TOKEN="your_api_token_here"
   ```

2. **Test Space**: Tests run in a specific ClickUp space to avoid affecting production data:
   - Default Space ID: `90158025753`
   - Default Team ID: `90151898946`
   - Space URL: https://app.clickup.com/90151898946/v/s/90158025753

3. **Configuration**: Edit `tests/test_config.py` to customize test settings:
   ```python
   TEST_SPACE_ID = "90158025753"  # Your test space ID
   TEST_TEAM_ID = "90151898946"   # Your workspace/team ID
   CLEANUP_AFTER_TESTS = True     # Auto-cleanup test data
   ```

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
python tests/run_tests.py --verbose

# Run with API coverage report
python tests/run_tests.py --verbose --coverage
```

### Run Specific Test Modules

```bash
# Test relationships only
python -m unittest tests.test_relationships

# Test client operations only
python -m unittest tests.test_client

# Run a specific test class
python -m unittest tests.test_relationships.TestTaskRelationships

# Run a specific test method
python -m unittest tests.test_relationships.TestTaskRelationships.test_01_add_dependency_waiting_on
```

### View API Coverage

```bash
# Show API coverage report without running tests
python tests/run_tests.py --coverage-only
```

## Test Structure

### Test Modules

- **`test_client.py`**: Core client API operations
  - Task CRUD operations
  - Comments and checklists
  - Custom fields
  - Lists, folders, spaces
  - Search functionality

- **`test_relationships.py`**: Task relationship functionality
  - Dependencies (blocking/waiting on)
  - Simple task links
  - TasksAPI convenience methods

- **`base_test.py`**: Base test infrastructure
  - Automatic test resource setup
  - Test folder and list creation
  - Cleanup after tests
  - Helper methods

### Test Configuration

**`test_config.py`** - Test settings:
- `TEST_SPACE_ID`: ClickUp space ID for tests
- `TEST_TEAM_ID`: ClickUp workspace/team ID
- `TEST_PREFIX`: Prefix for test resources (`[TEST]`)
- `CLEANUP_AFTER_TESTS`: Auto-delete test data (default: `True`)
- `VERBOSE_OUTPUT`: Print detailed test info (default: `True`)

### Coverage Tracking

**`coverage_tracker.py`** - API coverage analysis:
- Compares implemented client methods against `clickup-api-v2-reference.json`
- Shows covered and uncovered endpoints
- Groups by API category (Tasks, Lists, etc.)
- Calculates coverage percentage

## Test Flow

1. **Setup Phase** (`setUpClass`):
   - Create test folder in specified space
   - Create test list in folder
   - Track resource IDs for cleanup

2. **Test Execution**:
   - Each test creates necessary resources
   - Resources are tracked for cleanup
   - Tests are independent and can run in any order

3. **Cleanup Phase** (`tearDownClass`):
   - Delete all created tasks
   - Clean up test folder (if `CLEANUP_AFTER_TESTS=True`)
   - Print cleanup summary

## Writing New Tests

### Basic Test Template

```python
from tests.base_test import ClickUpTestCase


class TestMyFeature(ClickUpTestCase):
    """Test my feature."""

    def test_01_my_test(self):
        """Test description."""
        # Create test task
        task = self.create_test_task("My Test Task")

        # Perform operations
        result = self.client.some_operation(task["id"])

        # Assertions
        self.assertIn("expected_field", result)
        print(f"  ✓ Test passed")
```

### Helper Methods

- `self.create_test_task(name, **kwargs)`: Create and track a test task
- `self.track_task(task_id)`: Track a task for cleanup
- `self.track_list(list_id)`: Track a list for cleanup
- `self.track_folder(folder_id)`: Track a folder for cleanup

### Test Naming Convention

- Test methods should start with `test_`
- Number tests for execution order: `test_01_`, `test_02_`, etc.
- Use descriptive names: `test_01_create_task_with_dependencies`

## GitHub Actions

Tests run automatically on:
- Push to `main`, `master`, `develop`, or `claude/*` branches
- Pull requests to `main`, `master`, or `develop`
- Manual workflow dispatch

See `.github/workflows/test.yml` for configuration.

## API Coverage Report

The coverage tracker shows which ClickUp API v2 endpoints are implemented:

```
ClickUp Framework API Coverage Report
================================================================================
Total API Endpoints: 157
Covered by Client: 45
Not Covered: 112
Coverage: 28.7%

COVERED ENDPOINTS
================================================================================

Tasks:
  ✓ GET    /v2/task/{task_id}
    → get_task()
  ✓ POST   /v2/list/{list_id}/task
    → create_task()
  ...

UNCOVERED ENDPOINTS
================================================================================

Webhooks:
  ✗ POST   /v2/team/{team_id}/webhook
    Create Webhook
  ...
```

## Troubleshooting

### Tests Fail to Connect

- Verify `CLICKUP_API_TOKEN` is set correctly
- Check that token has access to the test space
- Ensure space ID and team ID are correct in `test_config.py`

### Cleanup Issues

- Set `CLEANUP_AFTER_TESTS = False` to inspect test data
- Manually delete test folder from ClickUp UI if needed
- Test resources are prefixed with `[TEST]` for easy identification

### Rate Limiting

- Tests include automatic rate limiting (100 req/min)
- If you hit rate limits, increase delays between tests
- Consider using a dedicated test workspace

## Best Practices

1. **Always use `create_test_task()`** instead of `client.create_task()` directly
2. **Track all created resources** for proper cleanup
3. **Use unique names** for test tasks to avoid conflicts
4. **Add print statements** to show test progress
5. **Test error cases** in addition to happy paths
6. **Group related tests** in the same test class
7. **Run coverage report** to identify gaps in API implementation

## Future Enhancements

- [ ] Add test data generators
- [ ] Implement parallel test execution
- [ ] Add performance benchmarks
- [ ] Generate HTML coverage reports
- [ ] Add integration with CI/CD pipelines
- [ ] Test docs API endpoints (v3)
- [ ] Add webhook testing infrastructure
