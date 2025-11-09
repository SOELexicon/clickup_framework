from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from managers.task_manager import get_manager

def create_task(task_data: Dict[str, Any], 
               json_file: str, 
               parent_name: Optional[str] = None, 
               assigned_to: Optional[List[str]] = None,
               tags: Optional[List[str]] = None,
               priority: str = "normal",
               status: str = "to do",
               task_type: Optional[str] = None,
               document_section: Optional[str] = None,
               format: Optional[str] = None,
               target_audience: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a new task.
    
    Args:
        task_data: Task data dictionary with name and description
        json_file: Path to the JSON file
        parent_name: Name of the parent task
        assigned_to: List of users assigned to the task
        tags: List of tags for the task
        priority: Priority of the task (urgent, high, normal, low)
        status: Status of the task (to do, in progress, in review, blocked, complete)
        task_type: Type of task (TASK, FEATURE, BUG, DOCUMENTATION, etc.)
        document_section: Section of the document (for DOCUMENTATION tasks)
        format: Format of the document (for DOCUMENTATION tasks)
        target_audience: Target audience for the document (for DOCUMENTATION tasks)
        
    Returns:
        The created task dictionary
    """
    logger = get_logger()
    
    try:
        # Extract required fields
        name = task_data.get("name")
        description = task_data.get("description", "")
        
        if not name:
            raise ValueError("Task name is required")
        
        # Initialize the manager
        manager = get_manager(json_file)
        
        # Find parent task if specified
        parent_id = None
        if parent_name:
            parent_task = manager.find_task_by_name(parent_name)
            if not parent_task:
                raise ValueError(f"Parent task '{parent_name}' not found")
            parent_id = parent_task.get("id")
        
        # Create task data
        create_data = {
            "name": name,
            "description": description,
            "status": status,
            "priority": priority,
            "parent_id": parent_id,
            "assigned_to": assigned_to,
            "tags": tags or []
        }
        
        # Add task_type if specified
        if task_type:
            create_data["task_type"] = task_type
            
            # Add documentation-specific fields if this is a documentation task
            if task_type.upper() == "DOCUMENTATION":
                if document_section:
                    create_data["document_section"] = document_section
                if format:
                    create_data["format"] = format
                if target_audience:
                    create_data["target_audience"] = target_audience
        
        # Create the task
        task = manager.create_task(create_data)
        
        logger.info(f"Created task: {task['name']} with ID: {task['id']}")
        
        return task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise 