"""
Relationship Service Module - Provides service layer for task relationship operations.

This module implements the RelationshipService class which handles all task relationship
operations, including creating and managing task dependencies, blocking relationships,
and detecting circular dependencies.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set, Tuple

from ..entities.task_entity import TaskEntity, RelationshipType
from ..repositories.repository_interface import ITaskRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class RelationshipServiceError(Exception):
    """Base exception for relationship service errors."""
    pass


class CircularDependencyError(RelationshipServiceError):
    """Exception raised when a circular dependency is detected."""
    pass


class RelationshipValidationError(RelationshipServiceError):
    """Exception raised when relationship validation fails."""
    pass


class TaskDependencyError(RelationshipServiceError):
    """Exception raised for task dependency errors."""
    pass


class RelationshipService:
    """
    Service for managing task relationships.
    
    This service provides methods for creating, updating, and deleting
    task relationships, as well as checking for circular dependencies
    and performing impact analysis.
    """
    
    def __init__(self, task_repository: ITaskRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the relationship service.
        
        Args:
            task_repository: Repository for task operations
            logger: Optional logger for service operations
        """
        self.task_repository = task_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def add_relationship(self, source_task_id: str, target_task_id: str, 
                        relationship_type: RelationshipType) -> Tuple[TaskEntity, TaskEntity]:
        """
        Add a relationship between two tasks.
        
        Args:
            source_task_id: ID of the source task
            target_task_id: ID of the target task
            relationship_type: Type of relationship to create
            
        Returns:
            Tuple of (source_task, target_task) after the relationship is added
            
        Raises:
            EntityNotFoundError: If either task doesn't exist
            CircularDependencyError: If adding the relationship would create a circular dependency
            RelationshipValidationError: If the relationship is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(source_task_id, "Source task ID")
                validate_id_format(target_task_id, "Target task ID")
                
                if source_task_id == target_task_id:
                    raise RelationshipValidationError("Cannot create a relationship with the same task")
                
                # Get both tasks
                source_task = self.task_repository.get(source_task_id)
                if not source_task:
                    raise EntityNotFoundError(f"Source task with ID {source_task_id} not found")
                
                target_task = self.task_repository.get(target_task_id)
                if not target_task:
                    raise EntityNotFoundError(f"Target task with ID {target_task_id} not found")
                
                # Check if the relationship already exists
                if source_task.has_relationship_with(target_task_id, relationship_type):
                    self.logger.info(f"Relationship already exists: {source_task_id} {relationship_type.value} {target_task_id}")
                    return (source_task, target_task)
                
                # Run pre-add hooks
                hook_data = {
                    "source_task_id": source_task_id,
                    "target_task_id": target_task_id,
                    "relationship_type": relationship_type
                }
                self.hook_registry.execute_hook("pre_relationship_add", hook_data)
                
                # Check for circular dependencies if this is a dependency relationship
                if relationship_type == RelationshipType.DEPENDS_ON:
                    if self._would_create_circular_dependency(source_task_id, target_task_id):
                        raise CircularDependencyError(
                            f"Adding dependency from {source_task_id} to {target_task_id} would create a circular dependency"
                        )
                
                # Add the relationship
                source_task.add_relationship(target_task_id, relationship_type)
                
                # Add the inverse relationship if needed
                if relationship_type == RelationshipType.DEPENDS_ON:
                    target_task.add_relationship(source_task_id, RelationshipType.BLOCKS)
                elif relationship_type == RelationshipType.BLOCKS:
                    target_task.add_relationship(source_task_id, RelationshipType.DEPENDS_ON)
                elif relationship_type == RelationshipType.RELATED_TO:
                    target_task.add_relationship(source_task_id, RelationshipType.RELATED_TO)
                elif relationship_type == RelationshipType.DOCUMENTS:
                    target_task.add_relationship(source_task_id, RelationshipType.DOCUMENTED_BY)
                elif relationship_type == RelationshipType.DOCUMENTED_BY:
                    target_task.add_relationship(source_task_id, RelationshipType.DOCUMENTS)
                
                # Save both tasks
                updated_source_task = self.task_repository.update(source_task)
                updated_target_task = self.task_repository.update(target_task)
                
                # Run post-add hooks
                self.hook_registry.execute_hook(
                    "post_relationship_add", 
                    {
                        "source_task": updated_source_task,
                        "target_task": updated_target_task,
                        "relationship_type": relationship_type
                    }
                )
                
                self.logger.info(f"Added relationship: {source_task_id} {relationship_type.value} {target_task_id}")
                return (updated_source_task, updated_target_task)
                
        except (EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error adding relationship: {str(e)}")
            raise
    
    def remove_relationship(self, source_task_id: str, target_task_id: str, 
                           relationship_type: RelationshipType) -> Tuple[TaskEntity, TaskEntity]:
        """
        Remove a relationship between two tasks.
        
        Args:
            source_task_id: ID of the source task
            target_task_id: ID of the target task
            relationship_type: Type of relationship to remove
            
        Returns:
            Tuple of (source_task, target_task) after the relationship is removed
            
        Raises:
            EntityNotFoundError: If either task doesn't exist
            RelationshipValidationError: If the relationship doesn't exist
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(source_task_id, "Source task ID")
                validate_id_format(target_task_id, "Target task ID")
                
                # Get both tasks
                source_task = self.task_repository.get(source_task_id)
                if not source_task:
                    raise EntityNotFoundError(f"Source task with ID {source_task_id} not found")
                
                target_task = self.task_repository.get(target_task_id)
                if not target_task:
                    raise EntityNotFoundError(f"Target task with ID {target_task_id} not found")
                
                # Check if the relationship exists
                if not source_task.has_relationship_with(target_task_id, relationship_type):
                    raise RelationshipValidationError(
                        f"Relationship does not exist: {source_task_id} {relationship_type.value} {target_task_id}"
                    )
                
                # Run pre-remove hooks
                hook_data = {
                    "source_task_id": source_task_id,
                    "target_task_id": target_task_id,
                    "relationship_type": relationship_type
                }
                self.hook_registry.execute_hook("pre_relationship_remove", hook_data)
                
                # Remove the relationship
                source_task.remove_relationship(target_task_id, relationship_type)
                
                # Remove the inverse relationship if needed
                if relationship_type == RelationshipType.DEPENDS_ON:
                    target_task.remove_relationship(source_task_id, RelationshipType.BLOCKS)
                elif relationship_type == RelationshipType.BLOCKS:
                    target_task.remove_relationship(source_task_id, RelationshipType.DEPENDS_ON)
                elif relationship_type == RelationshipType.RELATED_TO:
                    target_task.remove_relationship(source_task_id, RelationshipType.RELATED_TO)
                elif relationship_type == RelationshipType.DOCUMENTS:
                    target_task.remove_relationship(source_task_id, RelationshipType.DOCUMENTED_BY)
                elif relationship_type == RelationshipType.DOCUMENTED_BY:
                    target_task.remove_relationship(source_task_id, RelationshipType.DOCUMENTS)
                
                # Save both tasks
                updated_source_task = self.task_repository.update(source_task)
                updated_target_task = self.task_repository.update(target_task)
                
                # Run post-remove hooks
                self.hook_registry.execute_hook(
                    "post_relationship_remove", 
                    {
                        "source_task": updated_source_task,
                        "target_task": updated_target_task,
                        "relationship_type": relationship_type
                    }
                )
                
                self.logger.info(f"Removed relationship: {source_task_id} {relationship_type.value} {target_task_id}")
                return (updated_source_task, updated_target_task)
                
        except (EntityNotFoundError, ValidationError) as e:
            self.logger.error(f"Error removing relationship: {str(e)}")
            raise
    
    def get_relationships(self, task_id: str, relationship_type: Optional[RelationshipType] = None) -> Dict[str, List[str]]:
        """
        Get all relationships for a task.
        
        Args:
            task_id: ID of the task
            relationship_type: Optional type of relationships to get
            
        Returns:
            Dictionary mapping relationship types to lists of task IDs
            
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
                
                # Get relationships
                if relationship_type:
                    return {relationship_type.value: task.get_related_tasks(relationship_type)}
                else:
                    result = {}
                    for rel_type in RelationshipType:
                        related_tasks = task.get_related_tasks(rel_type)
                        if related_tasks:
                            result[rel_type.value] = related_tasks
                    return result
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error getting relationships: {str(e)}")
            raise
    
    def get_related_tasks(self, task_id: str, relationship_type: RelationshipType) -> List[TaskEntity]:
        """
        Get all tasks related to a task by the specified relationship type.
        
        Args:
            task_id: ID of the task
            relationship_type: Type of relationship to get
            
        Returns:
            List of related task entities
            
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
                
                # Get related task IDs
                related_task_ids = task.get_related_tasks(relationship_type)
                
                # Get task entities
                related_tasks = []
                for related_id in related_task_ids:
                    related_task = self.task_repository.get(related_id)
                    if related_task:
                        related_tasks.append(related_task)
                
                return related_tasks
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error getting related tasks: {str(e)}")
            raise
    
    def check_dependency_completion(self, task_id: str) -> bool:
        """
        Check if all dependencies of a task are completed.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            True if all dependencies are completed, False otherwise
            
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
                
                # Get dependent task IDs
                dependency_ids = task.get_related_tasks(RelationshipType.DEPENDS_ON)
                
                # Check completion of each dependency
                for dep_id in dependency_ids:
                    dep_task = self.task_repository.get(dep_id)
                    if not dep_task:
                        self.logger.warning(f"Dependency task {dep_id} not found")
                        return False
                    
                    if not dep_task.is_complete():
                        return False
                
                return True
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error checking dependency completion: {str(e)}")
            raise
    
    def get_dependency_chain(self, task_id: str, max_depth: int = 20) -> List[List[str]]:
        """
        Get all dependency chains for a task.
        
        Args:
            task_id: ID of the task
            max_depth: Maximum depth to search for dependencies
            
        Returns:
            List of dependency chains, where each chain is a list of task IDs
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
            RelationshipServiceError: If max depth is exceeded
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Get dependency chains
                chains = []
                self._get_dependency_chain_recursive(task_id, [], chains, set(), max_depth)
                return chains
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error getting dependency chain: {str(e)}")
            raise
    
    def _get_dependency_chain_recursive(self, task_id: str, current_chain: List[str], 
                                      chains: List[List[str]], visited: Set[str], max_depth: int) -> None:
        """
        Recursively get dependency chains for a task.
        
        Args:
            task_id: ID of the current task
            current_chain: Current chain of dependencies
            chains: List of all chains found
            visited: Set of already visited task IDs
            max_depth: Maximum depth to search
        """
        # Prevent infinite recursion
        if len(current_chain) > max_depth:
            raise RelationshipServiceError(f"Maximum dependency depth of {max_depth} exceeded")
        
        # Add current task to chain
        new_chain = current_chain + [task_id]
        
        # Get the task
        task = self.task_repository.get(task_id)
        if not task:
            return
        
        # Get dependent task IDs
        dependency_ids = task.get_related_tasks(RelationshipType.DEPENDS_ON)
        
        # If no dependencies, add the chain to the result
        if not dependency_ids:
            chains.append(new_chain)
            return
        
        # Process each dependency
        for dep_id in dependency_ids:
            # Skip if already in chain (circular dependency)
            if dep_id in new_chain:
                continue
            
            # Skip if already processed this path
            if dep_id in visited:
                continue
            
            # Add to visited
            visited.add(dep_id)
            
            # Recurse
            self._get_dependency_chain_recursive(dep_id, new_chain, chains, visited, max_depth)
    
    def _would_create_circular_dependency(self, source_id: str, target_id: str) -> bool:
        """
        Check if adding a dependency from source to target would create a circular dependency.
        
        Args:
            source_id: ID of the source task
            target_id: ID of the target task
            
        Returns:
            True if a circular dependency would be created, False otherwise
        """
        # Check if target depends on source (direct circular dependency)
        target_task = self.task_repository.get(target_id)
        if not target_task:
            return False
        
        if target_task.has_relationship_with(source_id, RelationshipType.DEPENDS_ON):
            return True
        
        # Check for indirect circular dependencies
        # Get all tasks that the target depends on
        tasks_to_check = target_task.get_related_tasks(RelationshipType.DEPENDS_ON)
        visited = {target_id}
        
        while tasks_to_check:
            current_id = tasks_to_check.pop(0)
            
            # If we've reached the source, there's a circular dependency
            if current_id == source_id:
                return True
            
            # Skip if already visited
            if current_id in visited:
                continue
            
            # Mark as visited
            visited.add(current_id)
            
            # Get the current task
            current_task = self.task_repository.get(current_id)
            if not current_task:
                continue
            
            # Add its dependencies to the queue
            tasks_to_check.extend(
                dep_id for dep_id in current_task.get_related_tasks(RelationshipType.DEPENDS_ON)
                if dep_id not in visited
            )
        
        return False
    
    def get_impact_analysis(self, task_id: str) -> Dict[str, List[str]]:
        """
        Perform impact analysis for a task.
        
        Args:
            task_id: ID of the task to analyze
            
        Returns:
            Dictionary mapping impact types to lists of affected task IDs
            
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
                
                result = {}
                
                # Tasks blocked by this task
                blocked_tasks = self.get_related_tasks(task_id, RelationshipType.BLOCKS)
                if blocked_tasks:
                    result["blocked"] = [t.id for t in blocked_tasks]
                
                # Tasks that depend on this task
                dependent_tasks = []
                for blocked_task in blocked_tasks:
                    dependent_tasks.append(blocked_task.id)
                    
                    # Also include tasks that depend on the blocked tasks (cascading impact)
                    cascading_deps = self._get_cascading_dependencies(blocked_task.id, set())
                    dependent_tasks.extend(cascading_deps)
                
                if dependent_tasks:
                    result["dependent"] = list(set(dependent_tasks))
                
                # Related tasks
                related_tasks = self.get_related_tasks(task_id, RelationshipType.RELATED_TO)
                if related_tasks:
                    result["related"] = [t.id for t in related_tasks]
                
                return result
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error performing impact analysis: {str(e)}")
            raise
    
    def _get_cascading_dependencies(self, task_id: str, visited: Set[str]) -> List[str]:
        """
        Get all tasks that directly or indirectly depend on a task.
        
        Args:
            task_id: ID of the task
            visited: Set of already visited task IDs
            
        Returns:
            List of task IDs that depend on the task
        """
        # Get the task
        task = self.task_repository.get(task_id)
        if not task:
            return []
        
        # Get tasks blocked by this task
        blocked_task_ids = task.get_related_tasks(RelationshipType.BLOCKS)
        
        # Filter out already visited tasks
        blocked_task_ids = [t_id for t_id in blocked_task_ids if t_id not in visited]
        
        # Add to visited
        for t_id in blocked_task_ids:
            visited.add(t_id)
        
        # Get cascading dependencies
        cascading_deps = []
        for blocked_id in blocked_task_ids:
            cascading_deps.extend(self._get_cascading_dependencies(blocked_id, visited))
        
        return blocked_task_ids + cascading_deps 