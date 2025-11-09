# ClickUp JSON Manager Refactoring

This directory contains the modular refactoring of the ClickUp JSON Manager tool. The refactoring is designed to improve maintainability, extensibility, and testability through a clear separation of concerns.

## Module Structure

The refactored code is organized into the following modules:

### 1. Core Module (`/core`)
- Task entity management
- Relationship handling
- Status transition logic
- Validation mechanisms

### 2. Storage Module (`/storage`)
- JSON file operations with cross-platform compatibility
- Data serialization/deserialization
- File integrity verification
- Backup and recovery mechanisms
- Saved search persistence and management

### 3. CLI Module (`/cli`)
- Command pattern implementation
- Argument parsing
- Output formatting
- User interaction
- Saved search commands

### 4. Dashboard Module (`/dashboard`)
- Metrics calculation
- Data visualization
- Interactive navigation
- Filter management

### 5. Common Services Module (`/common`)
- Error handling and exceptions
- Logging framework
- Configuration management
- Dependency injection

## New Features

### Saved Searches
The refactored version includes a new saved search feature that allows users to:
- Save complex search queries for reuse
- Organize searches with categories and tags
- Execute saved searches to quickly filter tasks
- Import and export searches between team members

See the [Saved Search Guide](docs/user_guides/saved_search_guide.md) for details on how to use this feature.

## Refactoring Strategy

The refactoring follows these principles:

1. **Interface-First Design**: Define clear interfaces between modules
2. **Single Responsibility**: Each module has a focused responsibility
3. **Dependency Inversion**: Depend on abstractions, not implementations
4. **Incremental Migration**: Gradually move functionality to the new structure
5. **Backward Compatibility**: Maintain compatibility with existing data formats
6. **Test Coverage**: Ensure comprehensive test coverage for refactored code

## Implementation Phases

1. **Design Phase**
   - Define module interfaces and responsibilities
   - Create class hierarchies and relationships
   - Design integration patterns between modules

2. **Implementation Phase**
   - Implement core modules with tests
   - Refactor existing functionality into the new structure
   - Integrate modules through defined interfaces

3. **Testing Phase**
   - Unit tests for each module
   - Integration tests for module interactions
   - System tests for end-to-end functionality

4. **Documentation Phase**
   - Update API documentation
   - Create architecture diagrams
   - Update user guides

## Integration with Existing Code

During the transition period, the refactored code will be maintained in this separate directory structure. The existing functionality in the `src` directory will continue to be the primary codebase until the refactoring is complete and thoroughly tested.

## Running Tests

Tests for the refactored code are located in the `/tests` directory. To run the tests:

```bash
# Run all tests
pytest tests/

# Run tests for a specific module
pytest tests/test_core/
pytest tests/test_storage/
pytest tests/test_cli/
pytest tests/test_dashboard/
pytest tests/test_common/

# Run tests for saved search feature
pytest tests/**/test_saved_search*.py
```

## Documentation

Comprehensive documentation of the refactored architecture is available in:

- Module interfaces in each module's `__init__.py` file
- Class and method docstrings
- README files in each module directory
- Design documentation in the `/docs` directory
- User guides in the `/docs/user_guides` directory:
  - [Saved Search Guide](docs/user_guides/saved_search_guide.md)

## Usage Examples for cujmrefactor.sh

The `cujmrefactor.sh` script allows you to run commands against the refactored ClickUp JSON Manager implementation. Here are some examples:

### Basic Usage

```bash
# Display help information
./refactor/cujmrefactor.sh --help

# List tasks in a template
./refactor/cujmrefactor.sh list template.json

# Show details of a specific task
./refactor/cujmrefactor.sh show template.json "Task Name" --details

# Create a new task
./refactor/cujmrefactor.sh create-task template.json "New Task" --folder "Development" --list "Backlog" --status "to do" --priority 1
```

### Advanced Usage

```bash
# Update task status
./refactor/cujmrefactor.sh update-status template.json "Task Name" "in progress" --comment "Starting implementation"

# Generate dashboard
./refactor/cujmrefactor.sh dashboard template.json --output dashboard.html --format html

# Search for tasks
./refactor/cujmrefactor.sh search template.json "status == 'to do' and priority == 1"

# Manage relationships
./refactor/cujmrefactor.sh relationship add template.json "Task A" depends_on "Task B"
```

### Saved Search Management

```bash
# Save a frequently used search query
./refactor/cujmrefactor.sh saved-search save "high-priority-tasks" "priority == 'high'" --category "tasks"

# List all saved searches
./refactor/cujmrefactor.sh saved-search list

# List searches in a specific category
./refactor/cujmrefactor.sh saved-search list --category "tasks"

# Execute a saved search
./refactor/cujmrefactor.sh saved-search get "high-priority-tasks" --execute

# Update an existing saved search
./refactor/cujmrefactor.sh saved-search update "high-priority-tasks" --query "priority == 'high' and status != 'complete'"

# Delete a saved search
./refactor/cujmrefactor.sh saved-search delete "deprecated-search"

# Export searches for sharing with your team
./refactor/cujmrefactor.sh saved-search export --output team-searches.json

# Import searches from colleagues
./refactor/cujmrefactor.sh saved-search import team-searches.json
```

For more detailed information about the saved search feature, see the [Saved Search Guide](docs/user_guides/saved_search_guide.md).

### Comparing with Original Implementation

To compare the output with the original implementation:

```bash
# Original implementation
./cujm list template.json > original_output.txt

# Refactored implementation
./refactor/cujmrefactor.sh list template.json > refactored_output.txt

# Compare outputs
diff original_output.txt refactored_output.txt
``` 