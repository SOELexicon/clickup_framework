"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/interfaces/core_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_65df3554 - Update TaskType Enum (sibling)

Used By:
    - Main Application: Primary entry point for all core operations
    - CLI Commands: Interface for executing business operations
    - Tests: For mocking and validation

Purpose:
    Defines the CoreManager interface which serves as the primary public API 
    for all core module functionality, acting as a facade over the various 
    services and providing a simplified, consistent interface for clients.

Requirements:
    - Must provide comprehensive access to all core functionality
    - Must abstract away implementation details of underlying services
    - Must maintain consistent error handling patterns
    - CRITICAL: Must ensure all implementations follow the interface contract precisely
    - CRITICAL: Must document parameter validation rules for all methods

Changes:
    - v1: Initial interface definition with basic task management
    - v2: Added support for spaces, folders, and lists
    - v3: Enhanced with comprehensive checklist operations
    - v4: Added relationship management between tasks
    - v5: Added search capabilities and advanced filtering

Lessons Learned:
    - Facade pattern simplifies client interactions with complex subsystems
    - Proper interface definition enables multiple implementations (file-based, API-based)
    - Abstract methods force implementation consistency across concrete classes
    - Comprehensive documentation at the interface level prevents implementation drift
"""

import abc
from typing import List, Dict, Any, Optional, Union, Set, Tuple

from ..entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from ..entities.list_entity import ListEntity
from ..entities.folder_entity import FolderEntity
from ..entities.space_entity import SpaceEntity


class CoreManagerError(Exception):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/interfaces/core_manager.py
    dohcount: 1
    
    Used By:
        - CoreManager implementations: For error handling
        - Client code: For catching and handling errors
        
    Purpose:
        Base exception class for all errors originating from CoreManager implementations,
        providing a common type for catching any core manager related exceptions.
        
    Requirements:
        - Must serve as the parent class for all CoreManager-specific exceptions
        - Should include descriptive error messages when raised
    """
    pass


class InvalidQueryError(CoreManagerError):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/interfaces/core_manager.py
    dohcount: 1
    
    Used By:
        - CoreManager.search_tasks: For reporting invalid search queries
        - Client code: For handling specific search-related errors
        
    Purpose:
        Specialized exception raised when a search query is malformed or 
        contains invalid syntax, helping distinguish between search errors
        and other CoreManager errors.
        
    Requirements:
        - Must include specific information about what made the query invalid
        - Should suggest corrections when possible
    """
    pass


class CoreManager(abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/interfaces/core_manager.py
    dohcount: 1
    
    Used By:
        - Main Application: For accessing core functionality
        - CLI Commands: For implementing command operations
        - Tests: For mocking and validation
        
    Purpose:
        Defines the contract for the Core Manager component, which serves as the
        main facade providing access to all core functionality. This abstracts
        the complexity of the underlying services, repositories, and entities.
        
    Requirements:
        - Must provide complete coverage of all core operations
        - Must handle exceptions from lower layers and convert to appropriate errors
        - Must enforce proper validation of all inputs
        - Must maintain strict separation between interface and implementation
        - CRITICAL: Must be the only entry point to core functionality for clients
        - CRITICAL: All methods must have precise documentation on parameters and return values
        
    Changes:
        - v1: Initial definition with task management
        - v2: Added checklist operations
        - v3: Added relationship management
        - v4: Added search and filtering operations
        - v5: Added documentation and structure operations
    """
    
    @abc.abstractmethod
    def initialize(self, file_path: str) -> None:
        """
        Initialize the Core Manager with a file path.
        
        Loads data from the specified JSON file and initializes all
        internal services and repositories.
        
        Args:
            file_path: Path to the JSON template file
            
        Raises:
            CoreManagerError: If file doesn't exist or has invalid format
            
        Requirements:
            - Must validate file exists before attempting to read
            - Must validate JSON structure after reading
            - Must initialize all required services
        """
        pass
    
    @abc.abstractmethod
    def save(self) -> None:
        """
        Save all changes to the template file.
        
        Persists all pending changes to tasks, lists, and other entities
        back to the source file.
        
        Raises:
            CoreManagerError: If file writing fails or permissions are insufficient
            
        Requirements:
            - Must handle file locking to prevent corruption
            - Must maintain backup during write operations
            - Must validate data before saving
        """
        pass
    
    @abc.abstractmethod
    def create_task(self, 
                   name: str, 
                   description: str = "", 
                   status: Union[str, TaskStatus] = TaskStatus.TO_DO,
                   priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
                   tags: Optional[List[str]] = None,
                   parent_id: Optional[str] = None,
                   list_id: Optional[str] = None) -> TaskEntity:
        """
        Create a new task.
        
        Creates a new task with the given properties and optionally
        assigns it to a parent task or list.
        
        Args:
            name: Name of the task (required, must not be empty)
            description: Description of the task (optional)
            status: Initial status (default: TO_DO, can be string or TaskStatus enum)
            priority: Priority level (default: NORMAL, can be int or TaskPriority enum)
            tags: List of tags to apply (optional)
            parent_id: Optional parent task ID for creating subtasks
            list_id: Optional list ID to add the task to
            
        Returns:
            The created TaskEntity with generated ID and timestamps
            
        Raises:
            CoreManagerError: If validation fails or dependencies don't exist
            
        Requirements:
            - Must validate name is not empty
            - Must validate parent_id exists if provided
            - Must validate list_id exists if provided
            - Must generate unique ID for the task
            - Must set created_at and updated_at timestamps
        """
        pass
    
    @abc.abstractmethod
    def get_task(self, task_id: str) -> TaskEntity:
        """
        Get a task by its ID.
        
        Retrieves a task with the exact ID provided.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The TaskEntity with the given ID
            
        Raises:
            CoreManagerError: If the task doesn't exist
            
        Requirements:
            - Must validate task_id format
            - Must raise exception if task not found
            - Must return complete task with all relationships
        """
        pass
    
    @abc.abstractmethod
    def get_task_by_name(self, name: str) -> Optional[TaskEntity]:
        """
        Get a task by its name.
        
        Searches for a task with the specified name (case-sensitive).
        If multiple tasks have the same name, returns the first one found.
        
        Args:
            name: Name of the task to retrieve
            
        Returns:
            The TaskEntity with the given name, or None if not found
            
        Requirements:
            - Must perform exact match on task name
            - Must handle case where multiple tasks have same name
            - Must return None if no matching task exists
        """
        pass
    
    @abc.abstractmethod
    def update_task(self, 
                   task_id: str, 
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   status: Optional[Union[str, TaskStatus]] = None,
                   priority: Optional[Union[int, TaskPriority]] = None) -> TaskEntity:
        """
        Update a task's properties.
        
        Updates one or more properties of an existing task. Any parameter
        set to None will retain its current value.
        
        Args:
            task_id: ID of the task to update
            name: New name (if None, unchanged)
            description: New description (if None, unchanged)
            status: New status (if None, unchanged)
            priority: New priority (if None, unchanged)
            
        Returns:
            The updated TaskEntity
            
        Raises:
            CoreManagerError: If the task doesn't exist or validation fails
            
        Requirements:
            - Must validate task exists before updating
            - Must only update fields that are explicitly provided
            - Must update updated_at timestamp
            - Must validate new values against entity rules
        """
        pass
    
    @abc.abstractmethod
    def delete_task(self, task_id: str, cascade: bool = True) -> bool:
        """
        Delete a task.
        
        Removes a task from the system, optionally deleting all its subtasks
        as well.
        
        Args:
            task_id: ID of the task to delete
            cascade: Whether to also delete subtasks (default: True)
            
        Returns:
            True if the task was deleted, False if it didn't exist
            
        Raises:
            CoreManagerError: If deletion fails due to constraints
            
        Requirements:
            - Must check if task exists
            - Must handle deletion of subtasks if cascade=True
            - Must handle relationships (dependencies, blockers)
            - Must clean up all references to the task
        """
        pass
    
    @abc.abstractmethod
    def update_task_status(self, 
                          task_id: str, 
                          status: Union[str, TaskStatus],
                          comment: Optional[str] = None) -> TaskEntity:
        """
        Update a task's status.
        
        Updates the status of a task and optionally adds a comment
        explaining the status change.
        
        Args:
            task_id: ID of the task to update
            status: New status (string or TaskStatus enum)
            comment: Optional comment explaining the status change
            
        Returns:
            The updated TaskEntity
            
        Raises:
            CoreManagerError: If the task doesn't exist or status is invalid
            
        Requirements:
            - Must validate task exists
            - Must validate status is a valid TaskStatus value
            - Must check if status change is allowed by rules
            - Must update updated_at timestamp
            - Must add comment if provided
        """
        pass
    
    @abc.abstractmethod
    def add_comment(self, task_id: str, text: str, author: str) -> Dict[str, Any]:
        """
        Add a comment to a task.
        
        Creates a new comment on the specified task with the given text
        and author information.
        
        Args:
            task_id: ID of the task to comment on
            text: Comment text (must not be empty)
            author: Name of the comment author
            
        Returns:
            Comment data including ID, text, author, and timestamp
            
        Raises:
            CoreManagerError: If the task doesn't exist or text is empty
            
        Requirements:
            - Must validate task exists
            - Must validate text is not empty
            - Must generate unique ID for comment
            - Must set timestamp for comment
            - Must update task's updated_at timestamp
        """
        pass
    
    @abc.abstractmethod
    def add_tag(self, task_id: str, tag: str) -> TaskEntity:
        """
        Add a tag to a task.
        
        Args:
            task_id: ID of the task to tag
            tag: Tag to add
            
        Returns:
            The updated TaskEntity
            
        Raises:
            CoreManagerError: If the task doesn't exist or tag addition fails
        """
        pass
    
    @abc.abstractmethod
    def remove_tag(self, task_id: str, tag: str) -> TaskEntity:
        """
        Remove a tag from a task.
        
        Args:
            task_id: ID of the task to modify
            tag: Tag to remove
            
        Returns:
            The updated TaskEntity
            
        Raises:
            CoreManagerError: If the task doesn't exist or tag removal fails
        """
        pass
    
    @abc.abstractmethod
    def add_dependency(self, task_id: str, depends_on_id: str) -> TaskEntity:
        """
        Add a dependency between tasks.
        
        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task that task_id depends on
            
        Returns:
            The updated dependent TaskEntity
            
        Raises:
            CoreManagerError: If either task doesn't exist or dependency addition fails
        """
        pass
    
    @abc.abstractmethod
    def remove_dependency(self, task_id: str, depends_on_id: str) -> TaskEntity:
        """
        Remove a dependency between tasks.
        
        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task that task_id depends on
            
        Returns:
            The updated dependent TaskEntity
            
        Raises:
            CoreManagerError: If either task doesn't exist or dependency removal fails
        """
        pass
    
    @abc.abstractmethod
    def get_subtasks(self, task_id: str) -> List[TaskEntity]:
        """
        Get all subtasks of a task.
        
        Args:
            task_id: ID of the parent task
            
        Returns:
            List of subtask entities
            
        Raises:
            CoreManagerError: If the task doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def get_dependencies(self, task_id: str) -> List[TaskEntity]:
        """
        Get all tasks that this task depends on.
        
        Args:
            task_id: ID of the task to check dependencies for
            
        Returns:
            List of task entities that task_id depends on
            
        Raises:
            CoreManagerError: If the task doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def get_blocking_tasks(self, task_id: str) -> List[TaskEntity]:
        """
        Get all tasks that are blocked by this task.
        
        Args:
            task_id: ID of the task that may block others
            
        Returns:
            List of task entities that are blocked by task_id
            
        Raises:
            CoreManagerError: If the task doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def create_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """
        Create a checklist for a task.
        
        Args:
            task_id: ID of the task to add the checklist to
            name: Name of the checklist
            
        Returns:
            Checklist data including ID
            
        Raises:
            CoreManagerError: If the task doesn't exist or checklist creation fails
        """
        pass
    
    @abc.abstractmethod
    def add_checklist_item(self, 
                          task_id: str, 
                          checklist_id: str, 
                          name: str, 
                          checked: bool = False) -> Dict[str, Any]:
        """
        Add an item to a checklist.
        
        Args:
            task_id: ID of the task that has the checklist
            checklist_id: ID of the checklist to add the item to
            name: Name of the checklist item
            checked: Whether the item is initially checked
            
        Returns:
            Checklist item data including ID
            
        Raises:
            CoreManagerError: If the task or checklist doesn't exist or item addition fails
        """
        pass
    
    @abc.abstractmethod
    def check_checklist_item(self, task_id: str, checklist_id: str, item_id: str, checked: bool) -> Dict[str, Any]:
        """
        Set whether a checklist item is checked or not.
        
        Args:
            task_id: ID of the task that has the checklist
            checklist_id: ID of the checklist
            item_id: ID of the checklist item
            checked: Whether the item should be checked
            
        Returns:
            Updated checklist item data
            
        Raises:
            CoreManagerError: If the task, checklist, or item doesn't exist or update fails
        """
        pass
    
    @abc.abstractmethod
    def search_tasks(self, query: str, **filters) -> List[TaskEntity]:
        """
        Search for tasks using a query string and optional filters.
        
        Args:
            query: Query string to search for
            **filters: Additional filters (status, priority, tags, etc.)
            
        Returns:
            List of matching task entities
            
        Raises:
            InvalidQueryError: If the query is invalid
            CoreManagerError: If search fails
        """
        pass
    
    @abc.abstractmethod
    def find_by_status(self, status: Union[str, TaskStatus]) -> List[TaskEntity]:
        """
        Find tasks with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching task entities
        """
        pass
    
    @abc.abstractmethod
    def find_by_priority(self, priority: Union[int, TaskPriority]) -> List[TaskEntity]:
        """
        Find tasks with a specific priority.
        
        Args:
            priority: Priority to filter by
            
        Returns:
            List of matching task entities
        """
        pass
    
    @abc.abstractmethod
    def find_by_tag(self, tag: str) -> List[TaskEntity]:
        """
        Find tasks with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of matching task entities
        """
        pass
    
    @abc.abstractmethod
    def find_related_to(self, task_id: str) -> List[TaskEntity]:
        """
        Find tasks related to a specific task.
        
        This includes both dependencies and tasks that depend on this task.
        
        Args:
            task_id: ID of the task to find related tasks for
            
        Returns:
            List of related task entities
            
        Raises:
            CoreManagerError: If the task doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def create_space(self, name: str, description: str = "", color: str = None, icon: str = None) -> SpaceEntity:
        """
        Create a new space.
        
        Args:
            name: Name of the space
            description: Description of the space
            color: Optional color for the space (hex code or name)
            icon: Optional icon identifier for the space
            
        Returns:
            The created SpaceEntity
            
        Raises:
            CoreManagerError: If space creation fails
        """
        pass
    
    @abc.abstractmethod
    def create_folder(self, name: str, space_id: str, description: str = "", color: str = None, icon: str = None) -> FolderEntity:
        """
        Create a new folder in a space.
        
        Args:
            name: Name of the folder
            space_id: ID of the space to create the folder in
            description: Description of the folder
            color: Optional color for the folder (hex code or name)
            icon: Optional icon identifier for the folder
            
        Returns:
            The created FolderEntity
            
        Raises:
            CoreManagerError: If the space doesn't exist or folder creation fails
        """
        pass
    
    @abc.abstractmethod
    def create_list(self, name: str, folder_id: str, description: str = "", color: str = None, icon: str = None) -> ListEntity:
        """
        Create a new list in a folder.
        
        Args:
            name: Name of the list
            folder_id: ID of the folder to create the list in
            description: Description of the list
            color: Optional color for the list (hex code or name)
            icon: Optional icon identifier for the list
            
        Returns:
            The created ListEntity
            
        Raises:
            CoreManagerError: If the folder doesn't exist or list creation fails
        """
        pass
    
    @abc.abstractmethod
    def get_spaces(self) -> List[SpaceEntity]:
        """
        Get all spaces.
        
        Returns:
            List of all space entities
        """
        pass
    
    @abc.abstractmethod
    def get_folders(self, space_id: str) -> List[FolderEntity]:
        """
        Get all folders in a space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folder entities in the space
            
        Raises:
            CoreManagerError: If the space doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def get_lists(self, folder_id: str) -> List[ListEntity]:
        """
        Get all lists in a folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of list entities in the folder
            
        Raises:
            CoreManagerError: If the folder doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def get_tasks_in_list(self, list_id: str) -> List[TaskEntity]:
        """
        Get all tasks in a list.
        
        Args:
            list_id: ID of the list to get tasks for
            
        Returns:
            List of task entities in the list
            
        Raises:
            CoreManagerError: If the list doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def add_task_to_list(self, task_id: str, list_id: str, force: bool = False) -> TaskEntity:
        """
        Task: tsk_ff8e47b1 - Update Task Entity with Parent Tracking
        Document: refactor/core/interfaces/core_manager.py
        dohcount: 1
        
        Used By:
            - CLI Assign Command: For container assignment operations
            - Container Management: For organizing tasks within containers
            - Task Import: For assigning tasks during creation
        
        Purpose:
            Assigns a task to a list container, updating the task's container_id
            and the list's task collection. This establishes a bidirectional
            relationship between tasks and their containers.
            
        Requirements:
            - Must validate both task and list exist
            - Must handle cases where task is already in another list
            - Must update the container_id on the task
            - Must maintain bidirectional relationships
            - CRITICAL: Force flag must be required to move between containers
            
        Args:
            task_id: ID of the task to assign
            list_id: ID of the list to assign the task to
            force: Whether to force reassignment if task is already in a list
            
        Returns:
            The updated task entity with the new container assignment
            
        Raises:
            CoreManagerError: If task or list doesn't exist
            ValidationError: If task is already in a list and force is False
        """
        pass
    
    @abc.abstractmethod
    def update_space_colors(self, space_id: str, color: str = None, icon: str = None) -> SpaceEntity:
        """
        Update the color and icon for a space.
        
        Args:
            space_id: ID of the space to update
            color: New color for the space (hex code or name), None to keep current
            icon: New icon identifier for the space, None to keep current
            
        Returns:
            Updated space entity
            
        Raises:
            CoreManagerError: If the space doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def update_folder_colors(self, folder_id: str, color: str = None, icon: str = None) -> FolderEntity:
        """
        Update the color and icon for a folder.
        
        Args:
            folder_id: ID of the folder to update
            color: New color for the folder (hex code or name), None to keep current
            icon: New icon identifier for the folder, None to keep current
            
        Returns:
            Updated folder entity
            
        Raises:
            CoreManagerError: If the folder doesn't exist
        """
        pass
    
    @abc.abstractmethod
    def update_list_colors(self, list_id: str, color: str = None, icon: str = None) -> ListEntity:
        """
        Update the color and icon for a list.
        
        Args:
            list_id: ID of the list to update
            color: New color for the list (hex code or name), None to keep current
            icon: New icon identifier for the list, None to keep current
            
        Returns:
            Updated list entity
            
        Raises:
            CoreManagerError: If the list doesn't exist
        """
        pass 