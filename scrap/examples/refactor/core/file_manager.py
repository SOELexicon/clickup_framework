"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/file_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)
    - tsk_2d5e7f90 - Improve Service Layer (related)

Used By:
    - CLI Commands: Used as the primary core manager implementation
    - Integration Tests: Used as the implementation for test fixtures
    - Export Tools: Used for data persistence and retrieval 
    - Dashboard: Used for task data access and processing

Purpose:
    Provides a file-based implementation of the CoreManager interface that loads and
    saves data from/to JSON files. This class serves as the primary data management 
    component, handling all operations related to tasks, relationships, checklists,
    and organizational structures.

Requirements:
    - Must handle cross-platform file path differences
    - Must gracefully handle JSON parsing errors
    - Must maintain data integrity during save/load operations
    - Must preserve existing data that is not being modified
    - CRITICAL: Must prevent data loss during file operations
    - CRITICAL: Must maintain backward compatibility with existing JSON formats

Changes:
    - v1: Initial implementation with basic task management
    - v2: Added relationship handling and enhanced error reporting
    - v3: Improved validation and error handling
    - v4: Added scoring system integration
    - v5: Enhanced with comprehensive cross-platform support

Lessons Learned:
    - Proper error handling is essential for file operations
    - JSON schema validation prevents data corruption
    - Platform-specific path handling prevents cross-platform issues
    - Clear error messages aid debugging and user experience
"""
import json
import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from refactor.core.interfaces.core_manager import CoreManager
from refactor.core.exceptions import get_repo_error_code
from refactor.cli.error_handling import CLIError
from refactor.core.scoring.task_scorer import TaskScorer

logger = logging.getLogger(__name__)

class FileManager(CoreManager):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/file_manager.py
    dohcount: 1
    
    Used By:
        - CLI Commands: Primary implementation for all CLI operations
        - Web API: Data access layer for REST endpoints
        - Export Tools: Source for data export functions
        - Dashboard: Data provider for visualization components
    
    Purpose:
        File-based implementation of CoreManager that uses JSON files for data storage.
        Responsible for loading, manipulating, and saving task data, while maintaining
        data integrity and providing a consistent interface for client code.
    
    Requirements:
        - Must handle file I/O errors gracefully
        - Must maintain data structures consistent with JSON schema
        - Must provide atomic operations where possible
        - Must ensure referential integrity across entities
        - CRITICAL: Must prevent data loss during save operations
        - CRITICAL: Must handle both legacy and modern data formats
    
    Changes:
        - v1: Initial implementation with basic file operations
        - v2: Added relationship management and validation
        - v3: Enhanced error handling with specific error codes
        - v4: Added task scoring integration
        - v5: Improved cross-platform compatibility
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize a new FileManager.
        
        Args:
            config_manager: Optional configuration manager
        """
        self.config_manager = config_manager
        self.data = None
        self.file_path = None
        self.initialized = False
        self.colors_enabled = True  # Default to enabling colors
        
    def initialize(self, file_path: str) -> None:
        """
        Initialize with a template file path and load its data.
        
        Args:
            file_path: Path to the JSON template file
        """
        self.file_path = file_path
            
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Template file {file_path} does not exist, will create on save")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # Ensure all required sections exist
            for section in ["spaces", "folders", "lists", "tasks"]:
                if section not in self.data:
                    self.data[section] = []
            
            # Migrate task container_id fields if needed
            self._migrate_task_container_ids()
                    
            logger.info(f"Loaded data from {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {file_path}: {str(e)}")
            raise CLIError(f"Invalid JSON in template file: {str(e)}", 
                          get_repo_error_code("FILE", "001"))
        except Exception as e:
            logger.error(f"Error loading template file {file_path}: {str(e)}")
            raise CLIError(f"Failed to load template file: {str(e)}", 
                          get_repo_error_code("FILE", "002"))
    
    def save(self) -> None:
        """Save data to the template file."""
        if not self.file_path:
            logger.error("No template path set for saving")
            raise CLIError("No template path set for saving",
                          get_repo_error_code("FILE", "003"))
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved data to {self.file_path}")
        except Exception as e:
            logger.error(f"Error saving to {self.file_path}: {str(e)}")
            raise CLIError(f"Failed to save template file: {str(e)}",
                          get_repo_error_code("FILE", "004"))
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with the given prefix."""
        # Use uuid4 to generate a random UUID
        random_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{random_id}"
    
    def _find_task_by_id_or_name(self, task_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Find a task by ID or name."""
        # First try to find by ID
        for task in self.data["tasks"]:
            if task["id"] == task_id_or_name:
                return task
        
        # Then try to find by name
        for task in self.data["tasks"]:
            if task["name"] == task_id_or_name:
                return task
                
        return None
    
    def create_task(self, 
                   name: str, 
                   description: str = "", 
                   status: str = "to do",
                   priority: int = 3,
                   tags: Optional[List[str]] = None,
                   parent_id: Optional[str] = None,
                   list_id: Optional[str] = None,
                   task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Task: tsk_1234abcd - Update Task Command Functionality
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Create Command: Primary interface for creating tasks
            - Task Batch Import: For bulk task creation
            - API Integration: For external system task creation
            
        Purpose:
            Creates a new task with the specified properties and handles
            relationships including parent-child task associations and
            list assignment.
            
        Requirements:
            - Must generate a unique ID for the task
            - Must add task to parent if specified
            - Must add task to list if specified
            - Must store all task metadata and relationships
            - CRITICAL: Must initialize proper default values
            
        Args:
            name: Task name/title
            description: Detailed task description
            status: Task status (default: "to do")
            priority: Task priority (default: 3)
            tags: List of task tags
            parent_id: Parent task ID if this is a subtask
            list_id: List ID if task belongs to a specific list
            task_type: Type of task (task, bug, feature, refactor, documentation)
            
        Returns:
            Newly created task dictionary
            
        Changes:
            - v1: Initial implementation with basic task creation
            - v2: Added task_type support for task classification
        """
        # Generate a unique ID
        task_id = self._generate_id("tsk")
        
        task = {
            "id": task_id,
            "name": name,
            "description": description,
            "status": status,
            "priority": priority,
            "tags": tags or [],
            "parent_id": parent_id,
            "subtasks": [],
            "comments": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add task_type if specified
        if task_type:
            task["task_type"] = task_type
        
        # Add to parent task if specified
        if parent_id:
            parent_task = self._find_task_by_id_or_name(parent_id)
            if parent_task:
                if "subtasks" not in parent_task:
                    parent_task["subtasks"] = []
                parent_task["subtasks"].append(task_id)
            else:
                logger.warning(f"Parent task {parent_id} not found for new task {task_id}")
        
        # Add task to the list
        self.data["tasks"].append(task)
        
        # Add to list if specified
        if list_id:
            self.add_task_to_list(task_id, list_id)
            
        return task
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a task by ID."""
        task = self._find_task_by_id_or_name(task_id)
        if not task:
            raise CLIError(f"Task not found: {task_id}", get_repo_error_code("TASK", "001"))
        return task
    
    def get_task_by_name(self, name: str) -> Dict[str, Any]:
        """Get a task by name."""
        for task in self.data["tasks"]:
            if task["name"] == name:
                return task
                
        raise CLIError(f"Task not found: {name}", get_repo_error_code("TASK", "001"))
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks in the file.
        
        Returns:
            List of task dictionaries
        """
        return self.data["tasks"]
        
    def find_task_by_id_or_name(self, task_id_or_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a task by ID or name.
        
        Args:
            task_id_or_name: Task ID or name to find
            
        Returns:
            Task dictionary or None if not found
        """
        return self._find_task_by_id_or_name(task_id_or_name)
    
    def update_task(self, 
                   task_id_or_dict: Union[str, Dict[str, Any]], 
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   status: Optional[str] = None,
                   priority: Optional[int] = None,
                   task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Task: tsk_1234abcd - Update Task Command Functionality
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Update Command: For modifying existing tasks
            - CLI Type Update Command: For changing task type
            - Task Management Tools: For batch updates
            
        Purpose:
            Updates a task with new data while maintaining its identity
            and relationships. Handles both ID-based updates and direct
            dictionary updates for flexibility.
            
        Requirements:
            - Must support both task ID and task dictionary as input
            - Must validate task exists if ID is provided
            - Must only update specified fields
            - Must update timestamp on changes
            - CRITICAL: Must preserve relationships and subtasks
            
        Args:
            task_id_or_dict: Task ID string or task dictionary object
            name: New task name (optional)
            description: New task description (optional)
            status: New task status (optional)
            priority: New task priority (optional)
            task_type: New task type (optional)
            
        Returns:
            Updated task dictionary
            
        Changes:
            - v1: Initial implementation with basic field updates
            - v2: Added task_type support and dictionary input
        """
        # Handle both task ID and task dict cases
        if isinstance(task_id_or_dict, dict):
            task = task_id_or_dict
            # Ensure task exists in the data
            if task.get('id') not in [t.get('id') for t in self.data["tasks"]]:
                raise CLIError(f"Task not found: {task.get('id')}", get_repo_error_code("TASK", "001"))
        else:
            # Get task by ID
            task = self.get_task(task_id_or_dict)
        
        # Update fields if provided
        if name is not None:
            task["name"] = name
        if description is not None:
            task["description"] = description
        if status is not None:
            task["status"] = status
        if priority is not None:
            task["priority"] = priority
        if task_type is not None:
            task["task_type"] = task_type
        
        # Update timestamp
        task["updated_at"] = datetime.now().isoformat()
        return task
    
    def delete_task(self, task_id: str, cascade: bool = True) -> bool:
        """Delete a task."""
        task = self._find_task_by_id_or_name(task_id)
        if not task:
            return False
        
        # Check for subtasks
        if task.get("subtasks", []) and not cascade:
            raise CLIError("Cannot delete task with subtasks", get_repo_error_code("TASK", "004"))
        
        # Remove from parent task if applicable
        parent_id = task.get("parent_id")
        if parent_id:
            parent_task = self._find_task_by_id_or_name(parent_id)
            if parent_task and "subtasks" in parent_task:
                if task["id"] in parent_task["subtasks"]:
                    parent_task["subtasks"].remove(task["id"])
        
        # Delete all subtasks if cascade is True
        if cascade:
            for subtask_id in task.get("subtasks", []).copy():
                self.delete_task(subtask_id, cascade=True)
        
        # Delete task
        self.data["tasks"].remove(task)
        return True
    
    def update_task_status(self, 
                          task_id: str, 
                          status: str,
                          comment: Optional[str] = None,
                          force: bool = False) -> Dict[str, Any]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Status Update Command: Primary implementation for status changes
            - Dashboard: For updating task progress
            - Batch Processing: For bulk status updates
            - Automation Tools: For workflow automation
        
        Purpose:
            Updates a task's status while enforcing business rules about task completion,
            such as requiring subtasks, checklist items, and dependencies to be completed
            before marking a task as complete, unless explicitly forced.
        
        Requirements:
            - Must verify task existence before updating
            - Must prevent marking a task complete if it has incomplete subtasks
            - Must prevent marking a task complete if it has unchecked checklist items
            - Must prevent marking a task complete if it has incomplete dependencies
            - Must provide a force option to override these checks
            - Must add a system comment when comment is provided
            - CRITICAL: Must maintain task relationship integrity
            - CRITICAL: Must handle both legacy and modern data formats
        
        Args:
            task_id: ID or name of the task to update
            status: New status value to set
            comment: Optional comment to add explaining the status change
            force: If True, bypasses validation checks for completion
            
        Returns:
            Updated task dictionary
            
        Raises:
            CLIError: If task not found or business rules prevent the status change
            
        Side Effects:
            - Updates task status in the data store
            - Adds a system comment if one is provided
            - Updates the task's updated_at timestamp
        """
        task = self.get_task(task_id)
        
        # Check if task has incomplete subtasks
        if not force and status == "complete" and task.get("subtasks"):
            incomplete_subtasks = []
            for subtask_id in task.get("subtasks", []):
                subtask = self._find_task_by_id_or_name(subtask_id)
                if subtask and subtask.get("status") != "complete":
                    incomplete_subtasks.append(subtask['name'])
            
            if incomplete_subtasks:
                error_msg = f"Cannot mark task as complete with incomplete subtasks: {', '.join(incomplete_subtasks)}"
                raise CLIError(error_msg, get_repo_error_code("TASK", "005"))
        
        # Check if task has unchecked checklist items
        if not force and status == "complete" and "checklists" in task:
            # Handle both dictionary format (MockCoreManager) and list format (FileManager)
            unchecked_items = []
            if isinstance(task["checklists"], dict):
                # Dictionary format: {'checklist_id': {'name': 'name', 'items': [...]}}
                for checklist_id, checklist in task.get("checklists", {}).items():
                    for item in checklist.get("items", []):
                        if not item.get("checked", False):
                            item_name = item.get('text', item.get('name', 'Unnamed item'))
                            unchecked_items.append(item_name)
            else:
                # List format: [{'id': 'checklist_id', 'name': 'name', 'items': [...]}]
                for checklist in task.get("checklists", []):
                    for item in checklist.get("items", []):
                        if not item.get("checked", False):
                            item_name = item.get('text', item.get('name', 'Unnamed item'))
                            unchecked_items.append(item_name)
            
            if unchecked_items:
                error_msg = f"Cannot mark task as complete with unchecked items in checklist: {', '.join(unchecked_items)}"
                raise CLIError(error_msg, get_repo_error_code("TASK", "006"))
        
        # Check if task has incomplete dependencies
        dependencies = []
        incomplete_dependencies = []
        
        # Check for direct dependency fields (FileManager format)
        if 'depends_on' in task:
            dependencies.extend(task['depends_on'])
        
        # Check for relationship dictionary (MockCoreManager format)
        if 'relationships' in task and 'depends_on' in task['relationships']:
            dependencies.extend(task['relationships']['depends_on'])
            
        if not force and status == "complete" and dependencies:
            for dep_id in dependencies:
                dep_task = self._find_task_by_id_or_name(dep_id)
                if dep_task and dep_task.get("status") != "complete":
                    incomplete_dependencies.append(dep_task['name'])
            
            if incomplete_dependencies:
                error_msg = f"Cannot mark task as complete with incomplete dependency (task is blocked by): {', '.join(incomplete_dependencies)}"
                raise CLIError(error_msg, get_repo_error_code("TASK", "007"))
        
        # Store the old status to check for completion transition
        old_status = task.get("status")
        
        # Update the status
        task["status"] = status
        
        # Set start_date when transitioning to "in progress"
        if status == "in progress" and old_status != "in progress" and old_status != "complete":
            if not task.get("start_date"):
                task["start_date"] = datetime.now().isoformat()
        
        # Set completed_at timestamp if task is being marked as complete
        if status == "complete" and old_status != "complete":
            task["completed_at"] = datetime.now().isoformat()
        # Clear completed_at if task was complete and is now not complete
        elif status != "complete" and old_status == "complete":
            if "completed_at" in task:
                del task["completed_at"]
        
        if comment:
            self.add_comment(task_id, comment, "system")
        
        task["updated_at"] = datetime.now().isoformat()
        return task
    
    def add_comment(self, task_id: str, text: str, author: str = "user") -> Dict[str, Any]:
        """Add a comment to a task."""
        task = self.get_task(task_id)
        
        if "comments" not in task:
            task["comments"] = []
            
        comment = {
            "text": text,
            "author": author,
            "created_at": datetime.now().isoformat()
        }
        
        task["comments"].append(comment)
        return comment
    
    def add_comment_to_task(self, task_id: str, text: str, author: str = "user") -> Dict[str, Any]:
        """
        Add a comment to a task.
        
        Args:
            task_id: ID of the task to add a comment to
            text: Comment text
            author: Name of the comment author (default: "user")
            
        Returns:
            The updated task dictionary
        """
        comment = self.add_comment(task_id, text, author)
        self.save()  # Save changes to file
        return comment
    
    def add_task_to_list(self, task_id: str, list_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Task: tsk_ff8e47b1 - Update Task Entity with Parent Tracking
        Document: refactor/core/file_manager.py
        dohcount: 3
        
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
            The updated task dictionary with the new container assignment
            
        Raises:
            CLIError: If task or list doesn't exist
            ValidationError: If task is already in a list and force is False
            
        Changes:
            - v3: Added setting specific container fields (space_id, folder_id, list_id) in addition to container_id
        """
        # Find the list
        list_obj = None
        for lst in self.data["lists"]:
            if lst["id"] == list_id:
                list_obj = lst
                break
                
        if not list_obj:
            raise CLIError(f"List not found: {list_id}", get_repo_error_code("LIST", "001"))
            
        # Find the task - handle both string ID and task object
        task = None
        task_id_str = task_id
        
        # If task_id is actually a task object (for backward compatibility)
        if isinstance(task_id, dict) and "id" in task_id:
            task = task_id
            task_id_str = task["id"]
        elif hasattr(task_id, "id"):  # Handle EntityObject
            task_id_str = task_id.id
            
        # Find task by ID if not already a task object
        if task is None:
            for t in self.data["tasks"]:
                if t["id"] == task_id_str:
                    task = t
                    break
                
        if not task:
            raise CLIError(f"Task not found: {task_id_str}", get_repo_error_code("TASK", "001"))
            
        # Check if task is already assigned to a different list
        if "container_id" in task and task["container_id"] and task["container_id"] != list_id:
            if not force:
                raise CLIError(
                    f"Task '{task_id_str}' is already assigned to list '{task['container_id']}'. Use --force to reassign.",
                    get_repo_error_code("ASSIGN", "001")
                )
            # Remove from previous list if force is True
            for lst in self.data["lists"]:
                if lst["id"] == task["container_id"] and "tasks" in lst and task_id_str in lst["tasks"]:
                    lst["tasks"].remove(task_id_str)
                    break
            
        # Ensure list has a tasks array
        if "tasks" not in list_obj:
            list_obj["tasks"] = []
            
        # Add task to list if not already there
        if task_id_str not in list_obj["tasks"]:
            list_obj["tasks"].append(task_id_str)
            
        # Update task's container_id
        task["container_id"] = list_id
        
        # For backward compatibility, also update list_id
        task["list_id"] = list_id
        
        # Get folder and space info for the list
        folder_id = list_obj.get("folder_id", "")
        if folder_id:
            task["folder_id"] = folder_id
            # Get folder name
            for folder in self.data.get("folders", []):
                if folder.get("id") == folder_id:
                    task["folder_name"] = folder.get("name", f"Folder {folder_id}")
                    # Get space info for the folder
                    space_id = folder.get("space_id", "")
                    if space_id:
                        task["space_id"] = space_id
                        # Get space name
                        for space in self.data.get("spaces", []):
                            if space.get("id") == space_id:
                                task["space_name"] = space.get("name", f"Space {space_id}")
                                break
                    break
        
        # Add list name and other attributes for better display
        task["list_name"] = list_obj.get("name", f"List {list_id}")
        if "color" in list_obj:
            task["list_color"] = list_obj["color"]
        if "icon" in list_obj:
            task["list_icon"] = list_obj["icon"]
            
        # Update timestamp
        task["updated_at"] = datetime.now().isoformat()
        
        return task
    
    def create_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """Create a checklist for a task."""
        task = self.get_task(task_id)
        
        # Ensure task has checklists
        if "checklists" not in task:
            task["checklists"] = {}
        
        # Generate checklist ID
        checklist_id = self._generate_id("chk")
        
        # Create checklist
        checklist = {
            "id": checklist_id,
            "name": name,
            "items": [],
            "created_at": datetime.now().isoformat()
        }
        
        task["checklists"][checklist_id] = checklist
        return checklist
    
    def add_checklist_item(self, task_id: str, checklist_id: str, text: str) -> Dict[str, Any]:
        """Add an item to a checklist."""
        task = self.get_task(task_id)
        
        # Ensure task has checklists
        if "checklists" not in task:
            task["checklists"] = {}
        
        # Check if checklist exists
        if checklist_id not in task["checklists"]:
            raise CLIError(f"Checklist not found: {checklist_id}", get_repo_error_code("CHECKLIST", "001"))
        
        # Generate item ID
        item_id = self._generate_id("item")
        
        # Create item
        item = {
            "id": item_id,
            "text": text,
            "checked": False,
            "created_at": datetime.now().isoformat()
        }
        
        task["checklists"][checklist_id]["items"].append(item)
        return item
    
    def check_checklist_item(self, task_id: str, item_id: str, checked: bool = True) -> Dict[str, Any]:
        """Check or uncheck a checklist item."""
        task = self.get_task(task_id)
        
        # Handle both dictionary format (MockCoreManager) and list format (FileManager)
        if "checklists" in task:
            if isinstance(task["checklists"], dict):
                # Dictionary format: {'checklist_id': {'name': 'name', 'items': [...]}}
                for checklist in task.get("checklists", {}).values():
                    for item in checklist.get("items", []):
                        if item["id"] == item_id:
                            item["checked"] = checked
                            return item
            else:
                # List format: [{'id': 'checklist_id', 'name': 'name', 'items': [...]}]
                for checklist in task.get("checklists", []):
                    for item in checklist.get("items", []):
                        if item["id"] == item_id:
                            item["checked"] = checked
                            return item
        
        raise CLIError(f"Checklist item not found: {item_id}", get_repo_error_code("CHECKLIST", "002"))
    
    def create_space(self, name: str, description: str = "", color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Create a space.
        
        Args:
            name: Name of the space
            description: Description of the space
            color: Optional color for the space (hex code or name)
            icon: Optional icon identifier for the space
        
        Returns:
            The created space dictionary
        """
        space_id = self._generate_id("spc")
        space = {
            "id": space_id,
            "name": name,
            "description": description,
            "folders": []
        }
        
        # Add optional color and icon if provided
        if color:
            space["color"] = color
        if icon:
            space["icon"] = icon
            
        self.data["spaces"].append(space)
        return space
    
    def create_folder(self, space_id: str, name: str, description: str = "", color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Create a folder in a space.
        
        Args:
            space_id: ID of the space to create the folder in
            name: Name of the folder
            description: Description of the folder
            color: Optional color for the folder (hex code or name)
            icon: Optional icon identifier for the folder
            
        Returns:
            The created folder dictionary
            
        Raises:
            CLIError: If the space doesn't exist
        """
        # Find the space
        space = None
        for s in self.data["spaces"]:
            if s["id"] == space_id:
                space = s
                break
                
        if not space:
            raise CLIError(f"Space not found: {space_id}", get_repo_error_code("SPACE", "001"))
        
        folder_id = self._generate_id("fld")
        folder = {
            "id": folder_id,
            "name": name,
            "description": description,
            "space_id": space_id,
            "lists": []
        }
        
        # Add optional color and icon if provided
        if color:
            folder["color"] = color
        if icon:
            folder["icon"] = icon
        
        self.data["folders"].append(folder)
        
        # Add to space's folders
        if "folders" not in space:
            space["folders"] = []
        space["folders"].append(folder_id)
        
        return folder
    
    def create_list(self, folder_id: str, name: str, description: str = "", color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Create a list in a folder.
        
        Args:
            folder_id: ID of the folder to create the list in
            name: Name of the list
            description: Description of the list
            color: Optional color for the list (hex code or name)
            icon: Optional icon identifier for the list
            
        Returns:
            The created list dictionary
            
        Raises:
            CLIError: If the folder doesn't exist
        """
        # Find the folder
        folder = None
        for f in self.data["folders"]:
            if f["id"] == folder_id:
                folder = f
                break
                
        if not folder:
            raise CLIError(f"Folder not found: {folder_id}", get_repo_error_code("FOLDER", "001"))
        
        list_id = self._generate_id("lst")
        list_obj = {
            "id": list_id,
            "name": name,
            "description": description,
            "folder_id": folder_id,
            "tasks": []
        }
        
        # Add optional color and icon if provided
        if color:
            list_obj["color"] = color
        if icon:
            list_obj["icon"] = icon
        
        self.data["lists"].append(list_obj)
        
        # Add to folder's lists
        if "lists" not in folder:
            folder["lists"] = []
        folder["lists"].append(list_id)
        
        return list_obj
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """Get all spaces."""
        return self.data["spaces"]
    
    def get_folders(self, space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all folders or folders in a space."""
        if space_id:
            return [f for f in self.data["folders"] if f["space_id"] == space_id]
        return self.data["folders"]
    
    def get_lists(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all lists or lists in a specific folder."""
        if folder_id:
            return [lst for lst in self.data["lists"] if lst.get("folder_id") == folder_id]
        return self.data["lists"]
    
    def find_list_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a list by its name.
        
        Args:
            name: The name of the list to find
            
        Returns:
            The list if found, None otherwise
        """
        for lst in self.data["lists"]:
            if lst.get("name") == name:
                return lst
        return None
    
    def get_subtasks(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all subtasks of a task."""
        task = self.get_task(task_id)
        
        subtasks = []
        for subtask_id in task.get("subtasks", []):
            subtask = self._find_task_by_id_or_name(subtask_id)
            if subtask:
                subtasks.append(subtask)
                
        return subtasks
    
    def get_parent_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the parent task of a task.
        
        Args:
            task_id: ID of the task to get the parent for
            
        Returns:
            The parent task if it exists, None otherwise
        """
        task = self.get_task(task_id)
        
        # Check if task has a parent_id
        parent_id = task.get("parent_id")
        if parent_id:
            try:
                return self.get_task(parent_id)
            except:
                return None
        
        return None
    
    def get_tasks_in_list(self, list_id: str) -> List[Dict[str, Any]]:
        """Get all tasks in a list."""
        # Find the list
        list_obj = None
        for l in self.data["lists"]:
            if l["id"] == list_id:
                list_obj = l
                break
                
        if not list_obj:
            raise CLIError(f"List not found: {list_id}", get_repo_error_code("LIST", "001"))
            
        tasks = []
        for task_id in list_obj.get("tasks", []):
            task = self._find_task_by_id_or_name(task_id)
            if task:
                tasks.append(task)
                
        return tasks
    
    def update_space_colors(self, space_id: str, color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Update the color and icon for a space.
        
        Args:
            space_id: ID of the space to update
            color: New color for the space (hex code or name), None to keep current
            icon: New icon identifier for the space, None to keep current
            
        Returns:
            Updated space dictionary
            
        Raises:
            CLIError: If the space doesn't exist
        """
        # Find the space
        space = None
        for s in self.data["spaces"]:
            if s["id"] == space_id:
                space = s
                break
                
        if not space:
            raise CLIError(f"Space not found: {space_id}", get_repo_error_code("SPACE", "001"))
        
        # Update color and icon if provided
        if color is not None:
            space["color"] = color
        if icon is not None:
            space["icon"] = icon
            
        return space
    
    def update_folder_colors(self, folder_id: str, color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Update the color and icon for a folder.
        
        Args:
            folder_id: ID of the folder to update
            color: New color for the folder (hex code or name), None to keep current
            icon: New icon identifier for the folder, None to keep current
            
        Returns:
            Updated folder dictionary
            
        Raises:
            CLIError: If the folder doesn't exist
        """
        # Find the folder
        folder = None
        for f in self.data["folders"]:
            if f["id"] == folder_id:
                folder = f
                break
                
        if not folder:
            raise CLIError(f"Folder not found: {folder_id}", get_repo_error_code("FOLDER", "001"))
        
        # Update color and icon if provided
        if color is not None:
            folder["color"] = color
        if icon is not None:
            folder["icon"] = icon
            
        return folder
    
    def update_list_colors(self, list_id: str, color: str = None, icon: str = None) -> Dict[str, Any]:
        """
        Update the color and icon for a list.
        
        Args:
            list_id: ID of the list to update
            color: New color for the list (hex code or name), None to keep current
            icon: New icon identifier for the list, None to keep current
            
        Returns:
            Updated list dictionary
            
        Raises:
            CLIError: If the list doesn't exist
        """
        # Find the list
        list_obj = None
        for l in self.data["lists"]:
            if l["id"] == list_id:
                list_obj = l
                break
                
        if not list_obj:
            raise CLIError(f"List not found: {list_id}", get_repo_error_code("LIST", "001"))
        
        # Update color and icon if provided
        if color is not None:
            list_obj["color"] = color
        if icon is not None:
            list_obj["icon"] = icon
            
        return list_obj
    
    def add_tag(self, task_id: str, tag: str) -> Dict[str, Any]:
        """Add a tag to a task."""
        task = self.get_task(task_id)
        
        if "tags" not in task:
            task["tags"] = []
            
        if tag not in task["tags"]:
            task["tags"].append(tag)
        
        return task
    
    def remove_tag(self, task_id: str, tag: str) -> Dict[str, Any]:
        """Remove a tag from a task."""
        task = self.get_task(task_id)
        
        if "tags" in task and tag in task["tags"]:
            task["tags"].remove(tag)
        
        return task
    
    def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find tasks by tag."""
        return [task for task in self.data["tasks"] if tag in task.get("tags", [])]
    
    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Find tasks by status."""
        return [task for task in self.data["tasks"] if task.get("status") == status]
    
    def find_by_priority(self, priority: int) -> List[Dict[str, Any]]:
        """Find tasks by priority."""
        return [task for task in self.data["tasks"] if task.get("priority") == priority]
    
    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by name or description."""
        query = query.lower()
        return [
            task for task in self.data["tasks"] 
            if query in task.get("name", "").lower() or query in task.get("description", "").lower()
        ]
    
    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Add a dependency between tasks."""
        # Get tasks
        task = self.get_task(task_id)
        depends_on_task = self.get_task(depends_on_id)
        
        # Ensure relationships exist
        if "relationships" not in task:
            task["relationships"] = {}
        if "depends_on" not in task["relationships"]:
            task["relationships"]["depends_on"] = []
            
        if "relationships" not in depends_on_task:
            depends_on_task["relationships"] = {}
        if "blocks" not in depends_on_task["relationships"]:
            depends_on_task["relationships"]["blocks"] = []
        
        # Add dependency
        if depends_on_id not in task["relationships"]["depends_on"]:
            task["relationships"]["depends_on"].append(depends_on_id)
        
        # Add blocks relationship to dependency
        if task_id not in depends_on_task["relationships"]["blocks"]:
            depends_on_task["relationships"]["blocks"].append(task_id)
    
    def remove_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Remove a dependency between tasks."""
        # Get tasks
        try:
            task = self.get_task(task_id)
            
            # Remove dependency if it exists
            if "relationships" in task and "depends_on" in task["relationships"]:
                if depends_on_id in task["relationships"]["depends_on"]:
                    task["relationships"]["depends_on"].remove(depends_on_id)
        except CLIError:
            logger.warning(f"Task {task_id} not found for dependency removal")
        
        try:
            depends_on_task = self.get_task(depends_on_id)
            
            # Remove blocks relationship from dependency if it exists
            if "relationships" in depends_on_task and "blocks" in depends_on_task["relationships"]:
                if task_id in depends_on_task["relationships"]["blocks"]:
                    depends_on_task["relationships"]["blocks"].remove(task_id)
        except CLIError:
            logger.warning(f"Task {depends_on_id} not found for dependency removal")
    
    def get_dependencies(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on."""
        task = self.get_task(task_id)
        
        dependencies = []
        for dep_id in task.get("relationships", {}).get("depends_on", []):
            dep_task = self._find_task_by_id_or_name(dep_id)
            if dep_task:
                dependencies.append(dep_task)
                
        return dependencies
    
    def get_blocking_tasks(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all tasks that are blocked by this task."""
        task = self.get_task(task_id)
        
        blocking = []
        # Check both relationships dictionary and direct fields
        blocks_ids = []
        
        # Check relationships dictionary
        if "relationships" in task and "blocks" in task["relationships"]:
            blocks_ids.extend(task["relationships"]["blocks"])
            
        # Check direct blocks field
        if "blocks" in task:
            blocks_ids.extend(task["blocks"])
            
        # Get unique IDs
        blocks_ids = list(set(blocks_ids))
        
        # Get task details for each blocked task
        for blocked_id in blocks_ids:
            blocked_task = self._find_task_by_id_or_name(blocked_id)
            if blocked_task:
                blocking.append(blocked_task)
                
        return blocking
    
    def find_tasks_blocked_by(self, task_id: str) -> List[str]:
        """Find all tasks that are blocked by the given task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            List of task IDs that are blocked by this task
        """
        blocked_tasks = []
        
        # Search through all tasks to find those that are blocked by this task
        for task in self.data["tasks"]:
            # Check relationships dictionary
            if "relationships" in task:
                if "depends_on" in task["relationships"] and task_id in task["relationships"]["depends_on"]:
                    blocked_tasks.append(task["id"])
                if "blocked_by" in task["relationships"] and task_id in task["relationships"]["blocked_by"]:
                    blocked_tasks.append(task["id"])
            
            # Check direct fields
            if "depends_on" in task and task_id in task["depends_on"]:
                blocked_tasks.append(task["id"])
            if "blocked_by" in task and task_id in task["blocked_by"]:
                blocked_tasks.append(task["id"])
        
        return list(set(blocked_tasks))
    
    def add_relationship(self, source_task_id: str, relationship_type: str, target_task_id: str) -> bool:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Relationship Command: For creating task relationships
            - Task Management Interface: For establishing task dependencies
            - Documentation System: For linking docs to implementation tasks
            - Dashboard: For visualizing task relationships
        
        Purpose:
            Establishes a bidirectional relationship between two tasks according to the
            specified relationship type, ensuring that both tasks properly reference each other
            and maintaining the semantic meaning of each relationship direction.
        
        Requirements:
            - Must validate that both source and target tasks exist
            - Must prevent self-relationships (task relating to itself)
            - Must handle all relationship types correctly (depends_on, blocks, documents, documented_by)
            - Must establish both sides of bidirectional relationships
            - Must prevent duplicate relationship entries
            - CRITICAL: Must maintain proper relationship semantics
            - CRITICAL: Must preserve existing relationships when adding new ones
        
        Args:
            source_task_id: ID or name of the source task
            relationship_type: Type of relationship ('blocks', 'depends_on', 'documents', or 'documented_by')
            target_task_id: ID or name of the target task
            
        Returns:
            True if the relationship was added successfully
            
        Raises:
            CLIError: If the tasks don't exist, the relationship is invalid, or it's a self-relationship
            
        Side Effects:
            - Updates relationship dictionaries in both source and target tasks
            - May create relationship dictionaries if they don't exist
            
        Example Usage:
            ```python
            # Create a dependency relationship: Task A depends on Task B
            file_manager.add_relationship("Task A", "depends_on", "Task B")
            
            # Create a documentation relationship: Task C documents Task D
            file_manager.add_relationship("Task C", "documents", "Task D")
            ```
        """
        # Get source task first
        try:
            # Try by ID first
            source_task = self.get_task(source_task_id)
        except:
            try:
                # Then try by name
                source_task = self.get_task_by_name(source_task_id)
            except Exception as e:
                raise CLIError(f"Source task not found: {source_task_id}", 
                              get_repo_error_code("TASK", "001"))
        
        # Get target task
        try:
            # Try by ID first
            target_task = self.get_task(target_task_id)
        except:
            try:
                # Then try by name
                target_task = self.get_task_by_name(target_task_id)
            except Exception as e:
                raise CLIError(f"Target task not found: {target_task_id}", 
                              get_repo_error_code("TASK", "001"))
        
        # Check for self-relationship
        if source_task['id'] == target_task['id']:
            raise CLIError(f"Cannot create relationship with the same task", 
                          get_repo_error_code("RELATIONSHIP", "001"))
        
        # Ensure relationships dictionaries exist
        if "relationships" not in source_task:
            source_task["relationships"] = {}
        if "relationships" not in target_task:
            target_task["relationships"] = {}
            
        # Add the appropriate relationships
        if relationship_type == "depends_on":
            # Source depends on target
            if "depends_on" not in source_task["relationships"]:
                source_task["relationships"]["depends_on"] = []
            if target_task['id'] not in source_task["relationships"]["depends_on"]:
                source_task["relationships"]["depends_on"].append(target_task['id'])
                
            # Target blocks source
            if "blocks" not in target_task["relationships"]:
                target_task["relationships"]["blocks"] = []
            if source_task['id'] not in target_task["relationships"]["blocks"]:
                target_task["relationships"]["blocks"].append(source_task['id'])
                
        elif relationship_type == "blocks":
            # Source blocks target
            if "blocks" not in source_task["relationships"]:
                source_task["relationships"]["blocks"] = []
            if target_task['id'] not in source_task["relationships"]["blocks"]:
                source_task["relationships"]["blocks"].append(target_task['id'])
                
            # Target depends on source
            if "depends_on" not in target_task["relationships"]:
                target_task["relationships"]["depends_on"] = []
            if source_task['id'] not in target_task["relationships"]["depends_on"]:
                target_task["relationships"]["depends_on"].append(source_task['id'])
                
        elif relationship_type == "documents":
            # Source documents target
            if "documents" not in source_task["relationships"]:
                source_task["relationships"]["documents"] = []
            if target_task['id'] not in source_task["relationships"]["documents"]:
                source_task["relationships"]["documents"].append(target_task['id'])
                
            # Target is documented by source
            if "documented_by" not in target_task["relationships"]:
                target_task["relationships"]["documented_by"] = []
            if source_task['id'] not in target_task["relationships"]["documented_by"]:
                target_task["relationships"]["documented_by"].append(source_task['id'])
                
        elif relationship_type == "documented_by":
            # Source is documented by target
            if "documented_by" not in source_task["relationships"]:
                source_task["relationships"]["documented_by"] = []
            if target_task['id'] not in source_task["relationships"]["documented_by"]:
                source_task["relationships"]["documented_by"].append(target_task['id'])
                
            # Target documents source
            if "documents" not in target_task["relationships"]:
                target_task["relationships"]["documents"] = []
            if source_task['id'] not in target_task["relationships"]["documents"]:
                target_task["relationships"]["documents"].append(source_task['id'])
        
        # Save changes
        self.save()
        return True
    
    def remove_relationship(self, source_task_id: str, relationship_type: str, target_task_id: str) -> bool:
        """Remove a relationship between tasks.
        
        Args:
            source_task_id: ID or name of the source task
            relationship_type: Type of relationship ('blocks', 'depends_on', 'documents', or 'documented_by')
            target_task_id: ID or name of the target task
            
        Returns:
            True if the relationship was removed successfully
            
        Raises:
            CLIError: If the tasks don't exist or the relationship doesn't exist
        """
        # Get source task first
        try:
            # Try by ID first
            source_task = self.get_task(source_task_id)
        except:
            try:
                # Then try by name
                source_task = self.get_task_by_name(source_task_id)
            except Exception as e:
                raise CLIError(f"Source task not found: {source_task_id}", 
                              get_repo_error_code("TASK", "001"))
        
        # Get target task
        try:
            # Try by ID first
            target_task = self.get_task(target_task_id)
        except:
            try:
                # Then try by name
                target_task = self.get_task_by_name(target_task_id)
            except Exception as e:
                raise CLIError(f"Target task not found: {target_task_id}", 
                              get_repo_error_code("TASK", "001"))
        
        # Check if the relationship exists
        relationship_exists = False
        
        if relationship_type == "depends_on":
            # Check if source depends on target
            if "relationships" in source_task and "depends_on" in source_task["relationships"]:
                if target_task['id'] in source_task["relationships"]["depends_on"]:
                    # Remove the dependency
                    source_task["relationships"]["depends_on"].remove(target_task['id'])
                    relationship_exists = True
            
            # Check if target blocks source
            if "relationships" in target_task and "blocks" in target_task["relationships"]:
                if source_task['id'] in target_task["relationships"]["blocks"]:
                    # Remove the blocks relationship
                    target_task["relationships"]["blocks"].remove(source_task['id'])
                    relationship_exists = True
                
        elif relationship_type == "blocks":
            # Check if source blocks target
            if "relationships" in source_task and "blocks" in source_task["relationships"]:
                if target_task['id'] in source_task["relationships"]["blocks"]:
                    # Remove the blocks relationship
                    source_task["relationships"]["blocks"].remove(target_task['id'])
                    relationship_exists = True
            
            # Check if target depends on source
            if "relationships" in target_task and "depends_on" in target_task["relationships"]:
                if source_task['id'] in target_task["relationships"]["depends_on"]:
                    # Remove the dependency
                    target_task["relationships"]["depends_on"].remove(source_task['id'])
                    relationship_exists = True
                    
        elif relationship_type == "documents":
            # Check if source documents target
            if "relationships" in source_task and "documents" in source_task["relationships"]:
                if target_task['id'] in source_task["relationships"]["documents"]:
                    # Remove the documents relationship
                    source_task["relationships"]["documents"].remove(target_task['id'])
                    relationship_exists = True
            
            # Check if target is documented by source
            if "relationships" in target_task and "documented_by" in target_task["relationships"]:
                if source_task['id'] in target_task["relationships"]["documented_by"]:
                    # Remove the documented_by relationship
                    target_task["relationships"]["documented_by"].remove(source_task['id'])
                    relationship_exists = True
                    
        elif relationship_type == "documented_by":
            # Check if source is documented by target
            if "relationships" in source_task and "documented_by" in source_task["relationships"]:
                if target_task['id'] in source_task["relationships"]["documented_by"]:
                    # Remove the documented_by relationship
                    source_task["relationships"]["documented_by"].remove(target_task['id'])
                    relationship_exists = True
            
            # Check if target documents source
            if "relationships" in target_task and "documents" in target_task["relationships"]:
                if source_task['id'] in target_task["relationships"]["documents"]:
                    # Remove the documents relationship
                    target_task["relationships"]["documents"].remove(source_task['id'])
                    relationship_exists = True
        
        if not relationship_exists:
            raise CLIError(f"Relationship does not exist between tasks", 
                          get_repo_error_code("RELATIONSHIP", "002"))
        
        # Save changes
        self.save()
        return True
    
    def find_related_to(self, task_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Find all tasks related to the given task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Dictionary with relationship types as keys and lists of related tasks as values
            
        The relationship types are:
        - depends_on: Tasks that this task depends on
        - blocks: Tasks that this task blocks
        - blocked_by: Tasks that block this task
        """
        task = self.get_task(task_id)
        
        # Initialize result structure
        related = {
            "depends_on": [],
            "blocks": [],
            "blocked_by": []
        }
        
        # First check this task's relationships
        if "relationships" in task:
            # Get tasks this task depends on
            if "depends_on" in task["relationships"]:
                for dep_id in task["relationships"]["depends_on"]:
                    dep_task = self._find_task_by_id_or_name(dep_id)
                    if dep_task:
                        related["depends_on"].append(dep_task)
            
            # Get tasks this task blocks
            if "blocks" in task["relationships"]:
                for blocked_id in task["relationships"]["blocks"]:
                    blocked_task = self._find_task_by_id_or_name(blocked_id)
                    if blocked_task:
                        related["blocks"].append(blocked_task)
        
        # Then check all other tasks for relationships to this task
        for other_task in self.data["tasks"]:
            if other_task["id"] == task["id"]:
                continue
                
            if "relationships" in other_task:
                # Check if other task blocks this task
                if "blocks" in other_task["relationships"] and task["id"] in other_task["relationships"]["blocks"]:
                    related["blocked_by"].append(other_task)
                    
                # Check if other task depends on this task
                if "depends_on" in other_task["relationships"] and task["id"] in other_task["relationships"]["depends_on"]:
                    related["blocks"].append(other_task)
                    
        # Remove duplicates and sort by name
        related["depends_on"] = sorted(list({task["id"]: task for task in related["depends_on"]}.values()), key=lambda t: t["name"])
        related["blocks"] = sorted(list({task["id"]: task for task in related["blocks"]}.values()), key=lambda t: t["name"])
        related["blocked_by"] = sorted(list({task["id"]: task for task in related["blocked_by"]}.values()), key=lambda t: t["name"])
                    
        return related
    
    def get_task_relationships(self, task_id: str) -> Dict[str, List[str]]:
        """
        Get all relationships for a task.
        
        Args:
            task_id: ID of the task to get relationships for
            
        Returns:
            Dictionary mapping relationship types to lists of related task IDs
        """
        task = self.get_task(task_id)
        relationships = {}
        
        # Check for relationships field in the task
        if "relationships" in task:
            return task["relationships"]
        
        # Legacy format - create from dependency fields
        relationships = {
            "depends_on": [],
            "blocks": []
        }
        
        # Add depends_on relationships
        if "depends_on" in task:
            relationships["depends_on"] = task["depends_on"]
            
        # Find tasks that are blocked by this task
        blocks = self.find_tasks_blocked_by(task_id)
        if blocks:
            relationships["blocks"] = blocks
            
        return relationships
    
    def list_relationships(self, task_id: str) -> str:
        """List all relationships for a task in a human-readable format.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            String containing formatted relationship information
        """
        try:
            task = self.get_task(task_id)
            task_name = task.get("name", task_id)
            
            # Initialize relationship collections
            blocks = []
            depends_on = []
            blocked_by = []
            documents = []
            documented_by = []
            
            # First, check task's own relationships dictionary
            if "relationships" in task:
                # Get tasks this task blocks
                if "blocks" in task["relationships"]:
                    for blocked_id in task["relationships"]["blocks"]:
                        try:
                            blocked_task = self.get_task(blocked_id)
                            blocks.append((blocked_task.get("name", blocked_id), blocked_id, blocked_task.get("status", "unknown")))
                        except:
                            blocks.append((blocked_id, blocked_id, "unknown"))
                
                # Get tasks this task depends on
                if "depends_on" in task["relationships"]:
                    for dep_id in task["relationships"]["depends_on"]:
                        try:
                            dep_task = self.get_task(dep_id)
                            depends_on.append((dep_task.get("name", dep_id), dep_id, dep_task.get("status", "unknown")))
                        except:
                            depends_on.append((dep_id, dep_id, "unknown"))
                
                # Get tasks this task documents
                if "documents" in task["relationships"]:
                    for doc_id in task["relationships"]["documents"]:
                        try:
                            doc_task = self.get_task(doc_id)
                            documents.append((doc_task.get("name", doc_id), doc_id, doc_task.get("status", "unknown")))
                        except:
                            documents.append((doc_id, doc_id, "unknown"))
                
                # Get tasks that document this task
                if "documented_by" in task["relationships"]:
                    for doc_by_id in task["relationships"]["documented_by"]:
                        try:
                            doc_by_task = self.get_task(doc_by_id)
                            documented_by.append((doc_by_task.get("name", doc_by_id), doc_by_id, doc_by_task.get("status", "unknown")))
                        except:
                            documented_by.append((doc_by_id, doc_by_id, "unknown"))
            
            # Then check direct fields (legacy format)
            if "blocks" in task and task["blocks"] and task["blocks"] not in [[], {}]:
                blocks_ids = task["blocks"] if isinstance(task["blocks"], list) else list(task["blocks"].keys())
                for blocked_id in blocks_ids:
                    try:
                        blocked_task = self.get_task(blocked_id)
                        block_tuple = (blocked_task.get("name", blocked_id), blocked_id, blocked_task.get("status", "unknown"))
                        if block_tuple not in blocks:  # Avoid duplicates
                            blocks.append(block_tuple)
                    except:
                        block_tuple = (blocked_id, blocked_id, "unknown")
                        if block_tuple not in blocks:  # Avoid duplicates
                            blocks.append(block_tuple)
            
            if "depends_on" in task and task["depends_on"] and task["depends_on"] not in [[], {}]:
                deps_ids = task["depends_on"] if isinstance(task["depends_on"], list) else list(task["depends_on"].keys())
                for dep_id in deps_ids:
                    try:
                        dep_task = self.get_task(dep_id)
                        dep_tuple = (dep_task.get("name", dep_id), dep_id, dep_task.get("status", "unknown"))
                        if dep_tuple not in depends_on:  # Avoid duplicates
                            depends_on.append(dep_tuple)
                    except:
                        dep_tuple = (dep_id, dep_id, "unknown")
                        if dep_tuple not in depends_on:  # Avoid duplicates
                            depends_on.append(dep_tuple)
            
            # Find tasks that are blocked by this task (tasks that depend on this task)
            # We need to check all other tasks to see if they have this task in their depends_on list
            for other_task in self.data["tasks"]:
                if other_task["id"] == task["id"]:
                    continue
                
                # Check if other task depends on this task (meaning this task blocks it)
                is_blocked = False
                
                # Check relationships dictionary
                if "relationships" in other_task:
                    if "depends_on" in other_task["relationships"]:
                        if task["id"] in (other_task["relationships"]["depends_on"] if isinstance(other_task["relationships"]["depends_on"], list) else other_task["relationships"]["depends_on"].keys()):
                            is_blocked = True
                
                # Check direct fields
                if not is_blocked and "depends_on" in other_task:
                    if task["id"] in (other_task["depends_on"] if isinstance(other_task["depends_on"], list) else other_task["depends_on"].keys()):
                        is_blocked = True
                
                if is_blocked:
                    blocked_by_tuple = (other_task.get("name", other_task["id"]), other_task["id"], other_task.get("status", "unknown"))
                    if blocked_by_tuple not in blocked_by:  # Avoid duplicates
                        blocked_by.append(blocked_by_tuple)
            
            # Find tasks that block this task (tasks that this task depends on)
            # We need to check all other tasks to see if they have this task in their blocks list
            for other_task in self.data["tasks"]:
                if other_task["id"] == task["id"]:
                    continue
                
                # Check if other task blocks this task (meaning this task depends on it)
                is_blocking = False
                
                # Check relationships dictionary
                if "relationships" in other_task:
                    if "blocks" in other_task["relationships"]:
                        if task["id"] in (other_task["relationships"]["blocks"] if isinstance(other_task["relationships"]["blocks"], list) else other_task["relationships"]["blocks"].keys()):
                            is_blocking = True
                
                # Check direct fields
                if not is_blocking and "blocks" in other_task:
                    if task["id"] in (other_task["blocks"] if isinstance(other_task["blocks"], list) else other_task["blocks"].keys()):
                        is_blocking = True
                
                if is_blocking:
                    dep_tuple = (other_task.get("name", other_task["id"]), other_task["id"], other_task.get("status", "unknown"))
                    if dep_tuple not in depends_on:  # Avoid duplicates
                        depends_on.append(dep_tuple)
            
            # Find tasks that are documented by this task
            # We need to check all other tasks to see if they have this task in their documented_by list
            for other_task in self.data["tasks"]:
                if other_task["id"] == task["id"]:
                    continue
                
                # Check if other task is documented by this task
                is_documented = False
                
                # Check relationships dictionary
                if "relationships" in other_task:
                    if "documented_by" in other_task["relationships"]:
                        if task["id"] in (other_task["relationships"]["documented_by"] if isinstance(other_task["relationships"]["documented_by"], list) else other_task["relationships"]["documented_by"].keys()):
                            is_documented = True
                
                if is_documented:
                    document_tuple = (other_task.get("name", other_task["id"]), other_task["id"], other_task.get("status", "unknown"))
                    if document_tuple not in documents:  # Avoid duplicates
                        documents.append(document_tuple)
            
            # Find tasks that document this task
            # We need to check all other tasks to see if they have this task in their documents list
            for other_task in self.data["tasks"]:
                if other_task["id"] == task["id"]:
                    continue
                
                # Check if other task documents this task
                is_documenting = False
                
                # Check relationships dictionary
                if "relationships" in other_task:
                    if "documents" in other_task["relationships"]:
                        if task["id"] in (other_task["relationships"]["documents"] if isinstance(other_task["relationships"]["documents"], list) else other_task["relationships"]["documents"].keys()):
                            is_documenting = True
                
                if is_documenting:
                    documented_by_tuple = (other_task.get("name", other_task["id"]), other_task["id"], other_task.get("status", "unknown"))
                    if documented_by_tuple not in documented_by:  # Avoid duplicates
                        documented_by.append(documented_by_tuple)
            
            # Format output
            output = []
            output.append(f"Relationships for task '{task_name}' (ID: {task_id}):\n")
            
            # Show tasks this task depends on
            output.append("Depends on:")
            if depends_on:
                for name, id, status in sorted(depends_on):
                    output.append(f"  - {name} (ID: {id}, Status: {status})")
            else:
                output.append("  None")
            
            # Show tasks this task blocks
            output.append("\nBlocks:")
            if blocks:
                for name, id, status in sorted(blocks):
                    output.append(f"  - {name} (ID: {id}, Status: {status})")
            else:
                output.append("  None")
            
            # Show tasks that block this task
            output.append("\nBlocked by:")
            if blocked_by:
                for name, id, status in sorted(blocked_by):
                    output.append(f"  - {name} (ID: {id}, Status: {status})")
            else:
                output.append("  None")
            
            # Show tasks this task documents
            output.append("\nDocuments:")
            if documents:
                for name, id, status in sorted(documents):
                    output.append(f"  - {name} (ID: {id}, Status: {status})")
            else:
                output.append("  None")
            
            # Show tasks that document this task
            output.append("\nDocumented by:")
            if documented_by:
                for name, id, status in sorted(documented_by):
                    output.append(f"  - {name} (ID: {id}, Status: {status})")
            else:
                output.append("  None")
                
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error listing relationships: {str(e)}", exc_info=True)
            return f"Error listing relationships: {str(e)}"

    def calculate_effort_score(self, task: Dict[str, Any]) -> float:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Related Tasks:
            - tsk_cc15e96f - Implement Revised Task Scoring System (related)
            - tsk_674e247f - Implement Scoring Metrics (related)
            - tsk_4a8cd155 - Create TaskScorer Class (related)
        
        Used By:
            - Dashboard: For sorting tasks by effort required
            - CLI Commands: For displaying effort metrics
            - Priority Queue: For ordering task processing
            - Task Sorting Functions: For organizing task lists
        
        Purpose:
            Calculates a numerical effort score for a task based on its complexity factors
            including dependencies, blocking relationships, subtasks, and checklist items,
            providing a quantitative measure of the work required to complete the task.
        
        Requirements:
            - Must consider task priority (higher priority = lower effort score)
            - Must consider dependency relationships (more dependencies = higher effort)
            - Must consider blocking relationships (more blocks = higher effort)
            - Must count subtasks (more subtasks = higher effort)
            - Must count checklist items (more items = higher effort)
            - Must handle both legacy and modern relationship formats
            - CRITICAL: Lower score must indicate tasks that should be done first
            - CRITICAL: Must use consistent weighting across all tasks
        
        Args:
            task: The task dictionary to calculate effort for
            
        Returns:
            Float representing the effort score (lower values indicate less effort/higher priority)
            
        Formula:
            Base score = priority (1-4)
            + dependency weight * number of dependencies
            + blocks weight * number of tasks this blocks
            + subtask weight * number of subtasks
            + checklist weight * number of checklist items
            
        Example Usage:
            ```python
            # Calculate effort for a task
            effort = file_manager.calculate_effort_score(task)
            
            # Use for sorting
            sorted_tasks = sorted(tasks, key=lambda t: file_manager.calculate_effort_score(t))
            ```
        """
        # Initialize score with priority (1-4, convert so lower priority = higher score)
        priority = task.get("priority", 3)
        score = priority
        
        dependency_count = 0
        blocks_count = 0
        subtask_count = 0
        
        # Count dependencies (things this task depends on)
        if "relationships" in task and "depends_on" in task["relationships"]:
            dependency_count += len(task["relationships"]["depends_on"])
        # Check legacy format
        if "depends_on" in task and isinstance(task["depends_on"], list):
            dependency_count += len(task["depends_on"]) 
        
        # Count blocks (things this task blocks)
        if "relationships" in task and "blocks" in task["relationships"]:
            blocks_count += len(task["relationships"]["blocks"])
        # Check legacy format
        if "blocks" in task and isinstance(task["blocks"], list):
            blocks_count += len(task["blocks"])
        
        # Count subtasks
        if "subtasks" in task and isinstance(task["subtasks"], list):
            subtask_count = len(task["subtasks"])
        
        # Check for checklists (more checklist items = more effort)
        checklist_item_count = 0
        if "checklists" in task:
            if isinstance(task["checklists"], list):
                for checklist in task["checklists"]:
                    if "items" in checklist and isinstance(checklist["items"], list):
                        checklist_item_count += len(checklist["items"])
            elif isinstance(task["checklists"], dict):
                for _, checklist in task["checklists"].items():
                    if "items" in checklist and isinstance(checklist["items"], list):
                        checklist_item_count += len(checklist["items"])
        
        # Check for other tasks that might be blocked by or depend on this task
        for other_task in self.data["tasks"]:
            if other_task["id"] == task["id"]:
                continue
            
            # Check if other task depends on this task
            if "relationships" in other_task:
                if "depends_on" in other_task["relationships"] and task["id"] in other_task["relationships"]["depends_on"]:
                    blocks_count += 1
                
            # Check legacy format
            if "depends_on" in other_task and isinstance(other_task["depends_on"], list):
                if task["id"] in other_task["depends_on"]:
                    blocks_count += 1
        
        # Consider task type (documentation tasks are often easier than implementation tasks)
        task_type_multiplier = 1.0
        task_type = task.get("task_type", "task").lower()
        if task_type == "documentation":
            task_type_multiplier = 0.8  # Documentation tasks are easier
        elif task_type == "feature":
            task_type_multiplier = 1.2  # Feature tasks are harder
        elif task_type == "bug":
            task_type_multiplier = 0.9  # Bug fixes are medium difficulty
        
        # Formula for effort score:
        # - Priority contributes directly (higher priority = lower score)
        # - Dependencies increase score (more dependencies = higher effort)
        # - Blocks increase score (more blocks = higher effort due to more impact)
        # - Subtasks increase score (more subtasks = higher effort)
        # - Checklist items increase score slightly (more items = more steps to complete)
        # - We weight blocks slightly higher than dependencies as they represent impact
        # - Task type affects overall score
        
        score = (
            priority + 
            (dependency_count * 0.8) +  # Each dependency adds 0.8 to score
            (blocks_count * 1.0) +      # Each blocked task adds 1.0 to score
            (subtask_count * 0.5) +     # Each subtask adds 0.5 to score
            (checklist_item_count * 0.1) # Each checklist item adds 0.1 to score
        ) * task_type_multiplier
        
        return score

    def get_tasks_with_scores(self) -> List[Dict[str, Any]]:
        """
        Get all tasks with calculated scores.
        
        This method uses the TaskScorer class to calculate comprehensive
        scores for each task, including effort, effectiveness, risk, 
        urgency, and total scores.
        
        Returns:
            List of tasks with score information added
        """
        # Initialize the TaskScorer with all tasks for normalization
        scorer = TaskScorer(self.data["tasks"])
        
        # Calculate scores for each task
        tasks_with_scores = []
        for task in self.data["tasks"]:
            # Calculate scores
            scores = scorer.calculate_scores(task)
            
            # Create a copy of the task
            task_copy = task.copy()
            
            # Add scores to the task
            task_copy["scores"] = scores
            
            # Add individual scores as top-level properties for easier access
            task_copy["effort_score"] = scores["effort"]
            task_copy["effectiveness_score"] = scores["effectiveness"]
            task_copy["risk_score"] = scores["risk"]
            task_copy["urgency_score"] = scores["urgency"]
            task_copy["total_score"] = scores["total"]
            
            tasks_with_scores.append(task_copy)
            
        return tasks_with_scores
    
    def get_tasks_ordered_by_total_score(self) -> List[Dict[str, Any]]:
        """
        Get all tasks ordered by total score (highest first).
        
        This method uses the comprehensive scoring system to sort tasks
        by their total score, which combines effort, effectiveness, risk,
        and urgency with appropriate weights.
        
        Returns:
            List of tasks ordered by total score (descending - highest score first)
        """
        # Get tasks with scores
        tasks = self.get_tasks_with_scores()
        
        # Sort by total score (descending - highest score first)
        tasks.sort(key=lambda x: x["total_score"], reverse=True)
        
        return tasks
    
    def get_tasks_ordered_by_effort(self) -> List[Dict[str, Any]]:
        """
        Get all tasks ordered by effort score (easiest/least dependent first).
        
        Returns:
            List of tasks ordered by effort score (ascending)
        """
        # Use the new scoring system
        tasks = self.get_tasks_with_scores()
        
        # Sort by effort score (ascending - lowest effort first)
        tasks.sort(key=lambda x: x["effort_score"])
        
        return tasks
    
    def find_task(self, task_id_or_name: str) -> Optional[Dict[str, Any]]:
        """
        Task: tsk_1234abcd - Update Task Command Functionality
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Update Type Command: For finding tasks by ID or name
            - Task Management Tools: For retrieving task data
            
        Purpose:
            Provides a consistent way to find a task by either its ID or name,
            with a more intuitive naming than find_task_by_id_or_name.
            
        Requirements:
            - Must search by both ID and name
            - Must return None if task not found (not raise an exception)
            - Must be consistent with find_task_by_id_or_name behavior
            
        Args:
            task_id_or_name: Task ID or name to search for
            
        Returns:
            Task dictionary if found, None otherwise
            
        Changes:
            - v1: Initial implementation as alias for _find_task_by_id_or_name
        """
        return self._find_task_by_id_or_name(task_id_or_name)
    
    def add_task_comment(self, task_id: str, text: str, author: str = "user") -> Dict[str, Any]:
        """
        Task: tsk_1234abcd - Update Task Command Functionality
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - CLI Type Update Command: For adding comments when updating task type
            - CLI Update Command: For adding comments during updates
            
        Purpose:
            Adds a comment to a task with standard interface matching CoreManager.
            
        Requirements:
            - Must be compatible with CoreManager interface
            - Must handle user attribution
            - Must preserve timestamps
            
        Args:
            task_id: ID of the task to add a comment to
            text: Comment text content
            author: Name of the comment author (default: "user")
            
        Returns:
            The updated task dictionary
            
        Changes:
            - v1: Initial implementation as alias for add_comment method
            - v2: Added automatic save to ensure comments are persisted
        """
        comment = self.add_comment(task_id, text, author)
        self.save()  # Save changes to file
        return comment

    def _migrate_task_container_ids(self) -> None:
        """
        Task: tsk_ff8e47b1 - Update Task Entity with Parent Tracking
        Document: refactor/core/file_manager.py
        dohcount: 1
        
        Used By:
            - FileManager.initialize: Called during initialization
            
        Purpose:
            Migrates existing tasks to use the new container_id field by examining
            list assignments and updating tasks accordingly. This ensures backward
            compatibility with the new container-based parent tracking system.
            
        Requirements:
            - Must handle both list_id and tasks arrays
            - Must not overwrite existing container_id values
            - Must maintain data consistency
            - CRITICAL: Must be idempotent (safe to run multiple times)
            
        Returns:
            None
        """
        if "tasks" not in self.data or "lists" not in self.data:
            return
            
        # Build a mapping of task_id to list_id from list task arrays
        task_to_list_map = {}
        
        for list_obj in self.data.get("lists", []):
            list_id = list_obj.get("id")
            if not list_id:
                continue
                
            for task_id in list_obj.get("tasks", []):
                task_to_list_map[task_id] = list_id
        
        # Update task container_id fields
        for task in self.data.get("tasks", []):
            task_id = task.get("id")
            if not task_id:
                continue
                
            # Skip if container_id is already set
            if "container_id" in task and task["container_id"]:
                continue
                
            # First check if task is in the task_to_list_map
            if task_id in task_to_list_map:
                task["container_id"] = task_to_list_map[task_id]
            # Then fall back to list_id if available
            elif "list_id" in task and task["list_id"]:
                task["container_id"] = task["list_id"]
                
        logger.info(f"Migrated container_id for {len(task_to_list_map)} tasks.")