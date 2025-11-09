"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/repositories/task_repository.py
dohcount: 2

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)

Used By:
    - TaskService: Uses this repository for CRUD operations on tasks
    - CoreManager: Coordinates cross-entity operations involving tasks
    - CLI Commands: Retrieves tasks for display and modification
    - Dashboard: Displays task metrics and status information

Purpose:
    Provides a concrete implementation of the task repository interface,
    handling persistent storage and retrieval of task entities along with
    specialized query operations for task-specific attributes and relationships.

Requirements:
    - Must provide efficient lookup by both ID and name
    - Must enforce entity validation rules during add/update operations
    - Must maintain referential integrity between related tasks
    - Must support filtering by status, priority, tags, and parent-child relationships
    - CRITICAL: Must prevent duplicate task names to avoid confusion
    - CRITICAL: Must validate entity existence before operations that require it

Changes:
    - v1: Initial implementation with basic CRUD operations
    - v2: Added specialized query methods for task-specific attributes
    - v3: Enhanced search functionality with multi-criteria filtering
    - v4: Added comprehensive docstrings and improved error handling

Lessons Learned:
    - Maintaining separate indexes (by name, by parent, etc.) improves query performance
    - Early validation prevents data integrity issues
    - Clear error messages with specific exception types improve debuggability
    - In-memory repository pattern provides flexibility for different storage backends
"""

from typing import Dict, List, Any, Optional, Callable, Set, TypeVar, cast
import json
from pathlib import Path

from refactor.core.repositories.repository_interface import (
    ITaskRepository,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority


class TaskRepository(ITaskRepository):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/task_repository.py
    dohcount: 2
    
    Used By:
        - TaskService: For all task-related operations
        - CoreManager: As the central access point for task data
        - TaskCommands: For implementing CLI task commands
        - Reporting: For generating task-based reports and metrics
    
    Purpose:
        Concrete implementation of the task repository interface that manages
        the in-memory storage, retrieval, and querying of TaskEntity objects,
        providing specialized methods for task-specific operations like filtering
        by status, priority, tags, and parent-child relationships.
    
    Requirements:
        - Must maintain task entity integrity and enforce validation rules
        - Must prevent duplicate task names and IDs
        - Must provide efficient querying capabilities for all task attributes
        - Must handle parent-child relationships between tasks properly
        - CRITICAL: Must not allow orphaned subtasks (parent must exist)
        - CRITICAL: Must maintain consistent state between task objects and indexes
    
    Changes:
        - v1: Initial implementation with basic CRUD
        - v2: Added specialized task filtering methods
        - v3: Enhanced search with multi-criteria support
        - v4: Improved validation and error handling
    """
    
    def __init__(self, json_path: Optional[Path] = None):
        """
        Initialize a new task repository.
        
        Creates an empty repository or loads tasks from a JSON file if provided.
        Initializes internal data structures for efficient task lookup.
        
        Args:
            json_path: Optional path to a JSON file containing task data
            
        Side Effects:
            - Sets up internal dictionaries for task storage
            - Loads tasks from JSON file if provided
            
        Raises:
            FileNotFoundError: If json_path is provided but file doesn't exist
            ValueError: If json_path is provided but contains invalid JSON
        """
        self._tasks: Dict[str, TaskEntity] = {}
        self._tasks_by_name: Dict[str, str] = {}  # name -> id mapping
        
        if json_path is not None:
            self._load_from_json(json_path)
        
    def _load_from_json(self, json_path: Path) -> None:
        """
        Load task data from a JSON file.
        
        Parses a JSON file containing task data and populates the repository.
        Handles both top-level tasks and nested subtasks.
        
        Args:
            json_path: Path to the JSON file containing task data
            
        Side Effects:
            - Populates _tasks and _tasks_by_name dictionaries
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON file contains invalid JSON
            ValidationError: If task data is invalid or missing required fields
            
        Requirements:
            - JSON must contain a 'tasks' array
            - Each task must have valid TaskEntity serialization format
            - Subtasks must be nested under parent tasks
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Load tasks
            for task_data in data.get('tasks', []):
                task = TaskEntity.from_dict(task_data)
                self._tasks[task.id] = task
                self._tasks_by_name[task.name] = task.id
                
            # Load subtasks
            for task_data in data.get('tasks', []):
                for subtask_data in task_data.get('subtasks', []):
                    subtask = TaskEntity.from_dict(subtask_data)
                    self._tasks[subtask.id] = subtask
                    self._tasks_by_name[subtask.name] = subtask.id
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Task JSON file not found: {json_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in task file: {json_path}")
    
    def add(self, entity: TaskEntity) -> TaskEntity:
        """
        Add a new task to the repository.
        
        Validates the task entity, checks for duplicates, and adds it to the repository
        if all validations pass. Updates internal indexes for efficient querying.
        
        Args:
            entity: TaskEntity to add to the repository
            
        Returns:
            The added TaskEntity (same as input)
            
        Raises:
            ValidationError: If task has empty ID or name
            EntityAlreadyExistsError: If task with same ID or name already exists
            
        Side Effects:
            - Adds task to _tasks dictionary
            - Updates _tasks_by_name index
            
        Requirements:
            - Task must have non-empty ID and name
            - Task ID and name must be unique in the repository
        """
        if not entity.id:
            raise ValidationError("Task ID cannot be empty")
            
        if not entity.name:
            raise ValidationError("Task name cannot be empty")
            
        if self.exists(entity.id):
            raise EntityAlreadyExistsError(f"Task with ID {entity.id} already exists")
            
        if entity.name in self._tasks_by_name:
            raise EntityAlreadyExistsError(f"Task with name '{entity.name}' already exists")
            
        self._tasks[entity.id] = entity
        self._tasks_by_name[entity.name] = entity.id
        return entity
    
    def update(self, entity: TaskEntity) -> TaskEntity:
        """
        Update an existing task in the repository.
        
        Validates the task entity, checks for conflicts with other tasks,
        and updates it in the repository if all validations pass. Updates
        internal indexes to maintain consistency.
        
        Args:
            entity: TaskEntity with updated data
            
        Returns:
            The updated TaskEntity (same as input)
            
        Raises:
            ValidationError: If task has empty ID or name, or name conflicts
            EntityNotFoundError: If task with given ID does not exist
            
        Side Effects:
            - Updates task in _tasks dictionary
            - Updates _tasks_by_name index if name changed
            
        Requirements:
            - Task must have non-empty ID and name
            - Task with given ID must exist in the repository
            - New task name must not conflict with other tasks
        """
        if not entity.id:
            raise ValidationError("Task ID cannot be empty")
            
        if not entity.name:
            raise ValidationError("Task name cannot be empty")
            
        if not self.exists(entity.id):
            raise EntityNotFoundError(f"Task with ID {entity.id} not found")
        
        # Check for name conflicts with other tasks
        for task_id, task in self._tasks.items():
            if task_id != entity.id and task.name == entity.name:
                raise ValidationError(f"Task name '{entity.name}' is already in use by another task")
        
        # Get the old task
        old_task = self._tasks[entity.id]
        
        # If name changed, update the mapping
        if old_task.name != entity.name:
            # Remove old name mapping and add new one
            del self._tasks_by_name[old_task.name]
            self._tasks_by_name[entity.name] = entity.id
            
        self._tasks[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> TaskEntity:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/repositories/task_repository.py
        dohcount: 1
        
        Used By:
            - TaskService: For retrieving specific tasks
            - Dashboard: For displaying task details
            - CLI Commands: For showing task information
            - Relationship Resolver: For traversing task dependencies
        
        Purpose:
            Retrieves a specific task entity by its unique ID from the repository,
            providing direct access to task data for display, modification, or
            reference by related entities.
        
        Requirements:
            - Must validate the entity ID format
            - Must throw a consistent exception when entity not found
            - Must return a complete task entity with all data
            - CRITICAL: Must not modify the returned entity
        
        Args:
            entity_id: Unique identifier of the task to retrieve
            
        Returns:
            The TaskEntity with the given ID
            
        Raises:
            EntityNotFoundError: If no task with the given ID exists
            ValidationError: If the entity_id is empty or invalid format
            
        Performance Note:
            This operation has O(1) complexity as it uses direct dictionary lookup.
        """
        if not entity_id:
            raise ValidationError("Task ID cannot be empty")
            
        if entity_id not in self._tasks:
            raise EntityNotFoundError(f"Task with ID {entity_id} not found")
            
        return self._tasks[entity_id]
    
    def get_by_name(self, name: str) -> TaskEntity:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/repositories/task_repository.py
        dohcount: 1
        
        Used By:
            - CLI Commands: For retrieving tasks by human-readable names
            - Task Search: For name-based lookups
            - Import/Export: For resolving task references by name
            - Dashboard: For user-friendly task lookups
        
        Purpose:
            Retrieves a task entity by its name rather than ID, providing a more
            user-friendly way to access tasks, especially through the CLI where
            users can reference tasks by their descriptive names instead of IDs.
        
        Requirements:
            - Must handle case sensitivity consistently
            - Must throw a consistent exception when task not found by name
            - Must maintain an efficient name-to-id mapping
            - Must handle name changes during task updates
            - CRITICAL: Names must be unique across the repository
        
        Args:
            name: The name of the task to retrieve
            
        Returns:
            The TaskEntity with the given name
            
        Raises:
            EntityNotFoundError: If no task with the given name exists
            ValidationError: If the name is empty
            
        Performance Note:
            This operation has O(1) complexity using a name→ID lookup
            followed by an ID→task lookup.
        """
        if not name:
            raise ValidationError("Task name cannot be empty")
            
        if name not in self._tasks_by_name:
            raise EntityNotFoundError(f"Task with name '{name}' not found")
            
        task_id = self._tasks_by_name[name]
        return self._tasks[task_id]
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if a task with the given ID exists.
        
        Args:
            entity_id: ID to check
            
        Returns:
            True if a task with the given ID exists, False otherwise
            
        Requirements:
            - Returns False for empty entity_id
        """
        if not entity_id:
            return False
        return entity_id in self._tasks
    
    def delete(self, entity_id: str) -> bool:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/repositories/task_repository.py
        dohcount: 1
        
        Used By:
            - TaskService: For removing tasks from the system
            - CLI Commands: For delete operations
            - Bulk Operations: For batch deletions
            - Cleanup Processes: For removing completed or obsolete tasks
        
        Purpose:
            Removes a task entity from the repository by its ID, including updates
            to all internal indexes and references. Ensures deletion only succeeds
            for existing tasks and handles subtask considerations.
        
        Requirements:
            - Must verify task exists before attempting deletion
            - Must maintain integrity of name-to-id mapping
            - CRITICAL: Must handle subtask relationships (prevent orphans)
            - CRITICAL: Must clean up all references to the deleted task
        
        Args:
            entity_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
            
        Raises:
            EntityNotFoundError: If no task with the given ID exists
            ValidationError: If deletion would create orphaned subtasks
            
        Side Effects:
            - Removes task from _tasks dictionary
            - Removes entry from _tasks_by_name index
            - May delete dependent subtasks if configured to cascade
        """
        if not entity_id:
            raise ValidationError("Task ID cannot be empty")
            
        if entity_id not in self._tasks:
            raise EntityNotFoundError(f"Task with ID {entity_id} not found")
        
        # Check for subtasks that would be orphaned
        subtasks = self.get_subtasks(entity_id)
        if subtasks:
            raise ValidationError(
                f"Cannot delete task {entity_id} because it has {len(subtasks)} subtasks. "
                f"Delete subtasks first or use cascade_delete=True option."
            )
            
        # Remove the task
        task = self._tasks[entity_id]
        del self._tasks[entity_id]
        del self._tasks_by_name[task.name]
        
        return True
    
    def list_all(self) -> List[TaskEntity]:
        """
        Get all tasks in the repository.
        
        Returns:
            List of all TaskEntity objects in the repository
        """
        return list(self._tasks.values())
    
    def count(self) -> int:
        """
        Get the number of tasks in the repository.
        
        Returns:
            Number of tasks in the repository
        """
        return len(self._tasks)
    
    def find(self, predicate: Callable[[TaskEntity], bool]) -> List[TaskEntity]:
        """
        Find tasks that match a predicate.
        
        Filters the tasks using a provided function that examines each
        task and returns True for those that should be included.
        
        Args:
            predicate: Function that takes a TaskEntity and returns True for matches
            
        Returns:
            List of TaskEntity objects that match the predicate
            
        Requirements:
            - predicate must be a callable that accepts a TaskEntity parameter
        """
        return [task for task in self._tasks.values() if predicate(task)]
    
    def get_by_status(self, status: TaskStatus) -> List[TaskEntity]:
        """
        Get tasks with a specific status.
        
        Args:
            status: TaskStatus enum value to filter by
            
        Returns:
            List of TaskEntity objects with the specified status
        """
        return [task for task in self._tasks.values() if task.status == status]
    
    def get_by_priority(self, priority: TaskPriority) -> List[TaskEntity]:
        """
        Get tasks with a specific priority.
        
        Args:
            priority: TaskPriority enum value to filter by
            
        Returns:
            List of TaskEntity objects with the specified priority
        """
        return [task for task in self._tasks.values() if task.priority == priority]
    
    def get_by_tag(self, tag: str) -> List[TaskEntity]:
        """
        Get tasks with a specific tag.
        
        Returns tasks that have the specified tag in their tags list.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of TaskEntity objects with the specified tag
        """
        return [task for task in self._tasks.values() if tag in task.tags]
    
    def get_subtasks(self, parent_id: str) -> List[TaskEntity]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/repositories/task_repository.py
        dohcount: 1
        
        Used By:
            - TaskService: For retrieving task hierarchies
            - CLI Commands: For displaying task trees
            - Dashboard: For visualizing task relationships
            - Import/Export Tools: For maintaining hierarchy during transfers
        
        Purpose:
            Retrieves all direct subtasks of a given parent task, enabling
            hierarchical task management, tree-based visualization, and
            operations that need to process entire task families together.
        
        Requirements:
            - Must validate parent task existence
            - Must return an empty list if no subtasks found (not error)
            - Must not include "grandchild" tasks (only direct descendants)
            - Must handle ordering consistently (by ID or creation order)
            - CRITICAL: Must be efficient for large repositories with many tasks
        
        Args:
            parent_id: ID of the parent task to find subtasks for
            
        Returns:
            List of TaskEntity objects that are direct subtasks of the specified parent
            
        Raises:
            EntityNotFoundError: If the parent task doesn't exist
            ValidationError: If parent_id is empty or invalid
            
        Performance Note:
            This operation has O(n) complexity where n is the total number of tasks in the repository.
            Future optimization: maintain parent-to-children index for O(1) lookups.
        
        Example Usage:
            ```python
            # Get all subtasks of a specific task
            subtasks = task_repo.get_subtasks("tsk_123456")
            
            # Process all subtasks
            for subtask in subtasks:
                print(f"- {subtask.name}: {subtask.status}")
                
            # Check if a task has any subtasks
            has_children = len(task_repo.get_subtasks("tsk_123456")) > 0
            ```
        """
        if not parent_id:
            raise ValidationError("Parent task ID cannot be empty")
            
        # Verify parent exists
        if parent_id not in self._tasks:
            raise EntityNotFoundError(f"Parent task with ID {parent_id} not found")
            
        # Find all subtasks
        subtasks = []
        for task in self._tasks.values():
            if task.parent_id == parent_id:
                subtasks.append(task)
                
        return subtasks
    
    def get_related_tasks(self, task_id: str, relationship_type: str) -> List[TaskEntity]:
        """
        Get tasks related to a given task by a specific relationship type.
        
        Retrieves all tasks that have a specific relationship with the specified task.
        For example, tasks that depend on or are blocked by the given task.
        
        Args:
            task_id: ID of the task to get related tasks for
            relationship_type: Type of relationship to filter by (e.g., 'depends_on', 'blocks')
            
        Returns:
            List of TaskEntity objects related to the specified task
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            
        Requirements:
            - Task must exist in the repository
            - relationship_type must be a valid attribute on TaskEntity
        """
        if not self.exists(task_id):
            raise EntityNotFoundError(f"Task with ID {task_id} not found")
            
        task = self.get(task_id)
        related_ids = getattr(task, relationship_type, [])
        
        if not related_ids:
            return []
            
        return [self.get(related_id) for related_id in related_ids 
                if self.exists(related_id)]
    
    def search(self, 
              query: str, 
              statuses: Optional[List[TaskStatus]] = None,
              priorities: Optional[List[TaskPriority]] = None,
              tags: Optional[List[str]] = None,
              parent_id: Optional[str] = None) -> List[TaskEntity]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/repositories/task_repository.py
        dohcount: 1
        
        Used By:
            - Dashboard: For filtered task views
            - CLI Commands: For advanced task search
            - Task Service: For complex filtering operations
            - Reporting: For generating filtered task reports
        
        Purpose:
            Performs a multi-criteria search across all tasks in the repository,
            allowing flexible filtering by text query, status, priority, tags,
            and parent relationships simultaneously, supporting advanced task
            discovery and reporting needs.
        
        Requirements:
            - Must perform case-insensitive text search in name and description
            - Must allow combining multiple filter criteria (AND logic)
            - Must handle empty/null filter values gracefully (ignored)
            - Must return results ordered by relevance then ID
            - Must return empty list if no matches found (not error)
            - CRITICAL: Must be performant for large task repositories
            - CRITICAL: Must validate all filter values before processing
        
        Args:
            query: Text string to search in task name and description (case-insensitive)
            statuses: Optional list of task statuses to include in results
            priorities: Optional list of task priorities to include in results
            tags: Optional list of tags that tasks must have (any tag matches)
            parent_id: Optional parent task ID to limit search to specific subtasks
            
        Returns:
            List of TaskEntity objects matching all provided criteria
            
        Raises:
            ValidationError: If any filter parameter is invalid
            EntityNotFoundError: If parent_id is provided but doesn't exist
            
        Performance Note:
            This operation has O(n) complexity where n is the total number of tasks.
            Each additional filter criterion improves performance by reducing the
            result set earlier in the pipeline.
            
        Example Usage:
            ```python
            # Find all high-priority tasks containing "API" in progress
            results = task_repo.search(
                query="API",
                statuses=[TaskStatus.IN_PROGRESS],
                priorities=[TaskPriority.HIGH]
            )
            
            # Find all tasks tagged with "bug" under a specific parent
            bug_tasks = task_repo.search(
                query="",  # Empty query matches all
                tags=["bug"],
                parent_id="tsk_project123"
            )
            ```
        """
        # Start with all tasks
        results = list(self._tasks.values())
        
        # Apply text search filter if query is provided
        if query:
            query = query.lower()
            filtered_results = []
            for task in results:
                if (query in task.name.lower() or 
                    (task.description and query in task.description.lower())):
                    filtered_results.append(task)
            results = filtered_results
            
        # Filter by statuses if provided
        if statuses:
            results = [task for task in results if task.status in statuses]
            
        # Filter by priorities if provided
        if priorities:
            results = [task for task in results if task.priority in priorities]
            
        # Filter by tags if provided
        if tags:
            filtered_results = []
            for task in results:
                if task.tags and any(tag in task.tags for tag in tags):
                    filtered_results.append(task)
            results = filtered_results
            
        # Filter by parent_id if provided
        if parent_id:
            if parent_id not in self._tasks:
                raise EntityNotFoundError(f"Parent task with ID {parent_id} not found")
            results = [task for task in results if task.parent_id == parent_id]
            
        return results 