# ClickUp JSON Manager Refactoring - Project Structure

This document outlines the modular structure for the refactored ClickUp JSON Manager codebase. The architecture focuses on:

- Clear separation of concerns
- Modular design with well-defined interfaces
- Testability and maintainability
- Extensibility for future features

## 1. Common Module

Foundation services and utilities used by all other modules.

```
refactor/common/
├── __init__.py
├── exceptions.py
├── config/
│   ├── __init__.py
│   └── config_manager.py
├── di/
│   ├── __init__.py
│   ├── container.py
│   └── service_provider.py
├── logging/
│   ├── __init__.py
│   └── logger.py
└── utils/
    ├── __init__.py
    ├── string_utils.py
    └── validation_utils.py
```

## 2. Core Module

Business logic and domain entities.

```
refactor/core/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── base_entity.py
│   ├── task_entity.py
│   ├── list_entity.py
│   ├── folder_entity.py
│   ├── space_entity.py
│   └── checklist_entity.py
├── repositories/
│   ├── __init__.py
│   ├── repository_interface.py
│   ├── task_repository.py
│   ├── list_repository.py
│   ├── folder_repository.py
│   └── space_repository.py
├── services/
│   ├── __init__.py
│   ├── task_service.py
│   ├── relationship_service.py
│   ├── status_service.py
│   ├── checklist_service.py
│   └── search_service.py
└── interfaces/
    ├── __init__.py
    └── core_manager.py
```

## 3. Storage Module

Data persistence and retrieval.

```
refactor/storage/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── storage_provider_interface.py
│   ├── json_storage_provider.py
│   └── memory_storage_provider.py
├── serialization/
│   ├── __init__.py
│   ├── serializer_interface.py
│   ├── json_serializer.py
│   └── entity_serializer.py
└── cache/
    ├── __init__.py
    ├── cache_manager.py
    └── caching_storage_provider.py
```

## 4. CLI Module

Command-line interface.

```
refactor/cli/
├── __init__.py
├── commands/
│   ├── __init__.py
│   ├── command_base.py
│   ├── task_commands.py
│   ├── list_commands.py
│   ├── folder_commands.py
│   ├── space_commands.py
│   ├── checklist_commands.py
│   ├── relationship_commands.py
│   ├── search_commands.py
│   └── dashboard_commands.py
├── middleware/
│   ├── __init__.py
│   ├── middleware_interface.py
│   ├── logging_middleware.py
│   └── error_handling_middleware.py
├── output/
│   ├── __init__.py
│   ├── output_formatter.py
│   ├── text_formatter.py
│   └── json_formatter.py
└── app.py
```

## 5. Dashboard Module

Reporting and visualization.

```
refactor/dashboard/
├── __init__.py
├── navigator/
│   ├── __init__.py
│   ├── navigation_context.py
│   └── navigator.py
├── metrics/
│   ├── __init__.py
│   ├── metrics_calculator.py
│   └── metrics_provider.py
├── views/
│   ├── __init__.py
│   ├── view_model.py
│   ├── summary_view.py
│   ├── detail_view.py
│   └── hierarchy_view.py
├── formatters/
│   ├── __init__.py
│   ├── formatter_interface.py
│   ├── console_formatter.py
│   └── html_formatter.py
└── interactive/
    ├── __init__.py
    ├── command_processor.py
    └── interactive_cli.py
```

## 6. Tests Module

Comprehensive test suite.

```
refactor/tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── common/
│   ├── core/
│   ├── storage/
│   ├── cli/
│   └── dashboard/
├── integration/
│   ├── __init__.py
│   ├── core_storage_tests.py
│   ├── cli_core_tests.py
│   └── dashboard_core_tests.py
└── fixtures/
    ├── __init__.py
    ├── test_data.py
    └── mock_providers.py
```

## 7. Main Application Entry Points

Application bootstrapping and public API.

```
refactor/
├── __init__.py
├── main.py              # Main application entry point
└── clickup_manager.py   # Public API
```

## 8. Plugins Module

Plugin system and extension points.

```
refactor/plugins/
├── __init__.py
├── base_plugin.py          # Plugin base class and interfaces
├── plugin_manager.py       # Plugin discovery and lifecycle management
├── hooks/
│   ├── __init__.py
│   ├── cli_hooks.py        # Hook points for CLI extensions
│   ├── dashboard_hooks.py  # Hook points for dashboard extensions
│   └── task_hooks.py       # Hook points for task operation extensions
└── examples/
    ├── __init__.py
    ├── github_integration/       # Example plugin for GitHub integration
    ├── time_tracking/            # Example plugin for time tracking
    └── custom_field_validators/  # Example plugin for field validation
```

## Module Responsibilities

### Common Module
- Exception handling and error hierarchy
- Logging services
- Configuration management
- Dependency injection container
- String and validation utilities

### Core Module
- Task and entity management
- Relationship handling between entities
- Status transitions and validations
- Checklist operations
- Search and filtering capabilities

### Storage Module
- Data persistence and retrieval
- JSON serialization and deserialization
- Cross-platform file handling
- Caching layer for performance

### CLI Module
- Command pattern implementation
- Argument parsing and validation
- Output formatting
- Middleware pipeline for cross-cutting concerns

### Dashboard Module
- Metrics calculation and aggregation
- View generation for different contexts
- Interactive navigation
- Visual formatting for console and HTML

### Tests Module
- Unit tests for all components
- Integration tests for module interactions
- Test fixtures and utilities

### Plugins Module
- Plugin interface definitions 
- Hook registration and management
- Plugin discovery and validation
- Plugin lifecycle management

## Implementation Guidelines

1. **Interface-First Design**: Define interfaces before implementations
2. **Dependency Injection**: Use DI for loosely coupled components
3. **Comprehensive Testing**: Ensure test coverage for each component
4. **Documentation**: Maintain clear documentation for all modules
5. **Cross-Platform Support**: Handle platform-specific differences
6. **Error Handling**: Consistent error handling across all modules
7. **Consistent Patterns**: Apply consistent design patterns

## Implementation Priorities

Based on dependencies and importance, the recommended implementation order is:

### 1. Common Module (Highest Priority)
- Provides foundation for all other modules
- Needs to be stable as other modules depend on it
- Required components:
  - Exception hierarchy
  - Logging framework
  - Configuration management
  - Dependency injection container
  - Core utilities

### 2. Storage Module
- Handles data persistence which is fundamental
- Isolates file operations and cross-platform concerns
- Required components:
  - Storage provider interface
  - JSON storage provider implementation
  - Serialization framework

### 3. Plugin System Foundation
- Early implementation needed to support extensibility
- Provides extension points for all other modules
- Required components:
  - Plugin base interfaces
  - Hook registration framework
  - Plugin discovery mechanism
  - Plugin lifecycle management

### 4. Core Module
- Contains the business logic and domain models
- Provides main services used by client modules
- Required components:
  - Entity models
  - Core repositories
  - Service implementations
  - Extension points for pluggable features

### 5. CLI Module
- Provides user-facing interface
- Depends on Core and Storage modules
- Required components:
  - Command framework
  - Core commands
  - Output formatting
  - Hook points for command extensions

### 6. Dashboard Module
- Visualization and reporting features
- Less critical than basic operations
- Required components:
  - Navigation components
  - Metrics
  - View generation
  - Extension points for custom visualizations

### 7. Example Plugins
- Demonstrate the plugin system capabilities
- Validate extension point design
- Required components:
  - At least one plugin for each category
  - Documentation on plugin development

### 8. Main Entry Points
- Connects all modules together
- Provides public API
- Bootstraps application
- Required components:
  - Application initialization
  - Plugin loading
  - Public API definition

## Migration Strategy

The migration from the monolithic to the modular architecture will follow an incremental approach:

### Phase 1: Foundation and Core Functionality
1. Implement the Common Module
2. Implement the Storage Module
3. Implement the Plugin System foundation
4. Implement core entities and interfaces (non-pluggable features only)

### Phase 2: Extension Points
1. Identify and implement extension points in the Core Module
2. Create the plugin registry and lifecycle management
3. Define hook interfaces for all pluggable functionality

### Phase 3: Client Modules with Extension Support
1. Implement CLI Module with core commands
2. Implement Dashboard Module with basic visualizations
3. Add extension points to both modules

### Phase 4: Example Plugins and Integration
1. Develop example plugins for each category
2. Connect all modules together
3. Create new entry points with plugin loading
4. Test and validate the entire system

### Migration Patterns

For each component being migrated:

1. **Extract and Transform Pattern**:
   - Identify functionality in existing code
   - Extract to a new module following new architecture
   - Transform interfaces to follow new patterns
   - Validate functionality matches original

2. **Side-by-Side Approach**:
   - New code lives in `refactor/` directory
   - Original code continues to function
   - Gradually shift functionality
   - Use feature toggles if needed

3. **Adapter Pattern for Compatibility**:
   - Create adapter classes to bridge old and new code
   - Allow incremental adoption of new modules
   - Example:
     ```python
     # Adapter between old and new APIs
     class LegacyTaskAdapter:
         def __init__(self, new_task_service):
             self.task_service = new_task_service
             
         def update_task_status(self, task_id, status, comment=None):
             # Convert to new API call
             return self.task_service.update_status(task_id, status, comment)
     ```

4. **Testing Strategy During Migration**:
   - Write tests that verify equivalent behavior
   - Create integration tests across old/new boundaries
   - Implement parallel testing of old and new implementations

## Data Flows

Key data flows in the system:

### 1. Task Creation Flow
```
CLI Command → Command Processor → Task Service → Task Repository → Storage Provider → File System
                                                     ↓
                                             Event Notification → Logging
```

### 2. Task Query/Search Flow
```
CLI Command → Command Processor → Search Service → Task Repository → Storage Provider → File System
                                        ↓
                            Response Formatting → Output Display
```

### 3. Dashboard Generation Flow
```
User Request → Dashboard Navigator → Metrics Service → Task Repository → Storage Provider → File System
                      ↓                    ↓
                 View Generation → Formatter → Output Display
```

### 4. Relationship Management Flow
```
CLI Command → Command Processor → Relationship Service → Task Repository → Storage Provider → File System
                                          ↓
                                Validation → Error Handling
```

## Entity Relationships

The core domain model and entity relationships:

```
                  ┌─────────┐
                  │  Space  │
                  └────┬────┘
                       │
                       │ contains
                       ▼
                  ┌─────────┐
                  │ Folder  │
                  └────┬────┘
                       │
                       │ contains
                       ▼
                   ┌───────┐
                   │  List  │
                   └───┬───┘
                       │
                       │ contains
                       ▼
        ┌─────────────┬─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌───────┐     ┌───────┐     ┌───────┐
    │ Task  ├────►│ Task  │◄────┤ Task  │
    └───┬───┘     └───┬───┘     └───┬───┘
        │             │             │
        │ contains    │ relates to  │ contains
        ▼             │             ▼
  ┌──────────┐        │       ┌──────────┐
  │ Checklist│        └─────► │ Subtask  │
  └─────┬────┘                └──────────┘
        │
        │ contains
        ▼
  ┌──────────┐
  │   Item   │
  └──────────┘
```

### Key Entity Relationships:

1. **Space-Folder-List Hierarchy**:
   - Spaces contain Folders
   - Folders contain Lists
   - Lists contain Tasks

2. **Task Relationships**:
   - Tasks can have subtasks (parent-child)
   - Tasks can have relationships to other tasks (depends_on, blocks, linked_to)
   - Tasks can have checklists
   - Checklists contain items

3. **Task Status Flow**:
   - Tasks have a defined status (to do, in progress, in review, complete)
   - Status transitions follow rules based on subtask completion and dependencies

4. **Entity Identification**:
   - All entities have a unique GUID
   - Entities can be referenced by GUID or human-readable name
   - GUIDs follow a pattern indicating entity type (tsk_, lst_, etc.)

5. **Task Types and Classification**:
   - Tasks have a `type` attribute defining their nature:
     - Standard task: Default task type for general work items
     - Milestone: Key project checkpoint or deliverable
     - Goal: Measurable objective with defined success criteria
     - Document: Documentation or knowledge base item
     - Project: Container for related work with multiple subtasks
     - Epic: Large work item that spans multiple iterations
   - Task types influence:
     - UI presentation
     - Available fields and properties
     - Workflow rules and validations
     - Reporting and dashboard display

6. **Tags and Categorization**:
   - Tasks can have multiple tags for flexible categorization
   - Tags support:
     - Filtering and searching
     - Grouping related tasks across lists/folders
     - Custom reporting dimensions
     - Workflow automation triggers
   - Tag implementation:
     - Stored as string array on task entity
     - Case-sensitive by default
     - Support hierarchical organization (e.g., "feature/ui", "feature/api")
     - Can be used in query expressions

7. **Custom Fields**:
   - Tasks support custom fields for domain-specific data
   - Field types include:
     - Text (single and multi-line)
     - Number (integer and decimal)
     - Date/Time
     - Dropdown (single and multi-select)
     - Checkbox
     - URL
     - User reference
   - Custom fields can be:
     - Required or optional
     - Validated against rules
     - Used in search queries and filters
     - Displayed in dashboard views 