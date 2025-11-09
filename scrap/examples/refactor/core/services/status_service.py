"""
Status Service Module - Provides service layer for task status operations.

This module implements the StatusService class which handles all task status-related
operations, including status transitions, validation, and history tracking.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime

from ..entities.task_entity import TaskEntity, TaskStatus, StatusHistoryEntry
from ..repositories.repository_interface import ITaskRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class StatusServiceError(Exception):
    """Base exception for status service errors."""
    pass


class InvalidStatusTransitionError(StatusServiceError):
    """Exception raised when a status transition is invalid."""
    pass


class StatusValidationError(StatusServiceError):
    """Exception raised when status validation fails."""
    pass


class StatusWorkflowError(StatusServiceError):
    """Exception raised for workflow-related errors."""
    pass


class StatusService:
    """
    Service for managing task statuses.
    
    This service provides methods for changing task statuses,
    validating status transitions, and tracking status history.
    """
    
    def __init__(self, task_repository: ITaskRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the status service.
        
        Args:
            task_repository: Repository for task operations
            logger: Optional logger for service operations
        """
        self.task_repository = task_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
        
        # Define default status transition rules
        self._default_transitions = {
            TaskStatus.TO_DO: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETE, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.TO_DO, TaskStatus.COMPLETE, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
            TaskStatus.BLOCKED: {TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETE, TaskStatus.CANCELLED},
            TaskStatus.COMPLETE: {TaskStatus.TO_DO, TaskStatus.IN_PROGRESS},
            TaskStatus.CANCELLED: {TaskStatus.TO_DO, TaskStatus.IN_PROGRESS}
        }
        
        # Custom workflow rules - can be modified at runtime
        self._custom_transitions = {}
    
    def update_task_status(self, task_id: str, new_status: TaskStatus, 
                          comment: Optional[str] = None) -> TaskEntity:
        """
        Update a task's status.
        
        Args:
            task_id: ID of the task to update
            new_status: New status for the task
            comment: Optional comment explaining the status change
            
        Returns:
            The updated task entity
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            InvalidStatusTransitionError: If the status transition is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                current_status = task.status
                
                # Skip if status hasn't changed
                if current_status == new_status:
                    self.logger.info(f"Task {task_id} status already set to {new_status.value}")
                    return task
                
                # Run pre-update hooks
                hook_data = {
                    "task_id": task_id,
                    "task": task,
                    "old_status": current_status,
                    "new_status": new_status,
                    "comment": comment
                }
                self.hook_registry.execute_hook("pre_status_update", hook_data)
                
                # Get updated values from hooks
                new_status = hook_data["new_status"]
                comment = hook_data["comment"]
                
                # Validate the transition
                if not self.is_valid_transition(current_status, new_status, task_id):
                    raise InvalidStatusTransitionError(
                        f"Invalid status transition: {current_status.value} -> {new_status.value} for task {task_id}"
                    )
                
                # Create history entry
                history_entry = StatusHistoryEntry(
                    from_status=current_status,
                    to_status=new_status,
                    timestamp=datetime.now(),
                    comment=comment or ""
                )
                
                # Update the task
                task.status = new_status
                task.add_status_history_entry(history_entry)
                
                # Save the task
                updated_task = self.task_repository.update(task)
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_status_update", 
                    {
                        "task": updated_task,
                        "old_status": current_status,
                        "new_status": new_status,
                        "history_entry": history_entry
                    }
                )
                
                self.logger.info(f"Updated task {task_id} status: {current_status.value} -> {new_status.value}")
                return updated_task
                
        except (EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error updating task status: {str(e)}")
            raise
    
    def is_valid_transition(self, current_status: TaskStatus, new_status: TaskStatus, 
                          task_id: Optional[str] = None) -> bool:
        """
        Check if a status transition is valid.
        
        Args:
            current_status: Current status of the task
            new_status: New status for the task
            task_id: Optional task ID for custom workflow validation
            
        Returns:
            True if the transition is valid, False otherwise
        """
        # Use custom workflow if available for this task
        if task_id and task_id in self._custom_transitions:
            workflow = self._custom_transitions[task_id]
            if current_status in workflow:
                return new_status in workflow[current_status]
        
        # Use default workflow
        if current_status in self._default_transitions:
            return new_status in self._default_transitions[current_status]
        
        # Unknown status
        return False
    
    def get_valid_transitions(self, task_id: str) -> List[TaskStatus]:
        """
        Get all valid status transitions for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of valid status values the task can transition to
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                current_status = task.status
                
                # Use custom workflow if available for this task
                if task_id in self._custom_transitions and current_status in self._custom_transitions[task_id]:
                    return list(self._custom_transitions[task_id][current_status])
                
                # Use default workflow
                if current_status in self._default_transitions:
                    return list(self._default_transitions[current_status])
                
                # Unknown status
                return []
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error getting valid transitions: {str(e)}")
            raise
    
    def get_status_history(self, task_id: str) -> List[StatusHistoryEntry]:
        """
        Get the status history for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of status history entries
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                return task.status_history
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error getting status history: {str(e)}")
            raise
    
    def define_custom_workflow(self, task_id: str, 
                              transitions: Dict[TaskStatus, Set[TaskStatus]]) -> None:
        """
        Define a custom workflow for a specific task.
        
        Args:
            task_id: ID of the task
            transitions: Dictionary mapping current statuses to sets of allowed next statuses
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            StatusWorkflowError: If the workflow definition is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task to ensure it exists
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Validate the workflow
                for from_status, to_statuses in transitions.items():
                    if not isinstance(from_status, TaskStatus):
                        raise StatusWorkflowError(f"Invalid status in workflow: {from_status}")
                    
                    for to_status in to_statuses:
                        if not isinstance(to_status, TaskStatus):
                            raise StatusWorkflowError(f"Invalid status in workflow: {to_status}")
                
                # Store the custom workflow
                self._custom_transitions[task_id] = transitions
                
                self.logger.info(f"Defined custom workflow for task {task_id}")
                
        except (EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error defining custom workflow: {str(e)}")
            raise
    
    def remove_custom_workflow(self, task_id: str) -> None:
        """
        Remove a custom workflow for a specific task.
        
        Args:
            task_id: ID of the task
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task to ensure it exists
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Remove the custom workflow
                if task_id in self._custom_transitions:
                    del self._custom_transitions[task_id]
                
                self.logger.info(f"Removed custom workflow for task {task_id}")
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error removing custom workflow: {str(e)}")
            raise
    
    def update_default_workflow(self, transitions: Dict[TaskStatus, Set[TaskStatus]]) -> None:
        """
        Update the default workflow for all tasks.
        
        Args:
            transitions: Dictionary mapping current statuses to sets of allowed next statuses
            
        Raises:
            StatusWorkflowError: If the workflow definition is invalid
        """
        try:
            with self._lock:
                # Validate the workflow
                for from_status, to_statuses in transitions.items():
                    if not isinstance(from_status, TaskStatus):
                        raise StatusWorkflowError(f"Invalid status in workflow: {from_status}")
                    
                    for to_status in to_statuses:
                        if not isinstance(to_status, TaskStatus):
                            raise StatusWorkflowError(f"Invalid status in workflow: {to_status}")
                
                # Update the default workflow
                self._default_transitions = transitions
                
                self.logger.info("Updated default workflow")
                
        except ValidationError as e:
            self.logger.error(f"Error updating default workflow: {str(e)}")
            raise
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskEntity]:
        """
        Get all tasks with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        with self._lock:
            # Get all tasks with the specified status
            tasks = self.task_repository.get_by_status(status)
            return tasks
    
    def complete_task(self, task_id: str, comment: Optional[str] = None) -> TaskEntity:
        """
        Mark a task as complete.
        
        Args:
            task_id: ID of the task to complete
            comment: Optional comment explaining the completion
            
        Returns:
            The updated task entity
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            InvalidStatusTransitionError: If the task cannot be marked as complete
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Run pre-complete hooks
                hook_data = {
                    "task_id": task_id,
                    "task": task,
                    "comment": comment
                }
                self.hook_registry.execute_hook("pre_task_complete", hook_data)
                
                # Check if the task can be marked as complete
                if not self.is_valid_transition(task.status, TaskStatus.COMPLETE, task_id):
                    raise InvalidStatusTransitionError(
                        f"Cannot mark task {task_id} as complete from status {task.status.value}"
                    )
                
                # Update the task status
                return self.update_task_status(task_id, TaskStatus.COMPLETE, 
                                            hook_data["comment"] or "Task completed")
                
        except (EntityNotFoundError, InvalidStatusTransitionError) as e:
            self.logger.error(f"Error completing task: {str(e)}")
            raise
    
    def start_task(self, task_id: str, comment: Optional[str] = None) -> TaskEntity:
        """
        Mark a task as in progress.
        
        Args:
            task_id: ID of the task to start
            comment: Optional comment explaining the start
            
        Returns:
            The updated task entity
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            InvalidStatusTransitionError: If the task cannot be marked as in progress
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Run pre-start hooks
                hook_data = {
                    "task_id": task_id,
                    "task": task,
                    "comment": comment
                }
                self.hook_registry.execute_hook("pre_task_start", hook_data)
                
                # Check if the task can be marked as in progress
                if not self.is_valid_transition(task.status, TaskStatus.IN_PROGRESS, task_id):
                    raise InvalidStatusTransitionError(
                        f"Cannot mark task {task_id} as in progress from status {task.status.value}"
                    )
                
                # Update the task status
                return self.update_task_status(task_id, TaskStatus.IN_PROGRESS, 
                                           hook_data["comment"] or "Task started")
                
        except (EntityNotFoundError, InvalidStatusTransitionError) as e:
            self.logger.error(f"Error starting task: {str(e)}")
            raise
    
    def block_task(self, task_id: str, reason: str) -> TaskEntity:
        """
        Mark a task as blocked.
        
        Args:
            task_id: ID of the task to block
            reason: Reason why the task is blocked
            
        Returns:
            The updated task entity
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            InvalidStatusTransitionError: If the task cannot be marked as blocked
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Run pre-block hooks
                hook_data = {
                    "task_id": task_id,
                    "task": task,
                    "reason": reason
                }
                self.hook_registry.execute_hook("pre_task_block", hook_data)
                
                # Check if the task can be marked as blocked
                if not self.is_valid_transition(task.status, TaskStatus.BLOCKED, task_id):
                    raise InvalidStatusTransitionError(
                        f"Cannot mark task {task_id} as blocked from status {task.status.value}"
                    )
                
                # Update the task status
                return self.update_task_status(task_id, TaskStatus.BLOCKED, 
                                            f"Blocked: {hook_data['reason']}")
                
        except (EntityNotFoundError, InvalidStatusTransitionError) as e:
            self.logger.error(f"Error blocking task: {str(e)}")
            raise
    
    def cancel_task(self, task_id: str, reason: str) -> TaskEntity:
        """
        Mark a task as cancelled.
        
        Args:
            task_id: ID of the task to cancel
            reason: Reason why the task is cancelled
            
        Returns:
            The updated task entity
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            InvalidStatusTransitionError: If the task cannot be marked as cancelled
        """
        try:
            with self._lock:
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Run pre-cancel hooks
                hook_data = {
                    "task_id": task_id,
                    "task": task,
                    "reason": reason
                }
                self.hook_registry.execute_hook("pre_task_cancel", hook_data)
                
                # Check if the task can be marked as cancelled
                if not self.is_valid_transition(task.status, TaskStatus.CANCELLED, task_id):
                    raise InvalidStatusTransitionError(
                        f"Cannot mark task {task_id} as cancelled from status {task.status.value}"
                    )
                
                # Update the task status
                return self.update_task_status(task_id, TaskStatus.CANCELLED, 
                                            f"Cancelled: {hook_data['reason']}")
                
        except (EntityNotFoundError, InvalidStatusTransitionError) as e:
            self.logger.error(f"Error cancelling task: {str(e)}")
            raise 