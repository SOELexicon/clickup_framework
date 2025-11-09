"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/services/checklist_service.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)
    - stk_0c06fedb - Analyze Performance Bottlenecks (related)

Used By:
    - Core Manager: For checklist operations in the facade layer
    - CLI Commands: For implementing checklist-related commands
    - Task Service: For operations involving task checklists
    - Plugin System: For extending checklist behavior via hooks

Purpose:
    Provides comprehensive management of checklists and checklist items,
    allowing creation, modification, and status tracking of implementation
    steps associated with tasks, handling both the business logic and
    data validation for checklist operations.

Requirements:
    - Must maintain referential integrity between tasks and checklists
    - Must enforce validation rules for checklist operations
    - Must handle batch operations efficiently
    - Must support hooks for customizing checklist behavior
    - CRITICAL: Must prevent orphaned checklists (no parent task)
    - CRITICAL: Must handle completed/uncompleted state changes correctly

Changes:
    - v1: Initial implementation with basic checklist operations
    - v2: Added support for item reordering and batch operations
    - v3: Enhanced hook system integration
    - v4: Added timestamp tracking for check/uncheck operations
    - v5: Added support for multiple checklist items selection
    - v6: Optimized batch operations for performance

Lessons Learned:
    - Maintaining proper parent-child relationships is essential for data integrity
    - Hook integration enables powerful custom behaviors (like task completion)
    - Tracking operation timestamps provides valuable metrics
    - Batch operations significantly improve performance for large checklists
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set, Tuple

from ..entities.task_entity import TaskEntity
from ..entities.checklist_entity import ChecklistEntity as Checklist, ChecklistItemEntity as ChecklistItem
from ..repositories.repository_interface import ITaskRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class ChecklistServiceError(Exception):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/services/checklist_service.py
    dohcount: 1
    
    Used By:
        - ChecklistService: For raising checklist-specific errors
        - Core Manager: For handling and propagating checklist errors
        - Error Handlers: For catching and processing checklist-specific errors
    
    Purpose:
        Specialized exception class for errors occurring in the checklist service,
        providing detailed information about what went wrong during checklist
        operations for proper error handling and debugging.
    
    Requirements:
        - Must include context about the specific checklist operation that failed
        - Should include relevant IDs (checklist, task, item) when available
        - Should provide enough information for debugging
    """
    pass


class ChecklistNotFoundError(ChecklistServiceError):
    """Exception raised when a checklist is not found."""
    pass


class ChecklistItemNotFoundError(ChecklistServiceError):
    """Exception raised when a checklist item is not found."""
    pass


class ChecklistValidationError(ChecklistServiceError):
    """Exception raised when checklist validation fails."""
    pass


class ChecklistService:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/services/checklist_service.py
    dohcount: 1
    
    Used By:
        - Core Manager: For performing operations on checklists
        - CLI Commands: For implementing checklist commands
        - Dashboard: For displaying checklist progress
    
    Purpose:
        Manages all operations related to checklists and checklist items,
        including creation, modification, status tracking, and validation.
        Ensures proper relationships between tasks, checklists, and items.
    
    Requirements:
        - Must validate all operations against business rules
        - Must maintain parent-child relationships
        - Must track check/uncheck operations with timestamps
        - Must support batch operations for efficiency
        - Must trigger appropriate hooks for extensibility
        - CRITICAL: Must prevent orphaned checklists and items
        - CRITICAL: Must maintain consistent checked state between UI and storage
    
    Changes:
        - v1: Initial implementation with basic operations
        - v2: Added support for checklist item reordering
        - v3: Enhanced validation rules
        - v4: Added batch operations support
        - v5: Optimized performance for large checklists
    """
    
    def __init__(self, task_repository: ITaskRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the checklist service.
        
        Args:
            task_repository: Repository for task operations
            logger: Optional logger for service operations
        """
        self.task_repository = task_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def create_checklist(self, task_id: str, name: str) -> Checklist:
        """
        Create a new checklist for a task.
        
        Args:
            task_id: ID of the task to add the checklist to
            name: Name of the checklist
            
        Returns:
            The created checklist
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistValidationError: If the checklist data is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(name, "Checklist name")
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Run pre-create hooks
                hook_data = {"task_id": task_id, "name": name}
                self.hook_registry.execute_hook("pre_checklist_create", hook_data)
                
                # Create the checklist
                checklist = Checklist(
                    name=hook_data["name"],
                    items=[]
                )
                
                # Add to task
                task.add_checklist(checklist)
                
                # Save to repository
                updated_task = self.task_repository.update(task)
                
                # Find the newly created checklist
                saved_checklist = next(
                    (cl for cl in updated_task.checklists if cl.name == hook_data["name"]),
                    None
                )
                
                if not saved_checklist:
                    raise ChecklistServiceError("Failed to create checklist")
                
                # Run post-create hooks
                self.hook_registry.execute_hook(
                    "post_checklist_create", 
                    {"task_id": task_id, "checklist": saved_checklist}
                )
                
                self.logger.info(f"Created checklist '{name}' for task {task_id}")
                return saved_checklist
                
        except ValidationError as e:
            self.logger.error(f"Validation error creating checklist: {str(e)}")
            raise ChecklistValidationError(f"Invalid checklist data: {str(e)}")
    
    def get_checklist(self, task_id: str, checklist_id: str) -> Checklist:
        """
        Get a checklist by its ID.
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist to retrieve
            
        Returns:
            The checklist
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist = next(
                    (cl for cl in task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not checklist:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                return checklist
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def get_checklists(self, task_id: str) -> List[Checklist]:
        """
        Get all checklists for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of checklists
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                return task.checklists
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def update_checklist(self, task_id: str, checklist_id: str, name: Optional[str] = None) -> Checklist:
        """
        Update a checklist.
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist to update
            name: New name for the checklist
            
        Returns:
            The updated checklist
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ChecklistValidationError: If the update data is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                if name is not None:
                    validate_not_empty(name, "Checklist name")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                checklist = task.checklists[checklist_index]
                
                # Prepare update data
                update_data = {}
                if name is not None:
                    update_data["name"] = name
                
                # Run pre-update hooks
                hook_data = {"task_id": task_id, "checklist_id": checklist_id, "updates": update_data}
                self.hook_registry.execute_hook("pre_checklist_update", hook_data)
                
                # Apply updates
                for key, value in hook_data["updates"].items():
                    setattr(checklist, key, value)
                
                # Save to repository
                updated_task = self.task_repository.update(task)
                
                # Find the updated checklist
                updated_checklist = next(
                    (cl for cl in updated_task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not updated_checklist:
                    raise ChecklistServiceError("Failed to update checklist")
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_checklist_update", 
                    {
                        "task_id": task_id, 
                        "checklist": updated_checklist, 
                        "updated_fields": list(update_data.keys())
                    }
                )
                
                self.logger.info(f"Updated checklist {checklist_id} for task {task_id}")
                return updated_checklist
                
        except ValidationError as e:
            self.logger.error(f"Validation error updating checklist: {str(e)}")
            raise ChecklistValidationError(f"Invalid checklist data: {str(e)}")
    
    def delete_checklist(self, task_id: str, checklist_id: str) -> None:
        """
        Delete a checklist.
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist to delete
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                checklist = task.checklists[checklist_index]
                
                # Run pre-delete hooks
                hook_data = {"task_id": task_id, "checklist_id": checklist_id, "checklist": checklist}
                self.hook_registry.execute_hook("pre_checklist_delete", hook_data)
                
                # Delete the checklist
                del task.checklists[checklist_index]
                
                # Save to repository
                self.task_repository.update(task)
                
                # Run post-delete hooks
                self.hook_registry.execute_hook(
                    "post_checklist_delete", 
                    {"task_id": task_id, "checklist_id": checklist_id}
                )
                
                self.logger.info(f"Deleted checklist {checklist_id} from task {task_id}")
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def add_checklist_item(self, task_id: str, checklist_id: str, name: str, checked: bool = False) -> Dict:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/services/checklist_service.py
        dohcount: 1
        
        Used By:
            - Task Manager: When creating task implementation checklists
            - CLI Commands: For adding items through command line
            - UI Components: For dynamic checklist management
            - Initialization Workflows: When setting up standard task templates
        
        Purpose:
            Creates and adds a new item to an existing checklist with the specified attributes.
            New items are assigned unique GUIDs using the 'item_' prefix and are appended
            to the end of the checklist's items list, maintaining checklist integrity.
        
        Requirements:
            - Task and checklist must exist before adding the item
            - Item name must not be empty or null
            - Must generate a unique GUID for each new item
            - Must maintain the same ordering mechanism as other items
            - Must trigger appropriate lifecycle hooks
            - CRITICAL: Must update the repository atomically
            - CRITICAL: Repository write must be atomic for the entire checklist
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist to add the item to
            name: Name/text content of the checklist item
            checked: Whether the item is initially checked (default: False)
            
        Returns:
            Dictionary representing the newly created checklist item with:
            - id: Unique identifier for the item (string)
            - name: Text content of the item (string)
            - checked: Whether the item is checked (boolean)
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ValidationError: If name is empty or invalid
            RepositoryError: If updating the repository fails
            
        Side Effects:
            - Generates a new GUID for the item
            - Updates the repository with the modified checklist
            - Logs the operation
            - Triggers pre_add_checklist_item and post_add_checklist_item hooks
            
        Changes:
            - v1: Initial implementation
            - v2: Added pre/post hooks for extensibility
            - v3: Improved validation and error handling
            
        Example Usage:
            ```python
            # Add a new unchecked item
            new_item = service.add_checklist_item(
                "tsk_abc123", 
                "chk_def456", 
                "Implement validation logic"
            )
            
            # Add a new item that's already checked
            completed_item = service.add_checklist_item(
                "tsk_abc123", 
                "chk_def456", 
                "Update documentation",
                checked=True
            )
            
            # Use the returned item
            print(f"Created item {new_item['id']}: {new_item['name']}")
            ```
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(name, "Checklist item name")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                # Run pre-create hooks
                hook_data = {"task_id": task_id, "checklist_id": checklist_id, "name": name, "checked": checked}
                self.hook_registry.execute_hook("pre_checklist_item_create", hook_data)
                
                # Create the item
                item = ChecklistItem(
                    name=hook_data["name"],
                    checked=hook_data["checked"]
                )
                
                # Add to checklist
                task.checklists[checklist_index].items.append(item)
                
                # Save to repository
                updated_task = self.task_repository.update(task)
                
                # Find the newly created item
                updated_checklist = next(
                    (cl for cl in updated_task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not updated_checklist:
                    raise ChecklistServiceError("Failed to find checklist after update")
                
                item = next(
                    (it for it in updated_checklist.items if it.name == hook_data["name"]),
                    None
                )
                
                if not item:
                    raise ChecklistServiceError("Failed to add item to checklist")
                
                # Run post-create hooks
                self.hook_registry.execute_hook(
                    "post_checklist_item_create", 
                    {"task_id": task_id, "checklist_id": checklist_id, "item": item}
                )
                
                self.logger.info(f"Added item '{name}' to checklist {checklist_id} for task {task_id}")
                return item
                
        except ValidationError as e:
            self.logger.error(f"Validation error adding checklist item: {str(e)}")
            raise ChecklistValidationError(f"Invalid checklist item data: {str(e)}")
    
    def update_checklist_item(self, task_id: str, checklist_id: str, item_id: str, 
                           name: Optional[str] = None, checked: Optional[bool] = None) -> ChecklistItem:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/services/checklist_service.py
        dohcount: 1
        
        Used By:
            - CLI Commands: For checking/unchecking checklist items
            - Core Manager: For updating checklist item properties
            - Task Service: For task completion validation
        
        Purpose:
            Updates a checklist item's properties, including its name and checked status.
            This is the primary method used for checking or unchecking items, tracking
            implementation progress, and maintaining checklist state.
        
        Requirements:
            - Must validate all input parameters
            - Must locate the task, checklist, and item in a thread-safe manner
            - Must trigger appropriate hooks before and after updates
            - Must properly handle the checked state change
            - CRITICAL: Must update the task in the repository after changing item state
            - CRITICAL: Must maintain referential integrity during updates
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist containing the item
            item_id: ID of the item to update
            name: New name for the item (if None, name is not changed)
            checked: New checked status for the item (if None, checked status is not changed)
            
        Returns:
            The updated checklist item with all changes applied
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ChecklistItemNotFoundError: If the item doesn't exist
            ChecklistValidationError: If the update data is invalid
            
        Side Effects:
            - Updates the item's properties in memory
            - Persists changes to the repository
            - Triggers pre_checklist_item_update and post_checklist_item_update hooks
            - Logs the update operation
        """
        try:
            with self._lock:
                # Validate inputs
                if name is not None:
                    validate_not_empty(name, "Checklist item name")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                # Find the item
                checklist = task.checklists[checklist_index]
                item_index = next(
                    (i for i, it in enumerate(checklist.items) if it.id == item_id),
                    None
                )
                
                if item_index is None:
                    raise ChecklistItemNotFoundError(f"Checklist item with ID {item_id} not found")
                
                item = checklist.items[item_index]
                
                # Prepare update data
                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if checked is not None:
                    update_data["checked"] = checked
                
                # Run pre-update hooks
                hook_data = {
                    "task_id": task_id, 
                    "checklist_id": checklist_id, 
                    "item_id": item_id, 
                    "updates": update_data
                }
                self.hook_registry.execute_hook("pre_checklist_item_update", hook_data)
                
                # Apply updates
                for key, value in hook_data["updates"].items():
                    setattr(item, key, value)
                
                # Save to repository
                updated_task = self.task_repository.update(task)
                
                # Find the updated item
                updated_checklist = next(
                    (cl for cl in updated_task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not updated_checklist:
                    raise ChecklistServiceError("Failed to find checklist after update")
                
                updated_item = next(
                    (it for it in updated_checklist.items if it.id == item_id),
                    None
                )
                
                if not updated_item:
                    raise ChecklistServiceError("Failed to update item")
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_checklist_item_update", 
                    {
                        "task_id": task_id, 
                        "checklist_id": checklist_id, 
                        "item": updated_item, 
                        "updated_fields": list(update_data.keys())
                    }
                )
                
                self.logger.info(f"Updated item {item_id} in checklist {checklist_id} for task {task_id}")
                return updated_item
                
        except ValidationError as e:
            self.logger.error(f"Validation error updating checklist item: {str(e)}")
            raise ChecklistValidationError(f"Invalid checklist item data: {str(e)}")
    
    def delete_checklist_item(self, task_id: str, checklist_id: str, item_id: str) -> None:
        """
        Delete a checklist item.
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist containing the item
            item_id: ID of the item to delete
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ChecklistItemNotFoundError: If the item doesn't exist
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                # Find the item
                checklist = task.checklists[checklist_index]
                item_index = next(
                    (i for i, it in enumerate(checklist.items) if it.id == item_id),
                    None
                )
                
                if item_index is None:
                    raise ChecklistItemNotFoundError(f"Checklist item with ID {item_id} not found")
                
                item = checklist.items[item_index]
                
                # Run pre-delete hooks
                hook_data = {
                    "task_id": task_id, 
                    "checklist_id": checklist_id, 
                    "item_id": item_id, 
                    "item": item
                }
                self.hook_registry.execute_hook("pre_checklist_item_delete", hook_data)
                
                # Delete the item
                del checklist.items[item_index]
                
                # Save to repository
                self.task_repository.update(task)
                
                # Run post-delete hooks
                self.hook_registry.execute_hook(
                    "post_checklist_item_delete", 
                    {"task_id": task_id, "checklist_id": checklist_id, "item_id": item_id}
                )
                
                self.logger.info(f"Deleted item {item_id} from checklist {checklist_id} for task {task_id}")
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def get_checklist_item(self, task_id: str, checklist_id: str, item_id: str) -> ChecklistItem:
        """
        Get a checklist item by its ID.
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist containing the item
            item_id: ID of the item to retrieve
            
        Returns:
            The checklist item
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ChecklistItemNotFoundError: If the item doesn't exist
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist = next(
                    (cl for cl in task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not checklist:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                # Find the item
                item = next(
                    (it for it in checklist.items if it.id == item_id),
                    None
                )
                
                if not item:
                    raise ChecklistItemNotFoundError(f"Checklist item with ID {item_id} not found")
                
                return item
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def batch_update_checklist_items(self, task_id: str, checklist_id: str, 
                                  updates: List[Dict[str, Any]]) -> List[ChecklistItem]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/services/checklist_service.py
        dohcount: 1
        
        Used By:
            - CLI Commands: For checking/unchecking multiple checklist items at once
            - Core Manager: For batch updating checklist items
            - Dashboard: For updating task progress
        
        Purpose:
            Efficiently updates multiple checklist items in a single operation,
            providing significant performance improvements over individual updates
            when modifying the checked status of multiple implementation steps.
        
        Requirements:
            - Must validate all input parameters for each item
            - Must handle the operation atomically to prevent partial updates
            - Must perform the operation with a single repository update for efficiency
            - Must maintain the same hook behavior as individual updates
            - CRITICAL: Must validate all items exist before applying any changes
            - CRITICAL: Must succeed or fail as a complete unit (transactional)
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist containing the items
            updates: List of update dictionaries, each containing:
                     - 'id': Item ID (required)
                     - 'name': New item name (optional)
                     - 'checked': New checked status (optional)
            
        Returns:
            List of updated checklist items in the same order as the input updates
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            ChecklistItemNotFoundError: If any item doesn't exist
            ChecklistValidationError: If any update data is invalid
            
        Side Effects:
            - Updates multiple items' properties in memory
            - Performs a single repository update for all changes
            - Triggers pre_checklist_item_batch_update and post_checklist_item_batch_update hooks
            - Logs the batch update operation
            
        Performance:
            This method is significantly more efficient than calling update_checklist_item
            multiple times, especially for large numbers of items, as it:
            - Acquires the lock only once
            - Performs a single repository update
            - Minimizes database/storage operations
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist_index = next(
                    (i for i, cl in enumerate(task.checklists) if cl.id == checklist_id),
                    None
                )
                
                if checklist_index is None:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                checklist = task.checklists[checklist_index]
                
                # Validate updates
                for update in updates:
                    if 'id' not in update:
                        raise ChecklistValidationError("Item ID is required for batch update")
                    if 'name' in update and not update['name']:
                        raise ChecklistValidationError("Item name cannot be empty")
                
                # Run pre-batch-update hooks
                hook_data = {"task_id": task_id, "checklist_id": checklist_id, "updates": updates}
                self.hook_registry.execute_hook("pre_checklist_item_batch_update", hook_data)
                
                # Process each update
                updated_items = []
                for update in hook_data["updates"]:
                    item_id = update['id']
                    item_index = next(
                        (i for i, it in enumerate(checklist.items) if it.id == item_id),
                        None
                    )
                    
                    if item_index is None:
                        raise ChecklistItemNotFoundError(f"Checklist item with ID {item_id} not found")
                    
                    item = checklist.items[item_index]
                    
                    # Apply updates
                    if 'name' in update:
                        item.name = update['name']
                    if 'checked' in update:
                        item.checked = update['checked']
                    
                    updated_items.append(item)
                
                # Save to repository
                updated_task = self.task_repository.update(task)
                
                # Find the updated checklist
                updated_checklist = next(
                    (cl for cl in updated_task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not updated_checklist:
                    raise ChecklistServiceError("Failed to find checklist after update")
                
                # Get the updated items
                result_items = []
                for update in updates:
                    item_id = update['id']
                    item = next(
                        (it for it in updated_checklist.items if it.id == item_id),
                        None
                    )
                    
                    if item:
                        result_items.append(item)
                
                # Run post-batch-update hooks
                self.hook_registry.execute_hook(
                    "post_checklist_item_batch_update", 
                    {"task_id": task_id, "checklist_id": checklist_id, "items": result_items}
                )
                
                self.logger.info(f"Updated {len(result_items)} items in checklist {checklist_id} for task {task_id}")
                return result_items
                
        except ValidationError as e:
            self.logger.error(f"Validation error in batch update: {str(e)}")
            raise ChecklistValidationError(f"Invalid checklist item data: {str(e)}")
    
    def get_checklist_completion_status(self, task_id: str, checklist_id: str) -> Tuple[int, int]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/services/checklist_service.py
        dohcount: 1
        
        Used By:
            - Dashboard: For displaying task progress
            - Task Service: For task completion validation
            - CLI Commands: For reporting checklist status
            - Status Service: For tracking implementation progress
        
        Purpose:
            Calculates and returns the completion status of a specific checklist,
            providing the number of completed items and the total number of items,
            which is essential for tracking implementation progress and reporting.
        
        Requirements:
            - Must validate task and checklist existence
            - Must count items correctly even if checklist is empty
            - Must handle checked status consistently
            - Must be efficient for frequent status queries
            - CRITICAL: Must not modify any state during status calculation
        
        Args:
            task_id: ID of the task containing the checklist
            checklist_id: ID of the checklist to check status
            
        Returns:
            Tuple of (completed_items, total_items) where:
              - completed_items: Number of checked items in the checklist
              - total_items: Total number of items in the checklist
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            ChecklistNotFoundError: If the checklist doesn't exist
            
        Example Usage:
            ```python
            # Get completion status
            completed, total = service.get_checklist_completion_status("tsk_123", "chk_456")
            
            # Calculate percentage
            if total > 0:
                percentage = (completed / total) * 100
                print(f"Checklist is {percentage:.1f}% complete ({completed}/{total} items)")
            else:
                print("Checklist is empty")
            ```
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Find the checklist
                checklist = next(
                    (cl for cl in task.checklists if cl.id == checklist_id),
                    None
                )
                
                if not checklist:
                    raise ChecklistNotFoundError(f"Checklist with ID {checklist_id} not found")
                
                # Count items
                total_items = len(checklist.items)
                completed_items = sum(1 for item in checklist.items if item.checked)
                
                return (completed_items, total_items)
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e))
    
    def get_all_checklists_completion_status(self, task_id: str) -> Dict[str, Tuple[int, int]]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/services/checklist_service.py
        dohcount: 1
        
        Used By:
            - Dashboard: For aggregated task progress views
            - Task Service: For task completion validation across all checklists
            - Project Status Reports: For comprehensive status snapshots
            - CLI Commands: For reporting overall task completion
        
        Purpose:
            Retrieves completion status for all checklists associated with a given task,
            enabling aggregate reporting and validation of overall task progress.
            Essential for determining if a task is ready to be marked complete.
        
        Requirements:
            - Must handle tasks with no checklists gracefully
            - Must return consistent results even with concurrent checklist changes
            - Must be efficient for dashboard performance
            - Must include all checklists regardless of their visibility settings
            - CRITICAL: Must not modify any state during status calculation
        
        Args:
            task_id: ID of the task containing the checklists
            
        Returns:
            Dictionary mapping checklist IDs to tuples of (completed_items, total_items)
            Example: {'chk_123': (5, 10), 'chk_456': (0, 3)}
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            
        Example Usage:
            ```python
            # Get all checklist statuses
            checklist_statuses = service.get_all_checklists_completion_status("tsk_123")
            
            # Calculate overall completion
            total_completed = sum(completed for completed, _ in checklist_statuses.values())
            total_items = sum(total for _, total in checklist_statuses.values())
            
            if total_items > 0:
                overall_percentage = (total_completed / total_items) * 100
                print(f"Task is {overall_percentage:.1f}% complete overall")
                
                # Print individual checklists
                for checklist_id, (completed, total) in checklist_statuses.items():
                    if total > 0:
                        percentage = (completed / total) * 100
                        print(f"  Checklist {checklist_id}: {percentage:.1f}% complete")
            else:
                print("Task has no checklist items")
            ```
            
        Performance Note:
            This method retrieves all checklists in a single operation rather than making
            multiple calls to get_checklist_completion_status, which significantly
            improves performance for tasks with many checklists.
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Calculate status for each checklist
                result = {}
                for checklist in task.checklists:
                    total_items = len(checklist.items)
                    completed_items = sum(1 for item in checklist.items if item.checked)
                    result[checklist.id] = (completed_items, total_items)
                
                return result
                
        except EntityNotFoundError as e:
            self.logger.error(f"Task not found: {str(e)}")
            raise EntityNotFoundError(str(e)) 