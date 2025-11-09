"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/repositories/repository_interface.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)

Used By:
    - Repository Implementations: All concrete repositories implement these interfaces
    - Services: Use repository interfaces for dependency injection
    - Core Manager: Coordinates operations across multiple repositories
    - Tests: For mocking repository behavior in unit tests

Purpose:
    Defines the core repository interfaces that standardize how the application
    interacts with entity storage, providing a consistent contract for all entity
    repositories regardless of their underlying storage implementation.

Requirements:
    - Must define a contract for basic CRUD operations for all entity types
    - Must provide specialized interfaces for each major entity type
    - Must define standard exceptions for common repository errors
    - CRITICAL: Must maintain backward compatibility for existing implementations
    - CRITICAL: Any change to these interfaces affects all repository implementations

Changes:
    - v1: Initial interface definition with base repository methods
    - v2: Added specialized repository interfaces for each entity type
    - v3: Enhanced with query methods for filtering and relationship traversal
    - v4: Improved documentation and type annotations
    - v5: Added support for advanced search operations

Lessons Learned:
    - Well-defined interfaces enable multiple implementations (file, API, database)
    - Generic types with type variables enable compile-time type checking
    - Specialized exceptions improve error handling in client code
    - Interface segregation (specialized interfaces) improves code organization
"""

import abc
from typing import Dict, List, Any, Optional, Generic, TypeVar, Union, Callable, Tuple

from refactor.core.entities.base_entity import BaseEntity


# Define the entity type variable for generic implementations
T = TypeVar('T', bound=BaseEntity)


class RepositoryError(Exception):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Repository Implementations: Raised for general repository errors
        - Error Handlers: For catching and handling repository-specific errors
        - Service Layer: For wrapping and propagating repository errors
    
    Purpose:
        Base exception class for repository-related errors, providing a common
        type that can be caught to handle any repository error while enabling
        more specific exception types for detailed error handling.
    
    Requirements:
        - Must be the parent class for all repository-specific exceptions
        - Should include informative error messages
        - Should be used sparingly in favor of more specific subclasses
    """
    pass


class EntityNotFoundError(RepositoryError):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Repository Implementations: Raised when an entity cannot be found
        - Service Layer: For detecting and handling missing entity cases
        - Commands: For providing user-friendly error messages
    
    Purpose:
        Specific exception raised when attempting to access or manipulate
        an entity that does not exist in the repository, allowing client
        code to handle this common case separately from other errors.
    
    Requirements:
        - Must include entity ID in error message
        - Should indicate entity type when possible
        - Should be caught and handled gracefully in client code
    """
    pass


class EntityAlreadyExistsError(RepositoryError):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Repository Implementations: Raised when trying to add a duplicate entity
        - Service Layer: For preventing duplicate entities
        - Commands: For providing user-friendly error messages
    
    Purpose:
        Specific exception raised when attempting to add an entity with an ID
        that already exists in the repository, preventing unintentional overwrites
        and maintaining data integrity.
    
    Requirements:
        - Must include entity ID in error message
        - Should indicate entity type when possible
        - Should be caught and handled appropriately in client code
    """
    pass


class ValidationError(RepositoryError):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Repository Implementations: Raised when entity validation fails
        - Service Layer: For validating entities before storage
        - Commands: For providing user-friendly validation error messages
    
    Purpose:
        Specific exception raised when an entity fails validation before
        being added or updated in the repository, preventing invalid data
        from entering the system.
    
    Requirements:
        - Must include detailed validation failure reason
        - Should include entity ID when available
        - Should include specific field or rule that caused validation failure
    """
    pass


class IRepository(Generic[T], abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Concrete Repository Implementations: Implement this interface
        - Service Layer: Depends on this interface for dependency injection
        - Core Manager: Uses this interface to access repositories
    
    Purpose:
        Generic interface that defines the standard contract for all entity repositories,
        providing a consistent set of operations for entity management regardless of
        the underlying storage implementation or entity type.
    
    Requirements:
        - Must support all basic CRUD operations
        - Must enforce entity validation
        - Must define consistent exception behavior
        - Must be implemented by all entity repositories
        - CRITICAL: Interface changes impact all repository implementations
    
    Changes:
        - v1: Initial definition with basic CRUD methods
        - v2: Added query capabilities with find method
        - v3: Enhanced documentation and type annotations
    """
    
    @abc.abstractmethod
    def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.
        
        Validates and stores a new entity, assigning an ID if not already present.
        
        Args:
            entity: Entity to add to the repository
            
        Returns:
            The added entity (possibly with generated ID)
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity fails validation
            
        Requirements:
            - Must validate entity before adding
            - Must check for duplicate IDs
            - Must generate ID if not present
            - Must update internal indexes if applicable
        """
        pass
    
    @abc.abstractmethod
    def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository.
        
        Validates and updates an existing entity with new data while
        maintaining its identity (ID).
        
        Args:
            entity: Entity with updated data
            
        Returns:
            The updated entity
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the entity fails validation
            
        Requirements:
            - Must validate entity before updating
            - Must verify entity exists
            - Must update internal indexes if applicable
            - Must not change entity ID
        """
        pass
    
    @abc.abstractmethod
    def get(self, entity_id: str) -> T:
        """
        Get an entity by its ID.
        
        Retrieves an entity with the exact ID provided.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            The entity with the given ID
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
            
        Requirements:
            - Must validate entity_id format if applicable
            - Must provide clear error message if not found
        """
        pass
    
    @abc.abstractmethod
    def get_by_name(self, name: str) -> T:
        """
        Get an entity by its name.
        
        Retrieves an entity with the exact name provided.
        
        Args:
            name: Name of the entity to retrieve
            
        Returns:
            The entity with the given name
            
        Raises:
            EntityNotFoundError: If no entity with the given name exists
            
        Requirements:
            - Must handle case where multiple entities have the same name
            - Must provide clear error message if not found
        """
        pass
    
    @abc.abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            entity_id: ID to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
            
        Requirements:
            - Must be efficient (should not load the entire entity)
            - Must handle empty/invalid entity_id gracefully
        """
        pass
    
    @abc.abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by its ID.
        
        Removes an entity from the repository if it exists.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it didn't exist
            
        Requirements:
            - Must update any related indexes
            - Must not fail if entity doesn't exist
            - Must clean up any related resources
        """
        pass
    
    @abc.abstractmethod
    def list_all(self) -> List[T]:
        """
        Get all entities in the repository.
        
        Returns:
            List of all entities
            
        Requirements:
            - Must handle empty repository gracefully
            - Must return a copy of entities when applicable to prevent inadvertent modification
        """
        pass
    
    @abc.abstractmethod
    def count(self) -> int:
        """
        Get the number of entities in the repository.
        
        Returns:
            Number of entities
            
        Requirements:
            - Must be efficient (should not load all entities if possible)
        """
        pass
    
    @abc.abstractmethod
    def find(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Find entities that match a predicate.
        
        Filters entities using a function that examines each entity
        and returns True for those that should be included.
        
        Args:
            predicate: Function that takes an entity and returns True for matches
            
        Returns:
            List of matching entities
            
        Requirements:
            - Must handle empty repository gracefully
            - Must handle empty result set gracefully
            - predicate must be a callable that accepts entity parameter
        """
        pass

# Create an alias for compatibility with existing code
# This allows code that imports Repository to work without changes
Repository = IRepository

# Create an alias for EntityRepository for compatibility with older code
EntityRepository = IRepository


class ITaskRepository(IRepository['TaskEntity'], abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Task Repository Implementations: Implement this specialized interface
        - Task Service: Depends on this interface for task-specific operations
        - Core Manager: Uses this interface to access task repositories
    
    Purpose:
        Specialized repository interface for task entities, extending the base
        repository interface with task-specific operations like filtering by
        status, priority, tags, and handling task relationships.
    
    Requirements:
        - Must support all base repository operations
        - Must provide task-specific query capabilities
        - Must handle task relationships (parent-child, dependencies)
        - Must implement efficient filtering for task attributes
    
    Changes:
        - v1: Initial definition with basic task filtering
        - v2: Added relationship querying (subtasks, dependencies)
        - v3: Added advanced search capabilities
    """
    
    @abc.abstractmethod
    def get_by_status(self, status: str) -> List['TaskEntity']:
        """
        Get tasks with a specific status.
        
        Retrieves all tasks that have the specified status.
        
        Args:
            status: Status to filter by (string or TaskStatus enum)
            
        Returns:
            List of tasks with the given status
            
        Requirements:
            - Must handle both string and enum status values
            - Must return empty list if no matches
        """
        pass
    
    @abc.abstractmethod
    def get_by_priority(self, priority: int) -> List['TaskEntity']:
        """
        Get tasks with a specific priority.
        
        Retrieves all tasks that have the specified priority level.
        
        Args:
            priority: Priority to filter by (int or TaskPriority enum)
            
        Returns:
            List of tasks with the given priority
            
        Requirements:
            - Must handle both integer and enum priority values
            - Must return empty list if no matches
        """
        pass
    
    @abc.abstractmethod
    def get_by_tag(self, tag: str) -> List['TaskEntity']:
        """
        Get tasks with a specific tag.
        
        Retrieves all tasks that have the specified tag in their tags list.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of tasks with the given tag
            
        Requirements:
            - Must match tags exactly (case-sensitive)
            - Must return empty list if no matches
        """
        pass
    
    @abc.abstractmethod
    def get_subtasks(self, parent_id: str) -> List['TaskEntity']:
        """
        Get all subtasks of a given task.
        
        Retrieves all tasks that have the specified task as their parent.
        
        Args:
            parent_id: ID of the parent task
            
        Returns:
            List of subtasks
            
        Raises:
            EntityNotFoundError: If the parent task doesn't exist
            
        Requirements:
            - Must verify parent task exists
            - Must return empty list if no subtasks
        """
        pass
    
    @abc.abstractmethod
    def get_related_tasks(self, task_id: str, relationship_type: str) -> List['TaskEntity']:
        """
        Get tasks related to a given task by a specific relationship type.
        
        Retrieves tasks that have a specific relationship with the given task,
        such as dependencies or blockers.
        
        Args:
            task_id: ID of the task to get related tasks for
            relationship_type: Type of relationship (e.g., 'depends_on', 'blocks')
            
        Returns:
            List of related tasks
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            
        Requirements:
            - Must verify task exists
            - Must handle unknown relationship types gracefully
            - Must return empty list if no related tasks
        """
        pass
    
    @abc.abstractmethod
    def search(self, 
              query: str, 
              statuses: Optional[List[str]] = None,
              priorities: Optional[List[int]] = None,
              tags: Optional[List[str]] = None,
              parent_id: Optional[str] = None) -> List['TaskEntity']:
        """
        Search for tasks using multiple criteria.
        
        Performs a multi-criteria search across tasks, filtering by text content,
        status, priority, tags, and parent-child relationships.
        
        Args:
            query: Text to search for in task name and description
            statuses: Optional list of statuses to include
            priorities: Optional list of priorities to include
            tags: Optional list of tags to filter by
            parent_id: Optional parent task ID to filter by
            
        Returns:
            List of tasks matching the search criteria
            
        Requirements:
            - Must apply criteria as AND operations (all must match)
            - Must handle empty/None parameters by not applying that filter
            - Text search should be case-insensitive
            - Must return empty list if no matches
        """
        pass


class IListRepository(IRepository['ListEntity'], abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - List Repository Implementations: Implement this specialized interface
        - List Service: Depends on this interface for list-specific operations
        - Core Manager: Uses this interface to access list repositories
    
    Purpose:
        Specialized repository interface for list entities, extending the base
        repository interface with list-specific operations like filtering by
        folder and accessing tasks within a list.
    
    Requirements:
        - Must support all base repository operations
        - Must provide folder-based filtering
        - Must handle list-task relationships
    """
    
    @abc.abstractmethod
    def get_by_folder(self, folder_id: str) -> List['ListEntity']:
        """
        Get all lists in a folder.
        
        Retrieves all lists that belong to the specified folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of lists in the specified folder
            
        Raises:
            EntityNotFoundError: If the folder doesn't exist
            
        Requirements:
            - Must verify folder exists
            - Must return empty list if folder has no lists
        """
        pass
    
    @abc.abstractmethod
    def get_tasks(self, list_id: str) -> List['TaskEntity']:
        """
        Get all tasks in a list.
        
        Retrieves all tasks that belong to the specified list.
        
        Args:
            list_id: ID of the list to get tasks for
            
        Returns:
            List of tasks in the specified list
            
        Raises:
            EntityNotFoundError: If the list doesn't exist
            
        Requirements:
            - Must verify list exists
            - Must return empty list if list has no tasks
        """
        pass


class IFolderRepository(IRepository['FolderEntity'], abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Folder Repository Implementations: Implement this specialized interface
        - Folder Service: Depends on this interface for folder-specific operations
        - Core Manager: Uses this interface to access folder repositories
    
    Purpose:
        Specialized repository interface for folder entities, extending the base
        repository interface with folder-specific operations like filtering by
        space and accessing lists within a folder.
    
    Requirements:
        - Must support all base repository operations
        - Must provide space-based filtering
        - Must handle folder-list relationships
    """
    
    @abc.abstractmethod
    def get_by_space(self, space_id: str) -> List['FolderEntity']:
        """
        Get all folders in a space.
        
        Retrieves all folders that belong to the specified space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folders in the specified space
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
            
        Requirements:
            - Must verify space exists
            - Must return empty list if space has no folders
        """
        pass
    
    @abc.abstractmethod
    def get_lists(self, folder_id: str) -> List['ListEntity']:
        """
        Get all lists in a folder.
        
        Retrieves all lists that belong to the specified folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of lists in the folder
            
        Raises:
            EntityNotFoundError: If the folder doesn't exist
            
        Requirements:
            - Must verify folder exists
            - Must return empty list if folder has no lists
        """
        pass


class ISpaceRepository(IRepository['SpaceEntity'], abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/repositories/repository_interface.py
    dohcount: 1
    
    Used By:
        - Space Repository Implementations: Implement this specialized interface
        - Space Service: Depends on this interface for space-specific operations
        - Core Manager: Uses this interface to access space repositories
    
    Purpose:
        Specialized repository interface for space entities, extending the base
        repository interface with space-specific operations like accessing folders
        and lists within a space.
    
    Requirements:
        - Must support all base repository operations
        - Must handle space-folder and space-list relationships
    """
    
    @abc.abstractmethod
    def get_folders(self, space_id: str) -> List['FolderEntity']:
        """
        Get all folders in a space.
        
        Retrieves all folders that belong to the specified space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folders in the space
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
            
        Requirements:
            - Must verify space exists
            - Must return empty list if space has no folders
        """
        pass
    
    @abc.abstractmethod
    def get_lists(self, space_id: str) -> List['ListEntity']:
        """
        Get all lists in a space.
        
        Retrieves all lists that belong to the specified space, across all folders.
        
        Args:
            space_id: ID of the space to get lists for
            
        Returns:
            List of lists in the space
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
            
        Requirements:
            - Must verify space exists
            - Must return empty list if space has no lists
            - Must include lists from all folders in the space
        """
        pass 