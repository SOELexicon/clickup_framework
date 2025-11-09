"""
Task: tsk_bf28d342 - Update CLI Module Comments
Document: refactor/cli/commands/base.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (current)
    - tsk_c31a2879 - Command Pattern Implementation (related)
    - tsk_d45e789b - CLI Command Interface Design (related)

Used By:
    - CLI Framework: Core foundation for all CLI commands
    - Command Implementations: Inherits these base classes for specific functionality
    - Command Registry: For tracking available commands
    - Main CLI Interface: For command execution flow

Purpose:
    Provides the foundation classes for implementing CLI commands
    using the Command Pattern design. Defines the core interfaces
    and abstract classes that all command implementations must follow.

Requirements:
    - Must follow the Command Pattern design principles
    - Must provide a clear interface for all command implementations
    - Must support both simple and composite command structures
    - CRITICAL: Must maintain backward compatibility with existing commands
    - CRITICAL: Must handle errors consistently across all command implementations

Parameters:
    N/A - This is a command module file

Returns:
    N/A - This is a command module file

Changes:
    - v1: Initial implementation with basic command pattern
    - v2: Added composite command support for command hierarchies
    - v3: Added middleware command for pre/post execution hooks
    - v4: Enhanced documentation and improved error handling

Lessons Learned:
    - Command pattern provides clean separation of CLI interface from business logic
    - Composite pattern enables complex command hierarchies with minimal code duplication
    - Consistent error handling is crucial for user experience in CLI applications
    - Strong typing with type hints improves API clarity and IDE support
"""
import abc
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional, Any, Union
from refactor.cli.error_handling import (
    ErrorCode, CLIError, handle_cli_error, 
    validate_args, validate_file_exists, validate_json_file
)
import os
import logging
from refactor.core.interfaces.core_manager import CoreManager
from refactor.utils.template_finder import get_template_path, get_required_template_path

logger = logging.getLogger(__name__)


class CommandContext:
    """
    Command execution context for sharing data between commands.
    
    This class provides a shared context for command execution, including
    services, configuration, and other execution-specific information.
    It serves as a lightweight dependency injection mechanism and state
    container for passing data between command execution phases.
    
    The context can store:
    - Core manager instance for accessing services
    - Configuration settings
    - Custom key-value pairs for command-specific data
    
    This facilitates middleware implementations and command hooks that
    need to share data or state during the command execution lifecycle.
    """
    
    def __init__(self, core_manager=None, config=None):
        """
        Initialize a new command execution context.
        
        Creates a context with optional core manager and configuration.
        The context starts with an empty values dictionary that can be
        populated during command execution.
        
        Args:
            core_manager: The core manager instance for accessing services
            config: The application configuration dictionary
        """
        self.core_manager = core_manager
        self.config = config or {}
        self.values = {}  # Additional context values
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the context by key.
        
        Returns the value associated with the key if it exists,
        otherwise returns the specified default value.
        
        Args:
            key: The key of the value to retrieve
            default: The default value to return if key is not found
        
        Returns:
            The value associated with the key or the default value
        """
        return self.values.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Store a value in the context with the specified key.
        
        If the key already exists, its value will be overwritten.
        This method is used to share data between command execution
        phases or between middleware components.
        
        Args:
            key: The key to associate with the value
            value: The value to store in the context
        """
        self.values[key] = value
    
    def has_value(self, key: str) -> bool:
        """
        Check if a key exists in the context.
        
        This method checks if a value has been set for the specified key,
        without retrieving the actual value.
        
        Args:
            key: The key to check for existence
        
        Returns:
            True if the key exists in the context, False otherwise
        """
        return key in self.values


class BaseCommand(abc.ABC):
    """
    Abstract base class for all CLI commands using the Command pattern.
    
    This abstract class defines the interface for all commands in the
    command pattern implementation. Every command in the system must
    inherit from this class and implement its abstract methods.
    
    The Command pattern encapsulates command execution logic into separate
    objects, allowing for:
    - Unified interface for all commands
    - Easy extension with new commands
    - Support for command composition
    - Separation of command parsing from execution
    - Standardized error handling
    
    Each command has a name and description, which are used for:
    - Command registration and discovery
    - Help text generation
    - Command documentation
    
    Command execution follows a consistent lifecycle:
    1. Command object is instantiated
    2. Command registers arguments via configure_parser
    3. Arguments are parsed
    4. Command's execute method is called with parsed arguments
    5. Return code indicates success (0) or failure (non-zero)
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a command.
        
        Args:
            name: Command name
            description: Command description
        """
        self.name = name
        self.description = description
    
    def add_to_parser(self, subparsers) -> None:
        """
        Add this command to a subparser group.
        
        Args:
            subparsers: The subparsers group to add to
        """
        parser = subparsers.add_parser(
            self.name,
            help=self.description,
            description=self.description
        )
        
        # Configure the parser with command-specific arguments
        self.configure_parser(parser)
        
        # Set the command as the default func
        parser.set_defaults(func=self)
    
    @abc.abstractmethod
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: The parser to configure
        """
        pass
    
    @abc.abstractmethod
    def execute(self, args: Namespace) -> Union[str, int]:
        """
        Execute the command with the given arguments.
        
        Args:
            args: The parsed arguments
        
        Returns:
            String error code or integer exit code (empty string or 0 for success)
        """
        pass
    
    def __call__(self, args: Namespace) -> int:
        """
        Make the command callable so it can be used with argparse set_defaults.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        result = self.execute(args)
        if isinstance(result, str):
            return 1 if result else 0  # Non-empty string indicates error
        return result  # Integer exit code


class CompositeCommand(BaseCommand):
    """
    A command that contains and manages a collection of subcommands.
    
    This class implements the Composite pattern to allow commands to contain
    other commands, forming a command hierarchy. This enables complex command
    structures like Git's subcommand system (git commit, git push, etc.).
    
    The Composite pattern allows:
    - Nested command hierarchies with arbitrary depth
    - Consistent interface for both leaf and composite commands
    - Organized command grouping by functionality
    - Hierarchical help system
    
    Examples of composite commands include:
    - Main application command containing all top-level commands
    - Feature-specific command groups (e.g., task, checklist, relationship)
    - Complex operations with multiple sub-operations
    
    Composite commands delegate execution to their subcommands rather than
    implementing execution logic themselves. They primarily manage the
    command hierarchy and routing.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a composite command.
        
        Args:
            name: Command name
            description: Command description
        """
        super().__init__(name, description)
        self.subcommands: Dict[str, BaseCommand] = {}
    
    def add_subcommand(self, command: BaseCommand) -> None:
        """
        Add a subcommand to this composite command.
        
        Args:
            command: The command to add
        """
        self.subcommands[command.name] = command
    
    def remove_subcommand(self, name: str) -> None:
        """
        Remove a subcommand by name.
        
        Args:
            name: The name of the command to remove
        """
        if name in self.subcommands:
            del self.subcommands[name]
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: The parser to configure
        """
        # Create subparsers for this command
        subparsers = parser.add_subparsers(
            title="subcommands",
            dest="subcommand",
            help="Available subcommands",
            required=True
        )
        
        # Add all subcommands to the parser
        for command in self.subcommands.values():
            command.add_to_parser(subparsers)
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the command with the given arguments.
        
        For composite commands, this delegates to the appropriate subcommand.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success)
        """
        # Subcommand execution is handled by the argparse mechanism,
        # which will call the subcommand directly.
        # This method should not be called on a composite command.
        return 1


class SimpleCommand(BaseCommand):
    """
    Concrete implementation of a command with basic functionality.
    
    This provides a basic implementation of a command that can be 
    executed with the given arguments. Unlike CompositeCommand,
    SimpleCommand represents a "leaf" in the command hierarchy
    that performs a specific operation rather than containing
    other commands.
    
    Features of SimpleCommand:
    - Default error handling with the @handle_cli_error decorator
    - Optional CoreManager integration for accessing services
    - Template method pattern for execution flow
    - Standard argument parsing setup
    
    Most concrete commands in the application should inherit from
    SimpleCommand rather than directly from BaseCommand, as it
    provides useful default behavior and error handling.
    
    Example uses:
    - Task creation/viewing commands
    - Search commands
    - Configuration commands
    - Import/export operations
    """
    
    def __init__(self, name: str, description: str, core_manager: Optional[CoreManager] = None):
        """
        Initialize a new simple command.
        
        Args:
            name: The name of the command
            description: The description of the command
            core_manager: Optional core manager instance
        """
        super().__init__(name, description)
        self._core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        This method should be overridden by concrete command classes
        to add their specific arguments.
        
        Args:
            parser: The parser to configure
        """
        pass
    
    @handle_cli_error
    def execute(self, args: Namespace) -> int:
        """
        Execute the command with the given arguments.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success)
        """
        # Validate required arguments if specified
        if hasattr(self, 'required_args'):
            valid, error = validate_args(args, self.required_args)
            if not valid:
                raise CLIError(error, ErrorCode.INVALID_ARGUMENT)
        
        # Validate template file if it's a common requirement
        if hasattr(args, 'template') and args.template:
            valid, error = validate_json_file(args.template)
            if not valid:
                if "not exist" in error:
                    raise CLIError(error, ErrorCode.FILE_NOT_FOUND)
                else:
                    raise CLIError(error, ErrorCode.INVALID_JSON)
        
        # Execute the command implementation
        return self._execute_command(args)
    
    def _execute_command(self, args: Namespace) -> int:
        """
        Execute the command implementation.
        
        This method should be overridden by concrete command classes
        to implement their specific behavior.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success)
        """
        print(f"Command '{self.name}' not implemented")
        return 0


class MiddlewareCommand(SimpleCommand):
    """
    Command implementation with pre/post execution hook support.
    
    This extends SimpleCommand to add middleware functionality that executes
    before and after the main command logic. This enables cross-cutting
    concerns like logging, validation, authorization, and timing to be
    added to commands without modifying their core implementation.
    
    Features:
    - Pre-execution hooks run before command execution
    - Post-execution hooks run after command execution
    - Shared execution context for data passing between hooks
    - Maintains execution order of hooks (FIFO)
    - Proper error propagation from hooks
    
    Examples of middleware usage:
    - Authentication/authorization checks before execution
    - Logging command execution start/end
    - Performance monitoring and metrics collection
    - Automatic transaction management
    - Input validation beyond basic argparse validation
    
    To use middleware functionality, create a subclass of MiddlewareCommand
    and register pre/post execution hooks with add_pre_execute_hook and
    add_post_execute_hook.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a middleware command.
        
        Args:
            name: Command name
            description: Command description
        """
        super().__init__(name, description)
        self.pre_execute_hooks: List[callable] = []
        self.post_execute_hooks: List[callable] = []
    
    def add_pre_execute_hook(self, hook: callable) -> None:
        """
        Add a hook to run before execution.
        
        Args:
            hook: The hook function to run before execution
                 Should accept (args, context) and return modified args
        """
        self.pre_execute_hooks.append(hook)
    
    def add_post_execute_hook(self, hook: callable) -> None:
        """
        Add a hook to run after execution.
        
        Args:
            hook: The hook function to run after execution
                 Should accept (result, args, context) and return modified result
        """
        self.post_execute_hooks.append(hook)
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the command with the given arguments.
        
        This implementation runs the command through the middleware pipeline.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success)
        """
        context = CommandContext()
        
        # Run pre-execute hooks
        for hook in self.pre_execute_hooks:
            args = hook(args, context)
        
        # Execute the actual command
        try:
            result = self._execute_command(args, context)
        except Exception as e:
            # Log the exception
            print(f"Error executing command: {str(e)}")
            return 1
        
        # Run post-execute hooks
        for hook in self.post_execute_hooks:
            result = hook(result, args, context)
        
        return result
    
    @abc.abstractmethod
    def _execute_command(self, args: Namespace, context: CommandContext) -> int:
        """
        Execute the command implementation.
        
        Must be implemented by concrete middleware command classes.
        
        Args:
            args: The parsed arguments
            context: The execution context
        
        Returns:
            Exit code (0 for success)
        """
        pass


class HelpCommand(SimpleCommand):
    """
    Specialized command for providing help and usage information.
    
    This command handles displaying help and usage information for all commands in the 
    application. It can show both general help (listing all commands)
    and specific help for individual commands.
    
    Features:
    - Dynamically generated help based on registered commands
    - Support for command-specific help
    - Enhanced formatting beyond standard argparse help
    - Consistent help style across all commands
    
    Help text includes:
    - Command name and description
    - Available arguments and their descriptions
    - Examples of command usage
    - Related commands
    
    The HelpCommand is typically registered as a top-level command and
    as the default handler when no command is specified or when the
    --help flag is provided.
    """
    
    def __init__(self, parser: ArgumentParser, commands: Dict[str, BaseCommand] = None):
        """
        Initialize a help command.
        
        Args:
            parser: The root argument parser
            commands: Dictionary of available commands
        """
        super().__init__("help", "Display help information")
        self.parser = parser
        self.commands = commands or {}
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for the help command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "command",
            nargs="?",
            help="Command to display help for (omit to show general help)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the help command.
        
        Args:
            args: The parsed arguments
        
        Returns:
            Exit code (0 for success)
        """
        if args.command:
            # Show help for specific command
            if args.command in self.commands:
                # Create a new parser for the command to display its help
                command_parser = ArgumentParser(prog=f"{self.parser.prog} {args.command}")
                self.commands[args.command].configure_parser(command_parser)
                command_parser.print_help()
            else:
                print(f"Unknown command: {args.command}")
                return 1
        else:
            # Show general help
            self.parser.print_help()
        
        return 0 


class TemplateCommand(SimpleCommand):
    """
    Base class for commands that work with template files.
    
    This class provides common functionality for working with template files, 
    including support for optional template arguments with automatic default detection.
    """
    
    def __init__(self, name: str, description: str, core_manager: Optional[CoreManager] = None):
        """
        Initialize the template command.
        
        Args:
            name: Command name
            description: Command description
            core_manager: Core manager instance
        """
        super().__init__(name, description, core_manager)
    
    def add_template_argument(self, parser: ArgumentParser, required: bool = False) -> None:
        """
        Add a template argument to the parser, making it optional or required.
        
        Args:
            parser: Argument parser to configure
            required: Whether the template argument is required (default: False)
        """
        help_text = 'Path to the JSON template file'
        if not required:
            help_text += ' (defaults to .project/clickup_tasks.json if it exists)'
            parser.add_argument('template', nargs='?', help=help_text)
        else:
            parser.add_argument('template', help=help_text)
    
    def get_template_path(self, args: Namespace) -> str:
        """
        Get the template path from the arguments or the default location.
        
        This method checks if a template path was provided and, if not,
        looks for the default template in the .project directory.
        
        Args:
            args: Command line arguments with optional template attribute
            
        Returns:
            Path to the template file to use
            
        Raises:
            ValueError: If no template is available (neither specified nor defaulted)
        """
        return get_required_template_path(getattr(args, 'template', None))
    
    def initialize_core_manager(self, args: Namespace) -> None:
        """
        Initialize the core manager with the template file from args.
        
        This method resolves the template path (using defaults if needed)
        and initializes the core manager with it.
        
        Args:
            args: Command line arguments with optional template attribute
            
        Raises:
            ValueError: If no template is available
            CLIError: If there is an error initializing the core manager
        """
        template_path = self.get_template_path(args)
        logger.info(f"Using template file: {template_path}")
        self._core_manager.initialize(template_path) 