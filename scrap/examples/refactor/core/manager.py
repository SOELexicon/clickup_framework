"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)
    - tsk_2d5e7f90 - Improve Service Layer (related)

Used By:
    - CLI Commands: Main entry point for command implementation
    - Web API: Core backend for REST endpoints
    - Dashboard: Data provider for metrics and visualizations
    - Tests: Central fixture for integration testing

Purpose:
    Provides a centralized facade for accessing all core functionality of the application,
    managing repositories, services, and their dependencies while offering a simplified
    interface for client code to interact with the business logic layer.

Requirements:
    - Must maintain a clean separation between client code and implementation details
    - Must initialize and configure all dependencies correctly
    - Must coordinate operations that span multiple services
    - Must provide consistent error handling across all operations
    - CRITICAL: Must maintain backward compatibility for public methods
    - CRITICAL: Changes here affect the entire application

Changes:
    - v1: Initial implementation with basic task management
    - v2: Added relationship management functionality
    - v3: Enhanced with comprehensive error handling
    - v4: Added dedicated services for specialized operations
    - v5: Improved documentation and interface consistency

Lessons Learned:
    - Facade pattern simplifies client code but must be kept focused
    - Dependency management is critical for maintaining testability
    - Service coordination requires careful handling of transaction boundaries
    - Method signatures should be designed for future extensibility
"""
from typing import Optional, List, Dict, Any
from pathlib import Path

from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.services.task_service import TaskService
from refactor.core.entities.task import Task


class CoreManager:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/manager.py
    dohcount: 1
    
    Used By:
        - CLI Module: Main entry point for all command operations
        - Web API: Central controller for REST endpoints
        - Dashboard: Data provider for visualization components
        - Integration Tests: Main fixture for testing scenarios
    
    Purpose:
        Acts as a high-level facade that provides centralized access to all core
        functionality, managing the initialization and coordination of repositories
        and services while presenting a simplified, cohesive API to client code.
    
    Requirements:
        - Must initialize all repositories and services with correct dependencies
        - Must delegate operations to appropriate services
        - Must provide consistent error handling patterns
        - Must maintain clear separation of concerns
        - CRITICAL: Must not expose internal implementation details
        - CRITICAL: All public methods must be thoroughly documented
    
    Changes:
        - v1: Initial implementation with basic task management
        - v2: Added support for relationships and comments
        - v3: Enhanced error propagation and handling
        - v4: Improved method signatures for consistency
    
    Attributes:
        task_repository: Repository for task data access
        task_service: Service for task business logic
    """
    
    def __init__(self):
        """
        Initialize the core manager with repositories and services.
        
        Creates and configures all required dependencies, establishing the
        object graph for the application's business logic layer.
        
        Side Effects:
            - Initializes task repository
            - Initializes task service with repository dependency
            - Sets up internal state for future operations
        """
        # Initialize repositories
        self.task_repository = TaskRepository()
        
        # Initialize services with repositories
        self.task_service = TaskService(self.task_repository)
    
    def load_template(self, template_path: str) -> None:
        """
        Load a template file into the repositories.
        
        Reads task data from the specified template file and populates
        the repositories, replacing any existing data.
        
        Args:
            template_path: Path to the template file to load
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template has invalid format
            IOError: If file cannot be read
            
        Side Effects:
            - Clears existing repository data
            - Populates repositories with template data
        """
        self.task_repository.load_template(template_path)
    
    def save_template(self, template_path: str) -> None:
        """
        Save current state to a template file.
        
        Persists the current state of all entities to the specified
        template file, creating or overwriting as needed.
        
        Args:
            template_path: Path to save the template to
            
        Raises:
            IOError: If file cannot be written
            PermissionError: If user lacks permission
            
        Side Effects:
            - Creates or overwrites file at template_path
            - Writes current repository state to file
        """
        self.task_repository.save_template(template_path)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/manager.py
        dohcount: 1
        
        Used By:
            - CLI Show Command: To display task details
            - Web API: For GET /tasks/:id endpoint
            - Dashboard: For retrieving specific task details
            - Relationship Resolver: For retrieving linked tasks
        
        Purpose:
            Retrieves a single task by its unique identifier, providing a central
            method for accessing task data across the application while handling
            cases where the task might not exist.
        
        Requirements:
            - Must validate input ID before processing
            - Must return None for non-existent tasks rather than raising exceptions
            - Must retrieve complete task data including all properties
            - CRITICAL: Must not modify the retrieved task
        
        Args:
            task_id: The unique identifier of the task to retrieve
            
        Returns:
            The task object if found, None otherwise
            
        Example Usage:
            ```python
            # Retrieve a task and handle possibility of it not existing
            task = manager.get_task("tsk_123abc")
            if task:
                print(f"Found task: {task.name} ({task.status})")
            else:
                print("Task not found")
            ```
        """
        return self.task_repository.get_task(task_id)
    
    def get_task_by_name(self, task_name: str) -> Optional[Task]:
        """
        Get a task by its name.
        
        Args:
            task_name: Task name to find
            
        Returns:
            Task if found, None otherwise
        """
        return self.task_repository.get_task_by_name(task_name)
    
    def list_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List of all tasks
        """
        return self.task_repository.list_tasks()
    
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/manager.py
        dohcount: 1
        
        Used By:
            - CLI Create Command: For creating new tasks
            - Web API: For POST /tasks endpoint
            - Import Tool: For creating tasks from external data
            - Initialization Scripts: For setting up standard tasks
        
        Purpose:
            Creates a new task in the system based on provided data, validating
            all required fields, generating necessary identifiers, and persisting
            the task to storage while enforcing business rules.
        
        Requirements:
            - Must validate all required fields in task_data
            - Must generate a unique ID if not provided
            - Must enforce business rules (e.g., unique names)
            - Must persist the task to storage
            - CRITICAL: Must prevent duplicate task names
            - CRITICAL: Must validate all relationships
        
        Args:
            task_data: Dictionary containing task properties including:
                - name: Task name (required)
                - description: Task description (optional)
                - status: Task status (optional, defaults to "to do")
                - priority: Task priority (optional, defaults to 1)
                - tags: List of task tags (optional)
            
        Returns:
            The newly created task object with populated ID and fields
            
        Raises:
            ValidationError: If required fields are missing or invalid
            EntityAlreadyExistsError: If a task with the same name exists
            
        Side Effects:
            - Adds task to repository
            - Generates and assigns a task ID
            - Updates indexes for efficient retrieval
            
        Example Usage:
            ```python
            # Create a simple task
            new_task = manager.create_task({
                "name": "Implement feature X",
                "description": "Add the new X feature to improve performance",
                "priority": 2,
                "tags": ["feature", "performance"]
            })
            print(f"Created task with ID: {new_task.id}")
            ```
        """
        return self.task_service.create_task(task_data)
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Task:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/manager.py
        dohcount: 1
        
        Used By:
            - CLI Update Command: For modifying existing tasks
            - Web API: For PUT/PATCH /tasks/:id endpoints
            - Dashboard: For inline task editing
            - Automation Scripts: For batch updates
        
        Purpose:
            Updates an existing task with new data while preserving its identity,
            validating all changes, enforcing business rules, and persisting
            the modifications to storage.
        
        Requirements:
            - Must verify task exists before updating
            - Must validate all provided fields
            - Must enforce business rules (e.g., unique names)
            - Must not change the task ID
            - CRITICAL: Must handle partial updates correctly
            - CRITICAL: Must maintain relationship integrity
        
        Args:
            task_id: The unique identifier of the task to update
            task_data: Dictionary containing fields to update, which may include:
                - name: New task name
                - description: New task description
                - status: New task status
                - priority: New task priority
                - tags: New list of task tags
            
        Returns:
            The updated task object with the changes applied
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ValidationError: If provided fields are invalid
            EntityAlreadyExistsError: If new name conflicts with another task
            
        Side Effects:
            - Updates task in repository
            - Updates indexes if name changes
            - May trigger related updates (e.g., status propagation)
            
        Example Usage:
            ```python
            # Update task status and priority
            updated_task = manager.update_task("tsk_123abc", {
                "status": "in progress",
                "priority": 3
            })
            print(f"Updated {updated_task.name} to {updated_task.status}")
            ```
        """
        return self.task_service.update_task(task_id, task_data)
    
    def delete_task(self, task_id: str) -> None:
        """
        Delete a task.
        
        Args:
            task_id: Task ID to delete
        """
        self.task_service.delete_task(task_id)
    
    def add_subtask(self, parent_id: str, subtask_data: Dict[str, Any]) -> Task:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/manager.py
        dohcount: 1
        
        Used By:
            - CLI Subtask Command: For creating hierarchical tasks
            - Web API: For POST /tasks/:id/subtasks endpoint
            - Import Tool: For creating task hierarchies
            - Task Breakdown UI: For splitting tasks into smaller units
        
        Purpose:
            Creates a new task as a subtask of an existing parent task,
            establishing a hierarchical relationship while validating
            all data and enforcing parent-child business rules.
        
        Requirements:
            - Must verify parent task exists
            - Must validate all subtask data
            - Must establish parent-child relationship
            - Must enforce hierarchy constraints
            - CRITICAL: Must maintain unique subtask names within parent
            - CRITICAL: Must handle nested subtasks correctly
        
        Args:
            parent_id: The unique identifier of the parent task
            subtask_data: Dictionary containing subtask properties including:
                - name: Subtask name (required)
                - description: Subtask description (optional)
                - status: Subtask status (optional, defaults to parent's status)
                - priority: Subtask priority (optional, defaults to parent's priority)
                - tags: List of subtask tags (optional, inherits parent's tags)
            
        Returns:
            The newly created subtask object with populated ID and fields
            
        Raises:
            EntityNotFoundError: If the parent task doesn't exist
            ValidationError: If required fields are missing or invalid
            EntityAlreadyExistsError: If a subtask with the same name exists
            
        Side Effects:
            - Creates new task in repository
            - Establishes parent-child relationship
            - Updates parent's subtask list
            
        Example Usage:
            ```python
            # Add a subtask to an existing task
            subtask = manager.add_subtask("tsk_parent123", {
                "name": "Research options",
                "status": "to do",
                "priority": 1
            })
            print(f"Added subtask {subtask.id} to parent task")
            ```
        """
        return self.task_service.add_subtask(parent_id, subtask_data)
    
    def update_task_status(self, task_id: str, status: str) -> Task:
        """
        Update a task's status.
        
        Args:
            task_id: Task ID to update
            status: New status
            
        Returns:
            Updated task
        """
        return self.task_service.update_task_status(task_id, status)
    
    def add_task_comment(self, task_id: str, comment: str) -> Task:
        """
        Add a comment to a task.
        
        Args:
            task_id: Task ID to comment on
            comment: Comment text
            
        Returns:
            Updated task
        """
        return self.task_service.add_task_comment(task_id, comment)
    
    def update_task_tags(self, task_id: str, tags: List[str]) -> Task:
        """
        Update a task's tags.
        
        Args:
            task_id: Task ID to update
            tags: New list of tags
            
        Returns:
            Updated task
        """
        return self.task_service.update_task_tags(task_id, tags)
    
    def get_task_relationships(self, task_id: str) -> Dict[str, List[str]]:
        """
        Get a task's relationships.
        
        Args:
            task_id: Task ID to get relationships for
            
        Returns:
            Dictionary of relationship types to lists of task IDs
        """
        return self.task_service.get_task_relationships(task_id)
    
    def add_task_relationship(self, task_id: str, related_id: str, relationship_type: str) -> None:
        """
        Add a relationship between tasks.
        
        Args:
            task_id: Source task ID
            related_id: Target task ID
            relationship_type: Type of relationship
        """
        self.task_service.add_task_relationship(task_id, related_id, relationship_type) 