"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/data_provider.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - DashboardManager: Sources data for all dashboard components
    - InteractiveDashboard: Uses filtered data for drill-down views
    - MetricsComponent: Consumes metric calculations
    - TaskHierarchyComponent: Uses hierarchy data structure
    - RESTfulAPI: Serves dashboard data through API endpoints
    - CLI Dashboard Command: Provides task data for terminal visualization

Purpose:
    Implements data providers that supply properly formatted and processed data
    to dashboard components. Abstracts underlying data access from visualization 
    components and implements caching, data transformation, and metric calculation 
    functions needed for dashboard display.

Requirements:
    - CRITICAL: Must implement efficient caching to avoid repeated database queries
    - CRITICAL: Must handle all entity relationships correctly (task hierarchies, dependencies)
    - CRITICAL: Must not modify any entity data during metric calculations
    - All data transformation methods must be idempotent
    - Filters must be chainable and composable
    - Must gracefully handle missing repositories by returning empty results

Dashboard Data Provider Module

This module implements data providers for the dashboard components.
"""
from abc import abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import copy
import json
import hashlib
import time
from collections import defaultdict

from .dashboard_component import DataProvider
from ..core.interfaces.core_manager import CoreManager
from ..core.repositories.task_repository import TaskRepository
from ..core.repositories.list_repository import ListRepository
from ..core.repositories.folder_repository import FolderRepository
from ..core.repositories.space_repository import SpaceRepository
from ..core.entities.task_entity import TaskEntity


class TaskDataProvider(DataProvider):
    """
    Data provider that sources data from tasks in the ClickUp JSON Manager.
    """
    
    def __init__(self, 
                 task_repository: TaskRepository,
                 list_repository: Optional[ListRepository] = None,
                 folder_repository: Optional[FolderRepository] = None,
                 space_repository: Optional[SpaceRepository] = None,
                 core_manager: Optional[CoreManager] = None):
        """
        Initialize the task data provider.
        
        Args:
            task_repository: Task repository for accessing task data
            list_repository: Optional list repository for accessing list data
            folder_repository: Optional folder repository for accessing folder data
            space_repository: Optional space repository for accessing space data
            core_manager: Optional core manager for backward compatibility
        """
        self.task_repository = task_repository
        self.list_repository = list_repository
        self.folder_repository = folder_repository
        self.space_repository = space_repository
        self.core_manager = core_manager  # For backward compatibility
        self.cache = {}
        self.cache_expiry = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get task data based on the given context.
        
        Args:
            context: Context information for the data request, including:
                    - level: navigation level (root, space, folder, list, task)
                    - entity_id: ID of the current entity being viewed
                    - metrics: list of metrics to calculate
        
        Returns:
            Data for dashboard components
        """
        cache_key = self._get_cache_key(context)
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        level = context.get('level', 'root')
        entity_id = context.get('entity_id')
        metrics_to_calculate = context.get('metrics', [])
        
        # Get raw task data based on the navigation level
        tasks = self._get_tasks_by_level(level, entity_id)
        
        # Convert task entities to dictionaries
        task_dicts = [self._task_entity_to_dict(task) for task in tasks]
        
        # Build result data
        result = {
            'tasks': task_dicts,
            'raw': {
                'level': level,
                'entity_id': entity_id,
                'task_count': len(task_dicts)
            }
        }
        
        # Calculate metrics
        metrics = {}
        
        # Always include these basic metrics
        metrics['task_count'] = len(task_dicts)
        metrics['status_distribution'] = self._calculate_status_distribution(task_dicts)
        metrics['priority_distribution'] = self._calculate_priority_distribution(task_dicts)
        
        # Add additional requested metrics
        if 'completion_percentage' in metrics_to_calculate or not metrics_to_calculate:
            metrics['completion_percentage'] = self._calculate_completion_percentage(task_dicts)
        
        if 'task_type_distribution' in metrics_to_calculate:
            metrics['task_type_distribution'] = self._calculate_task_type_distribution(task_dicts)
        
        if 'tasks_by_tag' in metrics_to_calculate:
            metrics['tasks_by_tag'] = self._calculate_tasks_by_tag(task_dicts)
        
        if 'recent_activity' in metrics_to_calculate:
            metrics['recent_activity'] = self._calculate_recent_activity(task_dicts)
        
        if 'task_hierarchy' in metrics_to_calculate or not metrics_to_calculate:
            metrics['task_hierarchy'] = self._build_task_hierarchy(task_dicts)
        
        # Include task data for table view
        result['task_data'] = self._prepare_task_data_for_table(task_dicts)
        
        # Add metrics to result
        result['metrics'] = metrics
        
        # Cache the result
        self._cache_result(cache_key, result)
        
        return result
    
    def get_filtered_data(self, context: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get filtered task data.
        
        Args:
            context: Context information for the data request
            filters: Filter criteria to apply
        
        Returns:
            Filtered data for dashboard components
        """
        # Get the base data
        data = self.get_data(context)
        
        # Apply filters to tasks
        tasks = data['tasks']
        filtered_tasks = self._apply_filters(tasks, filters)
        
        # Rebuild the result with filtered tasks
        result = copy.deepcopy(data)
        result['tasks'] = filtered_tasks
        result['raw']['task_count'] = len(filtered_tasks)
        
        # Recalculate metrics with filtered tasks
        metrics = {}
        metrics['task_count'] = len(filtered_tasks)
        metrics['status_distribution'] = self._calculate_status_distribution(filtered_tasks)
        metrics['priority_distribution'] = self._calculate_priority_distribution(filtered_tasks)
        metrics['completion_percentage'] = self._calculate_completion_percentage(filtered_tasks)
        
        # Add additional metrics if they were in the original data
        if 'task_type_distribution' in data['metrics']:
            metrics['task_type_distribution'] = self._calculate_task_type_distribution(filtered_tasks)
        
        if 'tasks_by_tag' in data['metrics']:
            metrics['tasks_by_tag'] = self._calculate_tasks_by_tag(filtered_tasks)
        
        if 'recent_activity' in data['metrics']:
            metrics['recent_activity'] = self._calculate_recent_activity(filtered_tasks)
        
        if 'task_hierarchy' in data['metrics']:
            metrics['task_hierarchy'] = self._build_task_hierarchy(filtered_tasks)
        
        # Update task data for table view
        result['task_data'] = self._prepare_task_data_for_table(filtered_tasks)
        
        # Update metrics in result
        result['metrics'] = metrics
        
        return result
    
    def _get_tasks_by_level(self, level: str, entity_id: Optional[str]) -> List[TaskEntity]:
        """
        Get tasks based on the navigation level and entity ID.
        
        Args:
            level: Navigation level (root, space, folder, list, task)
            entity_id: ID of the entity to get tasks for
            
        Returns:
            List of task entities
        """
        if level == 'root':
            # At root level, get all tasks
            return self.task_repository.list_all()
        
        elif level == 'space':
            # Get tasks for a specific space
            if not entity_id or not self.space_repository:
                return []
                
            try:
                # Get lists in the space
                lists = self.space_repository.get_lists(entity_id)
                
                # Get tasks for each list
                tasks = []
                for list_entity in lists:
                    if self.list_repository:
                        list_tasks = self.list_repository.get_tasks(list_entity.id)
                        tasks.extend(list_tasks)
                return tasks
            except Exception as e:
                # If repository method fails, try using core manager as fallback
                if self.core_manager:
                    task_dicts = self.core_manager.get_tasks_by_space(entity_id)
                    return [self._dict_to_task_entity(task) for task in task_dicts]
                return []
        
        elif level == 'folder':
            # Get tasks for a specific folder
            if not entity_id or not self.folder_repository or not self.list_repository:
                return []
                
            try:
                # Get lists in the folder
                lists = self.folder_repository.get_lists(entity_id)
                
                # Get tasks for each list
                tasks = []
                for list_entity in lists:
                    list_tasks = self.list_repository.get_tasks(list_entity.id)
                    tasks.extend(list_tasks)
                return tasks
            except Exception as e:
                # If repository method fails, try using core manager as fallback
                if self.core_manager:
                    task_dicts = self.core_manager.get_tasks_by_folder(entity_id)
                    return [self._dict_to_task_entity(task) for task in task_dicts]
                return []
        
        elif level == 'list':
            # Get tasks for a specific list
            if not entity_id or not self.list_repository:
                return []
                
            try:
                return self.list_repository.get_tasks(entity_id)
            except Exception as e:
                # If repository method fails, try using core manager as fallback
                if self.core_manager:
                    task_dicts = self.core_manager.get_tasks_by_list(entity_id)
                    return [self._dict_to_task_entity(task) for task in task_dicts]
                return []
        
        elif level == 'task':
            # Get a specific task and its subtasks
            if not entity_id:
                return []
                
            try:
                # Get the task
                task = self.task_repository.get(entity_id)
                
                # Get its subtasks
                subtasks = self.task_repository.get_subtasks(entity_id)
                
                # Return task and subtasks
                return [task] + subtasks
            except Exception as e:
                # If repository method fails, try using core manager as fallback
                if self.core_manager:
                    task_dict = self.core_manager.get_task(entity_id)
                    subtask_dicts = self.core_manager.get_subtasks(entity_id)
                    task_entity = self._dict_to_task_entity(task_dict) if task_dict else None
                    subtask_entities = [self._dict_to_task_entity(subtask) for subtask in subtask_dicts]
                    if task_entity:
                        return [task_entity] + subtask_entities
                return []
        
        return []
    
    def _task_entity_to_dict(self, task: TaskEntity) -> Dict[str, Any]:
        """
        Convert a task entity to a dictionary.
        
        Args:
            task: Task entity to convert
            
        Returns:
            Dictionary representation of the task
        """
        if not task:
            return {}
            
        # Convert to dictionary using entity's to_dict method if available
        if hasattr(task, 'to_dict') and callable(getattr(task, 'to_dict')):
            return task.to_dict()
            
        # Fallback: manual conversion
        task_dict = {
            'id': task.id,
            'name': task.name,
            'status': task.status if hasattr(task, 'status') else None,
            'priority': task.priority if hasattr(task, 'priority') else None,
            'type': task.type if hasattr(task, 'type') else None,
            'tags': task.tags if hasattr(task, 'tags') else [],
            'parent_id': task.parent_id if hasattr(task, 'parent_id') else None,
            'description': task.description if hasattr(task, 'description') else None,
        }
        
        # Add other attributes that might exist
        for attr in ['list_id', 'space_id', 'folder_id', 'created_at', 'updated_at']:
            if hasattr(task, attr):
                task_dict[attr] = getattr(task, attr)
                
        return task_dict
    
    def _dict_to_task_entity(self, task_dict: Dict[str, Any]) -> TaskEntity:
        """
        Convert a dictionary to a task entity.
        
        Args:
            task_dict: Dictionary to convert
            
        Returns:
            Task entity
        """
        if not task_dict:
            return None
            
        # Use entity's from_dict method if the class is available
        return TaskEntity.from_dict(task_dict)
    
    def _apply_filters(self, tasks: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to tasks.
        
        Args:
            tasks: List of tasks to filter
            filters: Filter criteria
            
        Returns:
            Filtered list of tasks
        """
        filtered_tasks = tasks
        
        # Filter by status
        if 'status' in filters:
            status = filters['status']
            if status:
                filtered_tasks = [task for task in filtered_tasks if task.get('status') == status]
        
        # Filter by priority
        if 'priority' in filters:
            priority = filters['priority']
            if priority:
                filtered_tasks = [task for task in filtered_tasks if task.get('priority') == priority]
        
        # Filter by task type
        if 'type' in filters:
            task_type = filters['type']
            if task_type:
                filtered_tasks = [task for task in filtered_tasks if task.get('type') == task_type]
        
        # Filter by tag
        if 'tag' in filters:
            tag = filters['tag']
            if tag:
                filtered_tasks = [task for task in filtered_tasks 
                                if 'tags' in task and tag in task['tags']]
        
        # Filter by search term (in name or description)
        if 'search' in filters:
            search_term = filters['search']
            if search_term:
                search_term = search_term.lower()
                filtered_tasks = [task for task in filtered_tasks 
                                if (search_term in task.get('name', '').lower() or 
                                    search_term in task.get('description', '').lower())]
        
        # Filter by parent task
        if 'parent_id' in filters:
            parent_id = filters['parent_id']
            if parent_id:
                filtered_tasks = [task for task in filtered_tasks 
                                if task.get('parent_id') == parent_id]
        
        # Filter by date range
        if 'date_start' in filters and 'date_end' in filters:
            date_start = filters['date_start']
            date_end = filters['date_end']
            if date_start and date_end:
                date_field = filters.get('date_field', 'created_at')
                filtered_tasks = [task for task in filtered_tasks 
                                if (date_field in task and 
                                    date_start <= task.get(date_field, '') <= date_end)]
        
        return filtered_tasks
    
    def _calculate_status_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by status.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary mapping status names to task counts
        """
        distribution = defaultdict(int)
        
        for task in tasks:
            status = task.get('status', 'unknown')
            distribution[status] += 1
            
        # Convert defaultdict to regular dict for serialization
        return dict(distribution)
    
    def _calculate_priority_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by priority.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary mapping priority levels to task counts
        """
        distribution = defaultdict(int)
        
        # Priority mapping for display
        priority_mapping = {
            1: "High",
            2: "Medium",
            3: "Low",
            4: "None"
        }
        
        for task in tasks:
            priority = task.get('priority', 4)  # Default to None (4) if not specified
            priority_name = priority_mapping.get(priority, "Unknown")
            distribution[priority_name] += 1
            
        # Convert defaultdict to regular dict for serialization
        return dict(distribution)
    
    def _calculate_completion_percentage(self, tasks: List[Dict[str, Any]]) -> float:
        """
        Calculate the percentage of tasks that are marked as complete.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Completion percentage (0-100)
        """
        if not tasks:
            return 0.0
            
        completed_count = sum(1 for task in tasks if task.get('status', '').lower() == 'complete')
        total_count = len(tasks)
        
        return (completed_count / total_count) * 100 if total_count > 0 else 0.0
    
    def _calculate_task_type_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by type.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary mapping task types to counts
        """
        distribution = defaultdict(int)
        
        for task in tasks:
            task_type = task.get('type', 'unknown')
            distribution[task_type] += 1
            
        # Convert defaultdict to regular dict for serialization
        return dict(distribution)
    
    def _calculate_tasks_by_tag(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by tag.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary mapping tags to task counts
        """
        distribution = defaultdict(int)
        
        for task in tasks:
            tags = task.get('tags', [])
            for tag in tags:
                distribution[tag] += 1
                
        # Sort by count (descending) and take top 10
        sorted_distribution = dict(sorted(
            distribution.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
            
        # Convert defaultdict to regular dict for serialization
        return sorted_distribution
    
    def _calculate_recent_activity(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate recent activity over time.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary mapping date strings to task counts
        """
        # Initialize counts by date
        activity = defaultdict(int)
        
        # Get current date
        now = datetime.now()
        
        # Calculate activity for last 30 days
        for i in range(30):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            activity[date] = 0
            
        # Count tasks by creation or modification date
        for task in tasks:
            # First try to use updated_at
            if 'updated_at' in task and task['updated_at']:
                date = task['updated_at'].split('T')[0]  # Extract date part
                activity[date] += 1
            # Fall back to created_at
            elif 'created_at' in task and task['created_at']:
                date = task['created_at'].split('T')[0]  # Extract date part
                activity[date] += 1
                
        # Sort by date (chronological order)
        sorted_activity = dict(sorted(activity.items()))
            
        return sorted_activity
    
    def _build_task_hierarchy(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a hierarchical structure of tasks.
        
        Args:
            tasks: List of tasks to organize
            
        Returns:
            Hierarchical structure of tasks
        """
        # Create a map of tasks by ID for easy lookup
        task_map = {task.get('id'): task for task in tasks}
        
        # Find root tasks (those without parent or with parent not in our list)
        root_tasks = [
            task for task in tasks 
            if not task.get('parent_id') or task.get('parent_id') not in task_map
        ]
        
        # Build hierarchy
        hierarchy = {
            'root': True,
            'name': 'All Tasks',
            'children': [
                self._build_hierarchy_node(task, task_map) 
                for task in root_tasks
            ]
        }
        
        return hierarchy
    
    def _build_hierarchy_node(self, task: Dict[str, Any], task_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recursively build a hierarchy node for a task.
        
        Args:
            task: Task to build node for
            task_map: Map of tasks by ID
            
        Returns:
            Hierarchy node with children
        """
        task_id = task.get('id')
        
        # Find child tasks
        children = [
            self._build_hierarchy_node(child_task, task_map)
            for child_task in task_map.values()
            if child_task.get('parent_id') == task_id
        ]
        
        # Create node with task details and children
        return {
            'id': task_id,
            'name': task.get('name', 'Unnamed Task'),
            'status': task.get('status', 'unknown'),
            'type': task.get('type', 'unknown'),
            'priority': task.get('priority', 4),
            'children': children,
            'has_children': bool(children)
        }
    
    def _prepare_task_data_for_table(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare task data for table display.
        
        Args:
            tasks: List of tasks to prepare
            
        Returns:
            List of task data prepared for table display
        """
        if not tasks:
            return []
            
        result = []
        
        # Create a map of tasks by ID for parent lookup
        task_map = {task.get('id'): task for task in tasks}
        
        for task in tasks:
            # Get parent task name if available
            parent_id = task.get('parent_id')
            parent_name = None
            if parent_id and parent_id in task_map:
                parent_name = task_map[parent_id].get('name')
                
            # Format tag list as comma-separated string
            tags = task.get('tags', [])
            tags_str = ', '.join(tags) if tags else ''
            
            # Prepare record for table
            record = {
                'id': task.get('id', ''),
                'name': task.get('name', 'Unnamed Task'),
                'status': task.get('status', ''),
                'type': task.get('type', ''),
                'priority': task.get('priority', 4),
                'priority_name': self._get_priority_name(task.get('priority', 4)),
                'tags': tags_str,
                'parent_id': parent_id,
                'parent_name': parent_name or 'None',
                'created_at': task.get('created_at', ''),
                'updated_at': task.get('updated_at', '')
            }
            
            result.append(record)
            
        return result
    
    def _get_priority_name(self, priority: int) -> str:
        """Get the readable name for a priority level."""
        priority_mapping = {
            1: "High",
            2: "Medium", 
            3: "Low",
            4: "None"
        }
        return priority_mapping.get(priority, "Unknown")
    
    def _get_cache_key(self, context: Dict[str, Any]) -> str:
        """
        Generate a cache key for the given context.
        
        Args:
            context: Context information to generate key for
            
        Returns:
            Cache key string
        """
        # Create a normalized representation of the context for caching
        cache_data = {
            'level': context.get('level', 'root'),
            'entity_id': context.get('entity_id'),
            'metrics': sorted(context.get('metrics', [])),
            'filters': context.get('filters', {})
        }
        
        # Convert to a deterministic string representation
        context_str = json.dumps(cache_data, sort_keys=True)
        
        # Create a hash of the context string
        return f"task_data_{hashlib.md5(context_str.encode()).hexdigest()}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if the cache for the given key is valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if the cache is valid, False otherwise
        """
        # Check if the cache contains the key
        if cache_key not in self.cache:
            return False
            
        # Check if the cache has expired
        current_time = time.time()
        if cache_key not in self.cache_expiry or self.cache_expiry[cache_key] < current_time:
            return False
            
        # Cache is valid
        return True
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Cache a result with the given key.
        
        Args:
            cache_key: Cache key to use
            result: Result data to cache
        """
        # Store result in cache
        self.cache[cache_key] = result
        
        # Set expiry time
        self.cache_expiry[cache_key] = time.time() + self.cache_ttl
    
    def clear_cache(self) -> None:
        """
        Clear the entire cache.
        """
        self.cache = {}
        self.cache_expiry = {} 