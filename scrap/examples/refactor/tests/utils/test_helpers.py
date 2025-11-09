"""
Test helpers and utilities for the ClickUp JSON Manager test suite.

This module provides reusable functions and classes for:
- Creating test fixtures
- Setting up test environments
- Common assertions
- Mock objects and factories
"""
import os
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# Type aliases
TaskDict = Dict[str, Any]
EntityDict = Dict[str, Any]


class TestFixtureFactory:
    """Factory for creating test fixtures."""
    
    @staticmethod
    def create_task(
        id: str = "tsk_test001",
        name: str = "Test Task",
        status: str = "to do",
        priority: int = 1,
        description: str = "Test task description",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> TaskDict:
        """
        Create a task fixture with customizable properties.
        
        Args:
            id: Task ID
            name: Task name
            status: Task status
            priority: Task priority
            description: Task description
            tags: List of tags
            **kwargs: Additional task properties
            
        Returns:
            Dictionary representing a task
        """
        task = {
            "id": id,
            "name": name,
            "status": status,
            "priority": priority,
            "description": description,
            "tags": tags or ["test"],
            "subtasks": [],
            "comments": [],
            "checklists": []
        }
        
        # Add any additional properties
        task.update(kwargs)
        
        return task
    
    @staticmethod
    def create_space(
        id: str = "spc_test001",
        name: str = "Test Space",
        **kwargs
    ) -> EntityDict:
        """
        Create a space fixture.
        
        Args:
            id: Space ID
            name: Space name
            **kwargs: Additional space properties
            
        Returns:
            Dictionary representing a space
        """
        space = {
            "id": id,
            "name": name,
        }
        
        # Add any additional properties
        space.update(kwargs)
        
        return space
    
    @staticmethod
    def create_folder(
        id: str = "fld_test001",
        name: str = "Test Folder",
        space_id: str = "spc_test001",
        **kwargs
    ) -> EntityDict:
        """
        Create a folder fixture.
        
        Args:
            id: Folder ID
            name: Folder name
            space_id: Parent space ID
            **kwargs: Additional folder properties
            
        Returns:
            Dictionary representing a folder
        """
        folder = {
            "id": id,
            "name": name,
            "space_id": space_id,
        }
        
        # Add any additional properties
        folder.update(kwargs)
        
        return folder
    
    @staticmethod
    def create_list(
        id: str = "lst_test001",
        name: str = "Test List",
        folder_id: str = "fld_test001",
        **kwargs
    ) -> EntityDict:
        """
        Create a list fixture.
        
        Args:
            id: List ID
            name: List name
            folder_id: Parent folder ID
            **kwargs: Additional list properties
            
        Returns:
            Dictionary representing a list
        """
        list_entity = {
            "id": id,
            "name": name,
            "folder_id": folder_id,
        }
        
        # Add any additional properties
        list_entity.update(kwargs)
        
        return list_entity
    
    @staticmethod
    def create_checklist(
        id: str = "chk_test001",
        name: str = "Test Checklist",
        items: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> EntityDict:
        """
        Create a checklist fixture.
        
        Args:
            id: Checklist ID
            name: Checklist name
            items: List of checklist items
            **kwargs: Additional checklist properties
            
        Returns:
            Dictionary representing a checklist
        """
        if items is None:
            items = [
                {
                    "id": "itm_test001",
                    "name": "Test Item 1",
                    "checked": False
                },
                {
                    "id": "itm_test002",
                    "name": "Test Item 2",
                    "checked": True
                }
            ]
        
        checklist = {
            "id": id,
            "name": name,
            "items": items
        }
        
        # Add any additional properties
        checklist.update(kwargs)
        
        return checklist
    
    @staticmethod
    def create_comment(
        id: str = "cmt_test001",
        text: str = "Test comment",
        **kwargs
    ) -> EntityDict:
        """
        Create a comment fixture.
        
        Args:
            id: Comment ID
            text: Comment text
            **kwargs: Additional comment properties
            
        Returns:
            Dictionary representing a comment
        """
        comment = {
            "id": id,
            "text": text,
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        # Add any additional properties
        comment.update(kwargs)
        
        return comment


class TestFileManager:
    """Manages temporary files and directories for tests."""
    
    @staticmethod
    def create_temp_dir() -> str:
        """
        Create a temporary directory.
        
        Returns:
            Path to the temporary directory
        """
        return tempfile.mkdtemp()
    
    @staticmethod
    def create_temp_file(content: Optional[str] = None, suffix: str = ".json") -> str:
        """
        Create a temporary file with optional content.
        
        Args:
            content: Content to write to the file
            suffix: File suffix
            
        Returns:
            Path to the temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        if content:
            with open(path, 'w') as f:
                f.write(content)
        
        return path
    
    @staticmethod
    def create_test_template(data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a test template file.
        
        Args:
            data: Template data (uses default if None)
            
        Returns:
            Path to the test template
        """
        if data is None:
            # Create a basic template structure
            data = {
                "spaces": [
                    TestFixtureFactory.create_space()
                ],
                "folders": [
                    TestFixtureFactory.create_folder()
                ],
                "lists": [
                    TestFixtureFactory.create_list()
                ],
                "tasks": [
                    TestFixtureFactory.create_task()
                ]
            }
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        
        # Write the template data
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return path
    
    @staticmethod
    def cleanup_temp_file(path: str) -> None:
        """
        Delete a temporary file.
        
        Args:
            path: Path to the file to delete
        """
        try:
            os.unlink(path)
        except (OSError, FileNotFoundError):
            pass
    
    @staticmethod
    def cleanup_temp_dir(path: str) -> None:
        """
        Delete a temporary directory.
        
        Args:
            path: Path to the directory to delete
        """
        try:
            shutil.rmtree(path)
        except (OSError, FileNotFoundError):
            pass


class TestAssertions:
    """Custom assertions for testing."""
    
    @staticmethod
    def assert_task_equal(
        test_case,
        actual: Union[Dict[str, Any], Any],
        expected: Union[Dict[str, Any], Any],
        check_fields: Optional[List[str]] = None
    ) -> None:
        """
        Assert that a task matches the expected values.
        
        Args:
            test_case: TestCase instance for assertions
            actual: Actual task object or dictionary
            expected: Expected task object or dictionary
            check_fields: List of fields to check (all fields if None)
        """
        # Convert objects to dictionaries if needed
        actual_dict = actual if isinstance(actual, dict) else actual.__dict__
        expected_dict = expected if isinstance(expected, dict) else expected.__dict__
        
        # Determine fields to check
        fields = check_fields or list(expected_dict.keys())
        
        # Check each field
        for field in fields:
            test_case.assertEqual(
                actual_dict.get(field),
                expected_dict.get(field),
                f"Field '{field}' does not match"
            )
    
    @staticmethod
    def assert_contains_task_with_name(
        test_case,
        tasks: List[Union[Dict[str, Any], Any]],
        name: str
    ) -> None:
        """
        Assert that a list of tasks contains a task with the specified name.
        
        Args:
            test_case: TestCase instance for assertions
            tasks: List of task objects or dictionaries
            name: Expected task name
        """
        for task in tasks:
            task_name = task.get('name') if isinstance(task, dict) else getattr(task, 'name', None)
            if task_name == name:
                return
        
        test_case.fail(f"No task with name '{name}' found in task list")
    
    @staticmethod
    def assert_json_file_contains_entity(
        test_case,
        file_path: str,
        entity_type: str,
        entity_id: str
    ) -> None:
        """
        Assert that a JSON file contains an entity with the specified ID.
        
        Args:
            test_case: TestCase instance for assertions
            file_path: Path to the JSON file
            entity_type: Type of entity (tasks, spaces, folders, lists)
            entity_id: Expected entity ID
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        entities = data.get(entity_type, [])
        
        for entity in entities:
            if entity.get('id') == entity_id:
                return
        
        test_case.fail(f"No {entity_type[:-1]} with ID '{entity_id}' found in file")


# Path utilities
def get_test_resources_dir() -> Path:
    """
    Get the path to the test resources directory.
    
    Returns:
        Path to test resources directory
    """
    current_dir = Path(__file__).resolve().parent
    tests_dir = current_dir.parent
    resources_dir = tests_dir / "resources"
    
    # Create the directory if it doesn't exist
    resources_dir.mkdir(exist_ok=True)
    
    return resources_dir

def get_sample_template_path() -> Path:
    """
    Get the path to the sample template file.
    
    Returns:
        Path to sample template file
    """
    resources_dir = get_test_resources_dir()
    template_path = resources_dir / "sample_template.json"
    
    # Create the file if it doesn't exist
    if not template_path.exists():
        data = {
            "spaces": [
                TestFixtureFactory.create_space()
            ],
            "folders": [
                TestFixtureFactory.create_folder()
            ],
            "lists": [
                TestFixtureFactory.create_list()
            ],
            "tasks": [
                TestFixtureFactory.create_task()
            ]
        }
        
        with open(template_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return template_path 