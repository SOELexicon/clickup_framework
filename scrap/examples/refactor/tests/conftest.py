"""
Pytest configuration and fixtures.

This module provides common fixtures for all tests.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from refactor.tests.utils.test_helpers import (
    TestFixtureFactory,
    TestFileManager
)
from refactor.tests.utils.mock_repository import MockRepositoryFactory, InMemoryRepository


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    
    Yields:
        Path to the temporary directory
    """
    temp_dir = TestFileManager.create_temp_dir()
    yield temp_dir
    TestFileManager.cleanup_temp_dir(temp_dir)


@pytest.fixture
def temp_file():
    """
    Create a temporary file.
    
    Yields:
        Path to the temporary file
    """
    temp_file = TestFileManager.create_temp_file()
    yield temp_file
    TestFileManager.cleanup_temp_file(temp_file)


@pytest.fixture
def sample_template_file(temp_dir):
    """
    Create a sample template file in the temporary directory.
    
    Args:
        temp_dir: Temporary directory (from the temp_dir fixture)
        
    Returns:
        Path to the sample template file
    """
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
    
    # Create the template file
    template_path = os.path.join(temp_dir, "sample_template.json")
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return template_path


@pytest.fixture
def sample_task():
    """
    Create a sample task dictionary.
    
    Returns:
        Dictionary representing a task
    """
    return TestFixtureFactory.create_task()


@pytest.fixture
def sample_space():
    """
    Create a sample space dictionary.
    
    Returns:
        Dictionary representing a space
    """
    return TestFixtureFactory.create_space()


@pytest.fixture
def sample_folder():
    """
    Create a sample folder dictionary.
    
    Returns:
        Dictionary representing a folder
    """
    return TestFixtureFactory.create_folder()


@pytest.fixture
def sample_list():
    """
    Create a sample list dictionary.
    
    Returns:
        Dictionary representing a list
    """
    return TestFixtureFactory.create_list()


@pytest.fixture
def complex_template_file(temp_dir):
    """
    Create a complex template file with multiple entities and relationships.
    
    Args:
        temp_dir: Temporary directory (from the temp_dir fixture)
        
    Returns:
        Path to the complex template file
    """
    # Create spaces
    space1 = TestFixtureFactory.create_space(id="spc_test001", name="Work Space")
    space2 = TestFixtureFactory.create_space(id="spc_test002", name="Personal Space")
    
    # Create folders
    folder1 = TestFixtureFactory.create_folder(id="fld_test001", name="Projects", space_id=space1["id"])
    folder2 = TestFixtureFactory.create_folder(id="fld_test002", name="Tasks", space_id=space1["id"])
    folder3 = TestFixtureFactory.create_folder(id="fld_test003", name="Home", space_id=space2["id"])
    
    # Create lists
    list1 = TestFixtureFactory.create_list(id="lst_test001", name="Development", folder_id=folder1["id"])
    list2 = TestFixtureFactory.create_list(id="lst_test002", name="Design", folder_id=folder1["id"])
    list3 = TestFixtureFactory.create_list(id="lst_test003", name="Daily Tasks", folder_id=folder2["id"])
    list4 = TestFixtureFactory.create_list(id="lst_test004", name="Shopping", folder_id=folder3["id"])
    
    # Create tasks
    task1 = TestFixtureFactory.create_task(
        id="tsk_test001",
        name="Implement Feature X",
        status="in progress",
        priority=1,
        description="Implement feature X for the project",
        tags=["development", "feature"]
    )
    
    task2 = TestFixtureFactory.create_task(
        id="tsk_test002",
        name="Design UI Components",
        status="to do",
        priority=2,
        description="Design UI components for the project",
        tags=["design", "ui"]
    )
    
    task3 = TestFixtureFactory.create_task(
        id="tsk_test003",
        name="Fix Bug #123",
        status="to do",
        priority=3,
        description="Fix bug #123 in the login form",
        tags=["bug", "urgent"]
    )
    
    task4 = TestFixtureFactory.create_task(
        id="tsk_test004",
        name="Buy Groceries",
        status="to do",
        priority=2,
        description="Buy groceries for the week",
        tags=["shopping", "personal"]
    )
    
    # Create subtasks
    subtask1 = TestFixtureFactory.create_task(
        id="stk_test001",
        name="Research API Options",
        status="complete",
        priority=2,
        description="Research API options for feature X",
        parent_id=task1["id"]
    )
    
    subtask2 = TestFixtureFactory.create_task(
        id="stk_test002",
        name="Implement Backend API",
        status="in progress",
        priority=1,
        description="Implement backend API for feature X",
        parent_id=task1["id"]
    )
    
    subtask3 = TestFixtureFactory.create_task(
        id="stk_test003",
        name="Implement Frontend UI",
        status="to do",
        priority=2,
        description="Implement frontend UI for feature X",
        parent_id=task1["id"]
    )
    
    # Create the template data
    data = {
        "spaces": [space1, space2],
        "folders": [folder1, folder2, folder3],
        "lists": [list1, list2, list3, list4],
        "tasks": [task1, task2, task3, task4, subtask1, subtask2, subtask3]
    }
    
    # Create the template file
    template_path = os.path.join(temp_dir, "complex_template.json")
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return template_path


@pytest.fixture
def mock_task_repository():
    """
    Create a mock task repository.
    
    Returns:
        InMemoryRepository instance for TaskEntity
    """
    return MockRepositoryFactory.create_task_repository()


@pytest.fixture
def mock_space_repository():
    """
    Create a mock space repository.
    
    Returns:
        InMemoryRepository instance for SpaceEntity
    """
    return MockRepositoryFactory.create_space_repository()


@pytest.fixture
def mock_folder_repository():
    """
    Create a mock folder repository.
    
    Returns:
        InMemoryRepository instance for FolderEntity
    """
    return MockRepositoryFactory.create_folder_repository()


@pytest.fixture
def mock_list_repository():
    """
    Create a mock list repository.
    
    Returns:
        InMemoryRepository instance for ListEntity
    """
    return MockRepositoryFactory.create_list_repository()


@pytest.fixture
def mock_repositories():
    """
    Create all mock repositories.
    
    Returns:
        Dictionary of repository instances keyed by entity type
    """
    return MockRepositoryFactory.create_all_repositories()


@pytest.fixture
def populated_mock_task_repository():
    """
    Create a mock task repository populated with sample tasks.
    
    Returns:
        InMemoryRepository instance with sample tasks
    """
    from refactor.core.entities.task_entity import TaskEntity
    
    # Create the repository
    repository = MockRepositoryFactory.create_task_repository()
    
    # Create and add sample tasks
    task1 = TaskEntity(
        entity_id="tsk_test001",
        name="Task 1",
        status="to do",
        priority=1,
        description="Description for Task 1"
    )
    repository.add(task1)
    
    task2 = TaskEntity(
        entity_id="tsk_test002",
        name="Task 2",
        status="in progress",
        priority=2,
        description="Description for Task 2"
    )
    repository.add(task2)
    
    task3 = TaskEntity(
        entity_id="tsk_test003",
        name="Task 3",
        status="complete",
        priority=3,
        description="Description for Task 3"
    )
    repository.add(task3)
    
    # Create a subtask
    subtask = TaskEntity(
        entity_id="stk_test001",
        name="Subtask 1",
        status="to do",
        priority=2,
        description="Description for Subtask 1",
        parent_id="tsk_test001"
    )
    repository.add(subtask)
    
    return repository 