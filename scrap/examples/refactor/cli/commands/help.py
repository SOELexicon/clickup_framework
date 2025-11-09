"""
Help Documentation Commands Implementation

This module provides command implementations for generating help documentation
for CLI commands and their usage.
"""
from argparse import ArgumentParser, Namespace
import inspect
import textwrap
from typing import Dict, List, Optional, Set, Type

from refactor.cli.commands.base import BaseCommand, CompositeCommand, SimpleCommand
from refactor.core.interfaces.core_manager import CoreManager


class CommandDocumenter:
    """Helper class for documenting commands."""
    
    @staticmethod
    def get_command_tree(command: BaseCommand, prefix: str = "") -> Dict:
        """
        Build a tree representation of a command and its subcommands.
        
        Args:
            command: The command to document
            prefix: Command prefix for nested commands
            
        Returns:
            Dictionary representing the command tree
        """
        command_path = f"{prefix}{command.name}" if prefix else command.name
        result = {
            "name": command.name,
            "path": command_path,
            "description": command.description,
            "class": command.__class__.__name__,
            "module": command.__class__.__module__,
            "subcommands": []
        }
        
        # Add parser arguments if available
        if hasattr(command, "configure_parser"):
            # Create a temporary parser to capture argument definitions
            temp_parser = ArgumentParser(add_help=False)
            command.configure_parser(temp_parser)
            
            # Extract argument information
            result["arguments"] = []
            for action in temp_parser._actions:
                if action.dest != 'help':  # Skip built-in help action
                    arg_info = {
                        "flags": action.option_strings or [action.dest],
                        "dest": action.dest,
                        "help": action.help,
                        "required": action.required,
                        "default": None if action.default == inspect.Parameter.empty else action.default,
                        "type": action.type.__name__ if action.type else None,
                        "choices": action.choices,
                        "nargs": action.nargs
                    }
                    result["arguments"].append(arg_info)
        
        # Add subcommands for composite commands
        if isinstance(command, CompositeCommand):
            for subcmd in command.subcommands.values():
                result["subcommands"].append(
                    CommandDocumenter.get_command_tree(
                        subcmd, 
                        f"{command_path} "
                    )
                )
        
        return result
    
    @staticmethod
    def format_command_help(command_tree: Dict, level: int = 0) -> str:
        """
        Format command help documentation from a command tree.
        
        Args:
            command_tree: The command tree to format
            level: Indentation level
            
        Returns:
            Formatted help text
        """
        indent = "  " * level
        result = []
        
        # Command name and description
        result.append(f"{indent}Command: {command_tree['path']}")
        result.append(f"{indent}Description: {command_tree['description']}")
        result.append("")
        
        # Arguments
        if "arguments" in command_tree and command_tree["arguments"]:
            result.append(f"{indent}Arguments:")
            
            for arg in command_tree["arguments"]:
                # Format flags
                flags_str = ", ".join(arg["flags"])
                
                # Add type and choices if available
                type_info = []
                if arg["type"]:
                    type_info.append(arg["type"])
                
                if arg["choices"]:
                    choices_str = ", ".join([str(c) for c in arg["choices"]])
                    type_info.append(f"choices: {{{choices_str}}}")
                
                if arg["nargs"]:
                    type_info.append(f"nargs: {arg['nargs']}")
                
                if arg["required"]:
                    type_info.append("required")
                
                type_str = " [" + ", ".join(type_info) + "]" if type_info else ""
                
                # Format argument line
                result.append(f"{indent}  {flags_str}{type_str}")
                
                # Format help text with wrapping
                if arg["help"]:
                    wrapped_help = textwrap.wrap(
                        arg["help"], 
                        width=80 - len(indent) - 4
                    )
                    for line in wrapped_help:
                        result.append(f"{indent}    {line}")
                
                # Show default if available and not required
                if not arg["required"] and arg["default"] is not None:
                    result.append(f"{indent}    Default: {arg['default']}")
                
                result.append("")
            
        # Subcommands
        if command_tree["subcommands"]:
            if level == 0:
                result.append(f"{indent}Subcommands:")
                result.append("")
            
            for subcmd in command_tree["subcommands"]:
                result.append(CommandDocumenter.format_command_help(subcmd, level + 1))
        
        return "\n".join(result)
    
    @staticmethod
    def generate_man_page(command_tree: Dict) -> str:
        """
        Generate a man page format documentation for a command.
        
        Args:
            command_tree: The command tree to document
            
        Returns:
            Man page formatted documentation
        """
        result = []
        
        # Man page header
        result.append(f".TH \"{command_tree['path'].upper()}\" 1 \"ClickUp JSON Manager\" \"CUJM Manual\"")
        result.append("")
        
        # Name section
        result.append(".SH NAME")
        result.append(f"{command_tree['path']} \\- {command_tree['description']}")
        result.append("")
        
        # Synopsis section
        result.append(".SH SYNOPSIS")
        synopsis = f".B {command_tree['path']}"
        
        # Add arguments to synopsis
        if "arguments" in command_tree and command_tree["arguments"]:
            for arg in command_tree["arguments"]:
                arg_text = ""
                if arg["flags"][0].startswith("-"):
                    # Optional argument
                    arg_text = " [" + arg["flags"][0]
                    if arg["nargs"] and arg["nargs"] != "?":
                        arg_text += f" {arg['dest'].upper()}"
                    arg_text += "]"
                else:
                    # Positional argument
                    required = arg["required"] or arg["nargs"] in ("+", 1, None)
                    if required:
                        arg_text = f" {arg['dest'].upper()}"
                    else:
                        arg_text = f" [{arg['dest'].upper()}]"
                
                synopsis += arg_text
        
        # Add subcommands indicator if it's a composite command
        if command_tree["subcommands"]:
            synopsis += " <subcommand>"
        
        result.append(synopsis)
        result.append("")
        
        # Description section
        result.append(".SH DESCRIPTION")
        result.append(f"{command_tree['description']}")
        result.append("")
        
        # Options section
        if "arguments" in command_tree and command_tree["arguments"]:
            result.append(".SH OPTIONS")
            
            for arg in command_tree["arguments"]:
                # Option name
                if arg["flags"][0].startswith("-"):
                    flag_list = ", ".join(arg["flags"])
                    result.append(f".TP")
                    result.append(f"\\fB{flag_list}\\fR")
                else:
                    result.append(f".TP")
                    result.append(f"\\fB{arg['dest'].upper()}\\fR")
                
                # Help text
                if arg["help"]:
                    result.append(arg["help"])
                
                # Type information
                type_info = []
                if arg["type"]:
                    type_info.append(f"Type: {arg['type']}")
                
                if arg["choices"]:
                    choices_str = ", ".join([str(c) for c in arg["choices"]])
                    type_info.append(f"Choices: {choices_str}")
                
                if type_info:
                    result.append(".br")
                    result.append(", ".join(type_info))
                
                # Default value
                if not arg["required"] and arg["default"] is not None:
                    result.append(".br")
                    result.append(f"Default: {arg['default']}")
        
        # Subcommands section
        if command_tree["subcommands"]:
            result.append(".SH SUBCOMMANDS")
            
            for subcmd in command_tree["subcommands"]:
                result.append(".TP")
                result.append(f"\\fB{subcmd['name']}\\fR")
                result.append(f"{subcmd['description']}")
        
        # Examples section
        result.append(".SH EXAMPLES")
        result.append(".PP")
        result.append(f".B {command_tree['path']} --help")
        result.append(".RS 4")
        result.append("Show help information for this command.")
        result.append(".RE")
        
        # If command has subcommands, add example for a subcommand
        if command_tree["subcommands"]:
            subcmd = command_tree["subcommands"][0]
            result.append(".PP")
            result.append(f".B {command_tree['path']} {subcmd['name']} --help")
            result.append(".RS 4")
            result.append(f"Show help information for the {subcmd['name']} subcommand.")
            result.append(".RE")
        
        # Add custom examples based on command type
        if "list" in command_tree["path"]:
            result.append(".PP")
            result.append(f".B {command_tree['path']}")
            result.append(".RS 4")
            result.append("List all items.")
            result.append(".RE")
        elif "show" in command_tree["path"]:
            result.append(".PP")
            result.append(f".B {command_tree['path']} example-id")
            result.append(".RS 4")
            result.append("Show details for the item with ID 'example-id'.")
            result.append(".RE")
        
        # See also section
        result.append(".SH SEE ALSO")
        result.append(".PP")
        result.append(".BR cujm (1),")
        
        # Add related commands
        if command_tree["subcommands"]:
            related = [f"{command_tree['path']}\\-{subcmd['name']}(1)" for subcmd in command_tree["subcommands"]]
            result.append(".BR " + ", ".join(related))
        
        return "\n".join(result)


class GenerateHelpCommand(SimpleCommand):
    """Command for generating help documentation."""
    
    def __init__(self, core_manager: CoreManager, root_command: Optional[BaseCommand] = None):
        """
        Initialize with a core manager and root command.
        
        Args:
            core_manager: The core manager to use
            root_command: The root command to document
        """
        super().__init__("generate", "Generate help documentation")
        self._core_manager = core_manager
        self._root_command = root_command
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for generate help command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "--command", 
            help="Specific command to document (omit for all commands)"
        )
        parser.add_argument(
            "--format", 
            choices=["text", "man", "markdown", "html"],
            default="text",
            help="Output format (default: text)"
        )
        parser.add_argument(
            "--output", 
            help="Output file (omit for stdout)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the generate help command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            if not self._root_command:
                print("Error: No root command provided for documentation")
                return 1
            
            # Generate documentation for the specified command or all commands
            if args.command:
                # Find the specified command
                command = self._find_command(self._root_command, args.command.split())
                if not command:
                    print(f"Command not found: {args.command}")
                    return 1
                
                # Generate documentation for the specified command
                command_tree = CommandDocumenter.get_command_tree(command)
            else:
                # Generate documentation for all commands
                command_tree = CommandDocumenter.get_command_tree(self._root_command)
            
            # Format the documentation based on the specified format
            if args.format == "man":
                output = CommandDocumenter.generate_man_page(command_tree)
            elif args.format == "markdown":
                # TODO: Implement markdown formatter
                print("Markdown format not yet implemented")
                return 1
            elif args.format == "html":
                # TODO: Implement HTML formatter
                print("HTML format not yet implemented")
                return 1
            else:  # text
                output = CommandDocumenter.format_command_help(command_tree)
            
            # Output the documentation
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
                print(f"Documentation written to {args.output}")
            else:
                print(output)
            
            return 0
        except Exception as e:
            print(f"Error generating help documentation: {str(e)}")
            return 1
    
    def _find_command(self, root: BaseCommand, path: List[str]) -> Optional[BaseCommand]:
        """
        Find a command by its path.
        
        Args:
            root: The root command to search from
            path: The command path components
            
        Returns:
            The found command or None if not found
        """
        if not path:
            return root
        
        name = path[0]
        remaining = path[1:]
        
        if isinstance(root, CompositeCommand) and name in root.subcommands:
            return self._find_command(root.subcommands[name], remaining)
        
        return None


class ListCommandsCommand(SimpleCommand):
    """Command for listing available commands."""
    
    def __init__(self, core_manager: CoreManager, root_command: Optional[BaseCommand] = None):
        """
        Initialize with a core manager and root command.
        
        Args:
            core_manager: The core manager to use
            root_command: The root command to list
        """
        super().__init__("list", "List available commands")
        self._core_manager = core_manager
        self._root_command = root_command
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the parser for list commands command.
        
        Args:
            parser: The parser to configure
        """
        parser.add_argument(
            "--prefix", 
            help="Filter commands by prefix"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show detailed command information"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the list commands command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success)
        """
        try:
            if not self._root_command:
                print("Error: No root command provided for listing")
                return 1
            
            # Collect all commands
            all_commands = []
            self._collect_commands(
                self._root_command, 
                "", 
                all_commands
            )
            
            # Filter by prefix if specified
            if args.prefix:
                all_commands = [cmd for cmd in all_commands if cmd["path"].startswith(args.prefix)]
            
            # Display commands
            if not all_commands:
                if args.prefix:
                    print(f"No commands found with prefix: {args.prefix}")
                else:
                    print("No commands found")
                return 0
            
            print(f"Available commands ({len(all_commands)}):\n")
            
            for cmd in all_commands:
                # Format command information
                if args.verbose:
                    print(f"Command: {cmd['path']}")
                    print(f"Description: {cmd['description']}")
                    print(f"Module: {cmd['module']}")
                    print(f"Class: {cmd['class']}")
                    print()
                else:
                    print(f"{cmd['path']:<30} {cmd['description']}")
            
            return 0
        except Exception as e:
            print(f"Error listing commands: {str(e)}")
            return 1
    
    def _collect_commands(self, command: BaseCommand, prefix: str, result: List[Dict]) -> None:
        """
        Recursively collect commands.
        
        Args:
            command: The command to collect
            prefix: Command prefix for nested commands
            result: List to collect results
        """
        command_path = f"{prefix}{command.name}" if prefix else command.name
        
        # Add this command
        result.append({
            "name": command.name,
            "path": command_path,
            "description": command.description,
            "class": command.__class__.__name__,
            "module": command.__class__.__module__
        })
        
        # Add subcommands for composite commands
        if isinstance(command, CompositeCommand):
            for subcmd in command.subcommands.values():
                self._collect_commands(
                    subcmd, 
                    f"{command_path} ",
                    result
                )


class HelpCommand(CompositeCommand):
    """
    Help command group.
    
    This command group provides subcommands for help documentation.
    """
    
    def __init__(self, core_manager: CoreManager, root_command: Optional[BaseCommand] = None):
        """
        Initialize with a core manager and root command.
        
        Args:
            core_manager: The core manager to use
            root_command: The root command to document
        """
        super().__init__("help", "Help documentation")
        
        # Add subcommands
        self.add_subcommand(GenerateHelpCommand(core_manager, root_command))
        self.add_subcommand(ListCommandsCommand(core_manager, root_command)) 