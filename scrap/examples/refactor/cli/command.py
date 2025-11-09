#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command handling infrastructure for CLI applications.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, Type
import argparse
import sys
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode,
    error_code_registry,
    get_command_error_code,
    ErrorContext,
    ErrorContextBuilder
)


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser that formats error messages consistently."""
    
    def error(self, message):
        """Override error handling to format messages consistently."""
        error_code = get_command_error_code("ARGS", "001")
        print(f"Error [{error_code}]: {message}", file=sys.stderr)
        self.print_help(sys.stderr)
        sys.exit(1)
        
    def exit(self, status=0, message=None):
        """Override exit to avoid exiting during help."""
        if status == 0 and message is None:  # Help command
            return
        if message:
            print(message, file=sys.stderr)
        sys.exit(status)


class Command(ABC):
    """
    Abstract base class for CLI commands.
    
    All commands must implement this interface to be registered in the system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the command.
        
        This is used to identify the command in the CLI.
        
        Returns:
            Command name
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the command.
        
        This is used in help text and documentation.
        
        Returns:
            Command description
        """
        pass
    
    @abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        pass
    
    @abstractmethod
    def execute(self, args: argparse.Namespace) -> Union[int, str]:
        """
        Execute the command with the given arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure) or error code string
        """
        pass


class CommandContext:
    """
    Command execution context with structured error handling.
    
    This class provides a container for data shared during command execution,
    including the command itself, arguments, execution state, and error context.
    """
    
    def __init__(self, command=None, args=None):
        """
        Initialize the command context.
        
        Args:
            command: The command to execute
            args: The parsed arguments
        """
        self.command = command
        self.args = args
        self.result = None
        self.error = None
        self.error_context = None
        self.aborted = False
        self.values = {}  # Additional context values for middleware use
        self.metadata = self.values  # Alias for middleware compatibility
    
    def abort(self, error=None, context_data: Optional[dict] = None) -> None:
        """
        Abort the command execution with structured error handling.
        
        Args:
            error: Error information (Exception or string)
            context_data: Optional dictionary of context data
        """
        self.aborted = True
        self.error = error
        
        if isinstance(error, CLIError):
            self.error_context = error.error_context
            # Format and print the error message
            print(f"Error [{error.code}]: {error.message}")
        elif error:
            # Create error context for non-CLIError exceptions
            error_code = get_command_error_code("ABORT", "001")  # CLI-COMMAND-ABORT-001
            error_message = str(error)
            print(f"Error [{error_code}]: {error_message}")
            self.error_context = ErrorContextBuilder(error_message) \
                .with_code(str(error_code)) \
                .with_data("command", self.command.name if self.command else "unknown") \
                .with_data_dict(context_data or {}) \
                .build()
    
    def get_value(self, key: str, default=None):
        """
        Get a value from the context.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            The value or default if not found
        """
        return self.values.get(key, default)
    
    def set_value(self, key: str, value) -> None:
        """
        Set a value in the context.
        
        Args:
            key: Key to set
            value: Value to store
        """
        self.values[key] = value
    
    def has_error(self) -> bool:
        """
        Check if an error occurred during execution.
        
        Returns:
            True if an error occurred, False otherwise
        """
        return self.error is not None
    
    def get_error_code(self) -> str:
        """
        Get the structured error code for the context.
        
        Returns:
            Error code string (empty string for success, structured error code for failure)
        """
        if not self.error:
            return ""  # Success
            
        if isinstance(self.error, CLIError):
            return str(self.error.code)
            
        if self.error_context:
            return str(self.error_context.error_code)
            
        # Default error code for unknown errors
        return str(get_command_error_code("GENERAL", "000"))  # CLI-COMMAND-GENERAL-000


class Middleware(ABC):
    """
    Abstract base class for command middleware.
    
    Middleware components can intercept command execution before and after
    the command is executed, enabling cross-cutting concerns like logging,
    error handling, and authorization.
    """
    
    @abstractmethod
    def before_execution(self, context: CommandContext) -> None:
        """
        Execute before the command is executed.
        
        Args:
            context: Command execution context
        """
        pass
    
    @abstractmethod
    def after_execution(self, context: CommandContext) -> None:
        """
        Execute after the command is executed.
        
        Args:
            context: Command execution context
        """
        pass


class MiddlewarePipeline:
    """
    Pipeline for executing middleware components.
    
    This class manages the execution of middleware components before and after
    command execution, ensuring they are called in the correct order.
    """
    
    def __init__(self):
        """Initialize the middleware pipeline."""
        self.middleware: List[Middleware] = []
    
    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add a middleware component to the pipeline.
        
        Args:
            middleware: Middleware component to add
        """
        self.middleware.append(middleware)
    
    def execute(self, context: CommandContext) -> Union[int, str]:
        """
        Execute the middleware pipeline.
        
        Args:
            context: Command execution context
            
        Returns:
            Exit code (0 for success, non-zero for failure) or error code string
        """
        try:
            # Execute before middleware
            for m in self.middleware:
                m.before_execution(context)
                if context.aborted:
                    break
            
            # Execute command if not aborted
            if not context.aborted:
                result = context.command.execute(context.args)
                context.result = result
            
            # Execute after middleware
            for m in reversed(self.middleware):
                m.after_execution(context)
            
            # Return result
            if context.aborted:
                return 1  # Error exit code
            if isinstance(context.result, str):
                if context.result:  # Non-empty string indicates error
                    print(f"Error [{context.result}]: Command failed", file=sys.stderr)
                    return 1  # Error exit code
                else:  # Empty string indicates success
                    return 0  # Success exit code
            if isinstance(context.result, int):  # Integer indicates explicit exit code
                return context.result
            return 0  # Success exit code for any other type
            
        except Exception as e:
            # Map the exception to an appropriate error code
            error_code = get_command_error_code("GENERAL", "000")
            print(f"Error [{error_code}]: {str(e)}", file=sys.stderr)
            return 1  # Error exit code


class CommandRegistry:
    """
    Registry for CLI commands.
    
    This class manages the registration and discovery of commands.
    """
    
    def __init__(self):
        """Initialize the command registry."""
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register_command(self, command: Command, category: Optional[str] = None) -> None:
        """
        Register a command.
        
        Args:
            command: Command to register
            category: Optional category for the command
        
        Raises:
            ValueError: If a command with the same name is already registered
        """
        if command.name in self.commands:
            raise ValueError(f"Command '{command.name}' is already registered")
        
        self.commands[command.name] = command
        
        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(command.name)
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        Get a command by name.
        
        Args:
            name: Name of the command
            
        Returns:
            Command if found, None otherwise
        """
        return self.commands.get(name)
    
    def get_all_commands(self) -> Dict[str, Command]:
        """
        Get all registered commands.
        
        Returns:
            Dictionary of command names to command objects
        """
        return self.commands.copy()
    
    def get_categories(self) -> Dict[str, List[str]]:
        """
        Get all categories and their commands.
        
        Returns:
            Dictionary of category names to lists of command names
        """
        return self.categories.copy()
    
    def get_commands_in_category(self, category: str) -> List[Command]:
        """
        Get all commands in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of command objects in the category
        """
        command_names = self.categories.get(category, [])
        return [self.commands[name] for name in command_names]


class CLIApplication:
    """
    Main application class for the CLI.
    
    This class manages command registration and execution, providing
    a unified interface for running commands with middleware support.
    """
    
    def __init__(self):
        """Initialize the CLI application."""
        self.commands = {}
        self.middleware_pipeline = MiddlewarePipeline()
        self.parser = CustomArgumentParser(description="ClickUp JSON Manager CLI")
        self.subparsers = self.parser.add_subparsers(dest='command')
    
    def register_command(self, command: Command) -> None:
        """
        Register a command with the application.
        
        Args:
            command: Command instance to register
        """
        if command.name in self.commands:
            raise ValueError(f"Command '{command.name}' already registered")
            
        # Create subparser for command
        subparser = self.subparsers.add_parser(command.name, help=command.description)
        command.configure_parser(subparser)
        self.commands[command.name] = command
    
    def register_middleware(self, middleware: Middleware) -> None:
        """
        Register middleware with the application.
        
        Args:
            middleware: Middleware instance to register
        """
        self.middleware_pipeline.add_middleware(middleware)
    
    def execute(self, args=None) -> int:
        """
        Execute a command with the given arguments.
        
        Args:
            args: Command-line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Parse arguments
            # If args is None or empty list, show help and indicate missing command
            if args is None or len(args) == 0:
                print("No command specified")
                self.parser.print_help()
                return 1
                
            parsed_args = self.parser.parse_args(args)
            
            # Special case for --help
            if hasattr(parsed_args, 'help') and parsed_args.help:
                return 0
                
            # Handle no command specified
            if not parsed_args.command:
                print("No command specified")
                self.parser.print_help()
                return 1
                
            # Get command
            command = self.commands.get(parsed_args.command)
            if not command:
                print(f"Unknown command '{parsed_args.command}'")
                self.parser.print_help()
                return 1
                
            # Create context
            context = CommandContext(command, parsed_args)
            
            # Execute with middleware
            result = self.middleware_pipeline.execute(context)
            
            # Handle result
            if isinstance(result, str) and result:
                # Non-empty string indicates error
                print(f"Error: {result}")
                return 1
            elif isinstance(result, int):
                return result
            else:
                return 0
                
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1


class CommandLineInterface:
    """
    Command-line interface for the application.
    
    This class provides the main entry point for the CLI application,
    handling argument parsing and command execution.
    """
    
    def __init__(self, program_name: str, description: str, version: str, registry: CommandRegistry = None):
        """
        Initialize the CLI.
        
        Args:
            program_name: Name of the program
            description: Program description
            version: Program version
            registry: Command registry (creates a new one if None)
        """
        self.program_name = program_name
        self.description = description
        self.version = version
        self.registry = registry or CommandRegistry()
        self.pipeline = MiddlewarePipeline()
    
    def register_command(self, command: Command, category: Optional[str] = None) -> None:
        """
        Register a command.
        
        Args:
            command: Command to register
            category: Optional category for the command
        """
        self.registry.register_command(command, category)
    
    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add middleware to the execution pipeline.
        
        Args:
            middleware: Middleware to add
        """
        self.pipeline.add_middleware(middleware)
    
    @handle_cli_error
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI application.
        
        Args:
            args: Optional command-line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Create the main argument parser
        parser = argparse.ArgumentParser(
            prog=self.program_name,
            description=self.description
        )
        
        # Configure parser to handle errors better
        class ArgumentParser(argparse.ArgumentParser):
            def error(self, message):
                if "invalid choice" in message:
                    print(f"Error: Unknown command '{message.split(':')[1].strip().split()[0]}'")
                elif "unrecognized arguments" in message:
                    print(f"Error: {message}")
                else:
                    print(f"Error: {message}")
                self.print_help()
                raise argparse.ArgumentError(None, message)
        
        parser = ArgumentParser(
            prog=self.program_name,
            description=self.description
        )
        parser.add_argument('--version', action='version', version=f'%(prog)s {self.version}')
        
        # Create subparsers for commands
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Configure subparsers for each command
        for command in self.registry.get_all_commands().values():
            subparser = subparsers.add_parser(command.name, help=command.description)
            command.configure_parser(subparser)
        
        try:
            # Parse arguments
            parsed_args = parser.parse_args(args)
            
            # If no command specified, print help and exit
            if not parsed_args.command:
                parser.print_help()
                print("\nError: No command specified")
                return 1
            
            # Get the command
            command = self.registry.get_command(parsed_args.command)
            if not command:
                print(f"\nError: Unknown command '{parsed_args.command}'")
                return 1
            
            # Create context and execute the command through the middleware pipeline
            context = CommandContext(command, parsed_args)
            result = self.pipeline.execute(context)
            
            # Return the result directly
            return result
            
        except argparse.ArgumentError as e:
            print(f"Error: {str(e)}")
            return 1
        except argparse.ArgumentTypeError as e:
            print(f"Error: {str(e)}")
            return 1
        except SystemExit as e:
            # Handle argparse's exit (e.g. from --help)
            return e.code
        except Exception as e:
            # Unexpected exceptions should be treated as general errors
            if not isinstance(e, CLIError):
                error_code = get_command_error_code("GENERAL", "000")
                print(f"Error [{error_code}]: {str(e)}")
                return 1
            raise 