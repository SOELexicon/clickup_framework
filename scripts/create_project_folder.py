#!/usr/bin/env python3
"""
Create ClickUp Framework Project Folder

Creates a project folder structure in ClickUp for managing the ClickUp Framework project.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def create_project_structure():
    """Create the ClickUp Framework project folder structure."""

    # Configuration
    SPACE_ID = "90157903115"  # Your ClickUp space
    PROJECT_NAME = "ClickUp Framework"

    print("=" * 80)
    print(f"Creating ClickUp Framework Project Structure")
    print("=" * 80)
    print()

    # Initialize client
    client = ClickUpClient()

    # Create main project folder
    print(f"Creating folder: {PROJECT_NAME}")
    folder = client.create_folder(SPACE_ID, PROJECT_NAME)
    folder_id = folder["id"]
    print(f"✓ Folder created: {folder_id}")
    print(f"  URL: https://app.clickup.com/{SPACE_ID}/v/f/{folder_id}")
    print()

    # Create lists within the folder
    lists_to_create = [
        {
            "name": "Development Tasks",
            "description": "Core development tasks for the ClickUp Framework"
        },
        {
            "name": "Feature Requests",
            "description": "New features to implement"
        },
        {
            "name": "Bug Fixes",
            "description": "Bugs and issues to fix"
        },
        {
            "name": "Documentation",
            "description": "Documentation tasks and improvements"
        },
        {
            "name": "Testing",
            "description": "Testing and quality assurance tasks"
        },
        {
            "name": "Releases",
            "description": "Release planning and management"
        }
    ]

    created_lists = []

    for list_config in lists_to_create:
        print(f"Creating list: {list_config['name']}")
        list_data = client.create_list(
            folder_id,
            list_config["name"],
            content=list_config.get("description", "")
        )
        created_lists.append(list_data)
        print(f"✓ List created: {list_data['id']}")
        print()

    # Summary
    print("=" * 80)
    print("PROJECT STRUCTURE CREATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"Folder: {PROJECT_NAME}")
    print(f"  ID: {folder_id}")
    print(f"  URL: https://app.clickup.com/{SPACE_ID}/v/f/{folder_id}")
    print()
    print(f"Lists created: {len(created_lists)}")
    for lst in created_lists:
        print(f"  - {lst['name']} (ID: {lst['id']})")
    print()
    print("=" * 80)

    return {
        "folder": folder,
        "lists": created_lists
    }


if __name__ == "__main__":
    try:
        result = create_project_structure()
        print("\n✓ Project structure created successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error creating project structure: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
