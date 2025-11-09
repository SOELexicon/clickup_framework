"""
Task management commands for CLI.
"""

from typing import Optional
import argparse

from refactor.cli.command import Command, CommandContext
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode,
    get_command_error_code,
    get_service_error_code,
    get_validation_error_code
)
from refactor.core.repositories import JsonTaskRepository
from refactor.core.services import TaskService
from refactor.core.validation import TaskValidator


class UpdateTaskCommand(Command):
    """Command for updating a task."""
    
    @property
    def name(self) -> str:
        """Get the name of the command."""
        return "update-task"
    
    @property
    def description(self) -> str:
        """Get the description of the command."""
        return "Update a task in a JSON file"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Configure the argument parser for this command."""
        parser.add_argument("file_path", help="Path to the JSON file")
        parser.add_argument("task_id", help="ID of the task to update")
        parser.add_argument("--name", help="New name for the task")
        parser.add_argument("--description", help="New description for the task")
        parser.add_argument("--status", help="New status for the task")
        parser.add_argument("--priority", type=int, help="New priority for the task")
        parser.add_argument("--assignee", help="New assignee for the task")
        parser.add_argument("--force", action="store_true", help="Force update even with incomplete subtasks")
    
    @handle_cli_error
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command with the given arguments."""
        context = CommandContext(self, args)
        
        # Validate arguments
        if not any([args.name, args.description, args.status, args.priority, args.assignee]):
            error_code = get_command_error_code("ARGS", "001")
            context.abort(CLIError(
                "At least one update field must be specified",
                error_code,
                {"file_path": args.file_path, "task_id": args.task_id}
            ))
            return 1
        
        # Create repository and service
        try:
            repository = JsonTaskRepository(args.file_path)
            validator = TaskValidator(repository)
            service = TaskService(repository, validator)
            
            # Update the task
            updates = {}
            if args.name:
                updates["name"] = args.name
            if args.description:
                updates["description"] = args.description
            if args.status:
                updates["status"] = args.status
            if args.priority is not None:
                updates["priority"] = args.priority
            if args.assignee:
                updates["assignee"] = args.assignee
            
            # Force flag
            force = args.force
            
            # Perform the update
            updated_task = service.update_task(args.task_id, updates, force=force)
            
            # Print success message
            print(f"Task {updated_task.id} updated successfully")
            return 0
            
        except Exception as e:
            # If it's already a CLI error, just propagate it
            if isinstance(e, CLIError):
                raise
                
            # Map domain-specific errors to appropriate error codes
            if "Task not found" in str(e):
                error_code = get_service_error_code("TASK", "001")
                context_data = {"task_id": args.task_id, "file_path": args.file_path}
                raise CLIError(str(e), error_code, context_data)
                
            if "Invalid status" in str(e):
                error_code = get_validation_error_code("FIELD", "001")
                context_data = {"task_id": args.task_id, "invalid_field": "status"}
                raise CLIError(str(e), error_code, context_data)
                
            if "cannot be completed" in str(e):
                error_code = get_service_error_code("TASK", "003")
                context_data = {"task_id": args.task_id, "reason": "incomplete_subtasks"}
                raise CLIError(str(e), error_code, context_data)
                
            # Generic error with the command error code
            error_code = get_command_error_code("EXEC", "001")
            context_data = {"task_id": args.task_id, "file_path": args.file_path}
            raise CLIError(f"Failed to update task: {str(e)}", error_code, context_data) 