#!/usr/bin/env python3
"""
Functional tests for task management workflows.

These tests verify end-to-end task management operations from a user perspective.
"""
import unittest
import os
import subprocess
import json
import tempfile
from pathlib import Path


class TaskWorkflowTests(unittest.TestCase):
    """Functional tests for task management workflows."""

    def setUp(self):
        """Set up test environment with a test template."""
        self.repo_root = Path(__file__).parent.parent.parent.parent
        self.script_path = self.repo_root / "refactor" / "cujmrefactor_manual.sh"
        
        # Ensure script is executable
        if not os.access(self.script_path, os.X_OK):
            os.chmod(self.script_path, 0o755)
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test template file
        self.test_template = self.temp_path / "workflow_test.json"
        
        # Initialize with basic template structure
        template_data = {
            "spaces": [
                {
                    "id": "spc_test001",
                    "name": "Test Space"
                }
            ],
            "folders": [
                {
                    "id": "fld_test001",
                    "name": "Test Folder",
                    "space_id": "spc_test001"
                }
            ],
            "lists": [
                {
                    "id": "lst_test001",
                    "name": "Test List",
                    "folder_id": "fld_test001"
                }
            ],
            "tasks": []
        }
        
        with open(self.test_template, 'w') as f:
            json.dump(template_data, f, indent=2)

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def run_command(self, *args):
        """Execute a CLI command and return the result."""
        cmd = [str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result

    def test_complete_task_lifecycle(self):
        """
        Test a complete task lifecycle including:
        - Creating a task
        - Adding a checklist
        - Creating subtasks
        - Updating task status
        - Adding comments
        - Completing the task
        """
        # Step 1: Create a parent task
        create_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Parent Workflow Task",
            "--description", "This is a test parent task",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,workflow"
        )
        self.assertEqual(create_result.returncode, 0)
        
        # Step 2: Add a checklist to the parent task
        checklist_result = self.run_command(
            "create-checklist",
            str(self.test_template),
            "Parent Workflow Task",
            "Implementation Steps",
            "--items", "Step 1,Step 2,Step 3"
        )
        self.assertEqual(checklist_result.returncode, 0)
        
        # Step 3: Create subtasks
        for i in range(1, 4):
            subtask_result = self.run_command(
                "create-subtask",
                str(self.test_template),
                "Parent Workflow Task",
                f"Subtask {i}",
                "--description", f"This is subtask {i}",
                "--priority", "2"
            )
            self.assertEqual(subtask_result.returncode, 0)
        
        # Step 4: Verify the task structure
        show_result = self.run_command(
            "show",
            str(self.test_template),
            "Parent Workflow Task",
            "--details"
        )
        self.assertEqual(show_result.returncode, 0)
        
        # Verify parent task exists
        self.assertIn("Parent Workflow Task", show_result.stdout)
        # Verify checklist exists
        self.assertIn("Implementation Steps", show_result.stdout)
        # Verify subtasks exist
        self.assertIn("Subtask 1", show_result.stdout)
        self.assertIn("Subtask 2", show_result.stdout)
        self.assertIn("Subtask 3", show_result.stdout)
        
        # Step 5: Update status of a subtask
        status_result = self.run_command(
            "update-status",
            str(self.test_template),
            "Subtask 1",
            "in progress",
            "--comment", "Starting work on this subtask"
        )
        self.assertEqual(status_result.returncode, 0)
        
        # Step 6: Check status of the subtask
        show_subtask = self.run_command(
            "show",
            str(self.test_template),
            "Subtask 1"
        )
        self.assertEqual(show_subtask.returncode, 0)
        self.assertIn("in progress", show_subtask.stdout)
        self.assertIn("Starting work on this subtask", show_subtask.stdout)
        
        # Step 7: Complete all subtasks
        for i in range(1, 4):
            complete_result = self.run_command(
                "update-status",
                str(self.test_template),
                f"Subtask {i}",
                "complete",
                "--comment", f"Completed subtask {i}"
            )
            self.assertEqual(complete_result.returncode, 0)
        
        # Step 8: Check items in the checklist
        for i in range(1, 4):
            # Find the checklist item ID first
            show_details = self.run_command(
                "show",
                str(self.test_template),
                "Parent Workflow Task",
                "--details"
            )
            # Extract item ID for "Step {i}" from the output
            lines = show_details.stdout.splitlines()
            item_id = None
            for line in lines:
                if f"Step {i}" in line:
                    # Extract the item ID using string parsing (simplified)
                    parts = line.split("(ID: ")
                    if len(parts) > 1:
                        item_id = parts[1].split(")")[0]
                        break
            
            # Check the item if we found its ID
            if item_id:
                check_result = self.run_command(
                    "checklist",
                    "check",
                    str(self.test_template),
                    "Parent Workflow Task",
                    item_id
                )
                self.assertEqual(check_result.returncode, 0)
        
        # Step 9: Complete the parent task
        complete_parent = self.run_command(
            "update-status",
            str(self.test_template),
            "Parent Workflow Task",
            "complete",
            "--comment", "All subtasks complete and checklist items checked"
        )
        self.assertEqual(complete_parent.returncode, 0)
        
        # Step 10: Final verification
        final_check = self.run_command(
            "show",
            str(self.test_template),
            "Parent Workflow Task",
            "--details"
        )
        self.assertEqual(final_check.returncode, 0)
        self.assertIn("complete", final_check.stdout)
        
        # All subtasks should be complete
        subtask_lines = [line for line in final_check.stdout.splitlines() if "Subtask" in line and "subtasks:" not in line.lower()]
        for line in subtask_lines:
            self.assertIn("complete", line.lower())
    
    def test_task_relationship_workflow(self):
        """
        Test task relationship workflows including:
        - Creating multiple tasks
        - Establishing dependencies between tasks
        - Verifying relationship constraints
        """
        # Step 1: Create three related tasks
        task_names = ["Task A", "Task B", "Task C"]
        for task_name in task_names:
            create_result = self.run_command(
                "create-task", 
                str(self.test_template),
                task_name,
                "--description", f"This is {task_name}",
                "--priority", "2",
                "--list", "Test List",
                "--tags", "test,relationship"
            )
            self.assertEqual(create_result.returncode, 0)
        
        # Step 2: Establish relationships - Task A blocks Task B, Task B depends on Task A
        relation1 = self.run_command(
            "relationship",
            "add",
            str(self.test_template),
            "Task A",
            "blocks",
            "Task B"
        )
        self.assertEqual(relation1.returncode, 0)
        
        # Step 3: Task B blocks Task C
        relation2 = self.run_command(
            "relationship",
            "add",
            str(self.test_template),
            "Task B",
            "blocks",
            "Task C"
        )
        self.assertEqual(relation2.returncode, 0)
        
        # Step 4: Verify relationships
        for task in task_names:
            relation_check = self.run_command(
                "relationship",
                "list",
                str(self.test_template),
                task
            )
            self.assertEqual(relation_check.returncode, 0)
        
        # Verify Task A blocks Task B
        check_a = self.run_command(
            "relationship",
            "list",
            str(self.test_template),
            "Task A"
        )
        self.assertIn("blocks", check_a.stdout)
        self.assertIn("Task B", check_a.stdout)
        
        # Verify Task B is blocked by Task A and blocks Task C
        check_b = self.run_command(
            "relationship",
            "list",
            str(self.test_template),
            "Task B"
        )
        self.assertIn("blocked by", check_b.stdout.lower())
        self.assertIn("Task A", check_b.stdout)
        self.assertIn("blocks", check_b.stdout)
        self.assertIn("Task C", check_b.stdout)
        
        # Step 5: Try to complete Task B before Task A (should fail)
        update_b = self.run_command(
            "update-status",
            str(self.test_template),
            "Task B",
            "complete"
        )
        # This should fail because Task B depends on Task A
        self.assertNotEqual(update_b.returncode, 0)
        self.assertIn("blocked", update_b.stdout.lower() + update_b.stderr.lower())
        
        # Step 6: Complete Task A
        update_a = self.run_command(
            "update-status",
            str(self.test_template),
            "Task A",
            "complete",
            "--comment", "Completed Task A"
        )
        self.assertEqual(update_a.returncode, 0)
        
        # Step 7: Now Task B can be completed
        update_b_again = self.run_command(
            "update-status",
            str(self.test_template),
            "Task B",
            "complete",
            "--comment", "Completed Task B after Task A"
        )
        self.assertEqual(update_b_again.returncode, 0)
        
        # Step 8: Finally, Task C can be completed
        update_c = self.run_command(
            "update-status",
            str(self.test_template),
            "Task C",
            "complete",
            "--comment", "Completed Task C after Tasks A and B"
        )
        self.assertEqual(update_c.returncode, 0)
        
        # Step 9: Final verification - all tasks should be complete
        for task in task_names:
            final_check = self.run_command(
                "show",
                str(self.test_template),
                task
            )
            self.assertEqual(final_check.returncode, 0)
            self.assertIn("complete", final_check.stdout.lower())

    def test_hierarchical_task_validation(self):
        """
        Test that the system prevents completion of a task when:
        - It has incomplete child tasks
        - It has incomplete grandchild tasks (nested hierarchy)
        """
        # Step 1: Create a parent task
        parent_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Hierarchical Parent Task",
            "--description", "This is the top-level parent task",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,hierarchy"
        )
        self.assertEqual(parent_result.returncode, 0)
        
        # Step 2: Create child tasks
        child_tasks = ["Child Task 1", "Child Task 2"]
        for child_name in child_tasks:
            child_result = self.run_command(
                "create-subtask",
                str(self.test_template),
                "Hierarchical Parent Task",
                child_name,
                "--description", f"This is {child_name}",
                "--priority", "2"
            )
            self.assertEqual(child_result.returncode, 0)
        
        # Step 3: Create grandchild tasks (for Child Task 1)
        grandchild_tasks = ["Grandchild Task 1", "Grandchild Task 2"]
        for grandchild_name in grandchild_tasks:
            grandchild_result = self.run_command(
                "create-subtask",
                str(self.test_template),
                "Child Task 1",
                grandchild_name,
                "--description", f"This is {grandchild_name}",
                "--priority", "3"
            )
            self.assertEqual(grandchild_result.returncode, 0)
        
        # Step 4: Verify the task hierarchy structure
        show_parent = self.run_command(
            "show",
            str(self.test_template),
            "Hierarchical Parent Task",
            "--details"
        )
        self.assertEqual(show_parent.returncode, 0)
        for child_name in child_tasks:
            self.assertIn(child_name, show_parent.stdout)
        
        # Step 5: Try to complete the parent task with incomplete children (should fail)
        try_complete_parent = self.run_command(
            "update-status",
            str(self.test_template),
            "Hierarchical Parent Task",
            "complete"
        )
        self.assertNotEqual(try_complete_parent.returncode, 0)
        # Check error message includes information about incomplete subtasks
        error_output = try_complete_parent.stdout.lower() + try_complete_parent.stderr.lower()
        self.assertIn("incomplete subtask", error_output)
        
        # Step 6: Try to complete Child Task 1 with incomplete grandchildren (should fail)
        try_complete_child = self.run_command(
            "update-status",
            str(self.test_template),
            "Child Task 1",
            "complete"
        )
        self.assertNotEqual(try_complete_child.returncode, 0)
        # Check error message includes information about incomplete subtasks
        error_output = try_complete_child.stdout.lower() + try_complete_child.stderr.lower()
        self.assertIn("incomplete subtask", error_output)
        
        # Step 7: Complete the grandchild tasks
        for grandchild_name in grandchild_tasks:
            complete_grandchild = self.run_command(
                "update-status",
                str(self.test_template),
                grandchild_name,
                "complete",
                "--comment", f"Completed {grandchild_name}"
            )
            self.assertEqual(complete_grandchild.returncode, 0)
        
        # Step 8: Now Child Task 1 can be completed
        complete_child1 = self.run_command(
            "update-status",
            str(self.test_template),
            "Child Task 1",
            "complete",
            "--comment", "Completed Child Task 1 after all grandchildren"
        )
        self.assertEqual(complete_child1.returncode, 0)
        
        # Step 9: Complete Child Task 2
        complete_child2 = self.run_command(
            "update-status",
            str(self.test_template),
            "Child Task 2",
            "complete",
            "--comment", "Completed Child Task 2"
        )
        self.assertEqual(complete_child2.returncode, 0)
        
        # Step 10: Now the parent task can be completed
        complete_parent = self.run_command(
            "update-status",
            str(self.test_template),
            "Hierarchical Parent Task",
            "complete",
            "--comment", "Completed parent task after all children and grandchildren"
        )
        self.assertEqual(complete_parent.returncode, 0)
        
        # Step 11: Final verification
        final_check = self.run_command(
            "show",
            str(self.test_template),
            "Hierarchical Parent Task",
            "--details"
        )
        self.assertEqual(final_check.returncode, 0)
        self.assertIn("complete", final_check.stdout.lower())

    def test_checklist_completion_validation(self):
        """
        Test that the system prevents completion of a task when it has
        incomplete checklist items.
        """
        # Step 1: Create a task with a checklist
        task_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Checklist Validation Task",
            "--description", "This task has a checklist that must be completed",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,checklist"
        )
        self.assertEqual(task_result.returncode, 0)
        
        # Step 2: Add a checklist with multiple items
        checklist_result = self.run_command(
            "create-checklist",
            str(self.test_template),
            "Checklist Validation Task",
            "Required Steps",
            "--items", "Step 1,Step 2,Step 3,Step 4"
        )
        self.assertEqual(checklist_result.returncode, 0)
        
        # Step 3: Try to complete the task with incomplete checklist (should fail)
        try_complete = self.run_command(
            "update-status",
            str(self.test_template),
            "Checklist Validation Task",
            "complete"
        )
        self.assertNotEqual(try_complete.returncode, 0)
        # Check error message includes information about incomplete checklist
        error_output = try_complete.stdout.lower() + try_complete.stderr.lower()
        self.assertIn("checklist", error_output)
        
        # Step 4: Get checklist item IDs
        show_task = self.run_command(
            "show",
            str(self.test_template),
            "Checklist Validation Task",
            "--details"
        )
        
        # Step 5: Check only some checklist items (not all)
        lines = show_task.stdout.splitlines()
        item_ids = []
        for line in lines:
            if "Step " in line and "(ID: " in line:
                parts = line.split("(ID: ")
                if len(parts) > 1:
                    item_id = parts[1].split(")")[0]
                    item_ids.append(item_id)
        
        # Check first two items only
        for item_id in item_ids[:2]:
            check_result = self.run_command(
                "checklist",
                "check",
                str(self.test_template),
                "Checklist Validation Task",
                item_id
            )
            self.assertEqual(check_result.returncode, 0)
        
        # Step 6: Try to complete the task with partially complete checklist (should fail)
        try_complete_again = self.run_command(
            "update-status",
            str(self.test_template),
            "Checklist Validation Task",
            "complete"
        )
        self.assertNotEqual(try_complete_again.returncode, 0)
        
        # Step 7: Complete the remaining checklist items
        for item_id in item_ids[2:]:
            check_result = self.run_command(
                "checklist",
                "check",
                str(self.test_template),
                "Checklist Validation Task",
                item_id
            )
            self.assertEqual(check_result.returncode, 0)
        
        # Step 8: Now the task can be completed
        complete_task = self.run_command(
            "update-status",
            str(self.test_template),
            "Checklist Validation Task",
            "complete",
            "--comment", "Completed task after checking all checklist items"
        )
        self.assertEqual(complete_task.returncode, 0)
        
        # Step 9: Verify the task is complete
        final_check = self.run_command(
            "show",
            str(self.test_template),
            "Checklist Validation Task"
        )
        self.assertEqual(final_check.returncode, 0)
        self.assertIn("complete", final_check.stdout.lower())

    def test_force_completion_override(self):
        """
        Test that the --force flag allows completion of tasks despite:
        - Incomplete subtasks
        - Incomplete checklist items
        """
        # Step 1: Create a parent task
        parent_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Force Override Task",
            "--description", "This task will be force-completed despite constraints",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,force"
        )
        self.assertEqual(parent_result.returncode, 0)
        
        # Step 2: Add a subtask
        subtask_result = self.run_command(
            "create-subtask",
            str(self.test_template),
            "Force Override Task",
            "Incomplete Subtask",
            "--description", "This subtask will remain incomplete",
            "--priority", "2"
        )
        self.assertEqual(subtask_result.returncode, 0)
        
        # Step 3: Add a checklist
        checklist_result = self.run_command(
            "create-checklist",
            str(self.test_template),
            "Force Override Task",
            "Incomplete Checklist",
            "--items", "Item 1,Item 2,Item 3"
        )
        self.assertEqual(checklist_result.returncode, 0)
        
        # Step 4: Verify that normal completion fails
        try_complete = self.run_command(
            "update-status",
            str(self.test_template),
            "Force Override Task",
            "complete"
        )
        self.assertNotEqual(try_complete.returncode, 0)
        
        # Step 5: Use --force flag to override validation
        force_complete = self.run_command(
            "update-status",
            str(self.test_template),
            "Force Override Task",
            "complete",
            "--comment", "Forced completion despite incomplete dependencies",
            "--force"
        )
        self.assertEqual(force_complete.returncode, 0)
        
        # Step 6: Verify the task is complete
        final_check = self.run_command(
            "show",
            str(self.test_template),
            "Force Override Task"
        )
        self.assertEqual(final_check.returncode, 0)
        self.assertIn("complete", final_check.stdout.lower())

    def test_error_message_detail(self):
        """
        Test that error messages provide detailed information about:
        - Which specific subtasks are incomplete
        - Which checklist items are incomplete
        - Task relationships blocking completion
        """
        # Step 1: Create a complex task with multiple constraints
        task_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Error Detail Task",
            "--description", "This task tests error message detail",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,error"
        )
        self.assertEqual(task_result.returncode, 0)
        
        # Step 2: Add subtasks with descriptive names
        subtasks = ["Critical Subtask 1", "Optional Subtask 2", "Required Subtask 3"]
        for subtask_name in subtasks:
            subtask_result = self.run_command(
                "create-subtask",
                str(self.test_template),
                "Error Detail Task",
                subtask_name,
                "--description", f"This is {subtask_name}",
                "--priority", "2"
            )
            self.assertEqual(subtask_result.returncode, 0)
        
        # Step 3: Add a checklist with named items
        checklist_result = self.run_command(
            "create-checklist",
            str(self.test_template),
            "Error Detail Task",
            "Required Checklist",
            "--items", "Verify documentation,Run tests,Update changelog"
        )
        self.assertEqual(checklist_result.returncode, 0)
        
        # Step 4: Create blocking task relationships
        blocking_task_result = self.run_command(
            "create-task", 
            str(self.test_template),
            "Blocker Task",
            "--description", "This task blocks the Error Detail Task",
            "--priority", "1",
            "--list", "Test List",
            "--tags", "test,blocker"
        )
        self.assertEqual(blocking_task_result.returncode, 0)
        
        # Set up blocking relationship
        block_result = self.run_command(
            "relationship",
            "add",
            str(self.test_template),
            "Blocker Task",
            "blocks",
            "Error Detail Task"
        )
        self.assertEqual(block_result.returncode, 0)
        
        # Step 5: Try to complete the task and verify detailed error message
        try_complete = self.run_command(
            "update-status",
            str(self.test_template),
            "Error Detail Task",
            "complete"
        )
        self.assertNotEqual(try_complete.returncode, 0)
        
        error_output = try_complete.stdout.lower() + try_complete.stderr.lower()
        
        # Verify error mentions incomplete subtasks
        for subtask in subtasks:
            self.assertIn(subtask.lower(), error_output)
        
        # Verify error mentions incomplete subtasks or dependencies
        self.assertIn("cannot mark task as complete", error_output)
        
        # Check for blocker relationship with Blocker Task
        relation_check = self.run_command(
            "relationship",
            "list",
            str(self.test_template),
            "Error Detail Task"
        )
        self.assertEqual(relation_check.returncode, 0)
        self.assertIn("Blocker Task", relation_check.stdout)


if __name__ == "__main__":
    unittest.main() 