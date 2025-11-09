"""
Command Registry System

This module implements a comprehensive command registry system that manages
command registration, discovery, and metadata handling.
"""
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
import json
import os
from pathlib import Path
from .command import Command


@dataclass
class CommandMetadata:
    """
    Metadata for a registered command.
    
    This class holds additional information about commands that is used
    for documentation, help generation, and plugin management.
    """
    name: str
    description: str
    category: str
    plugin_id: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    examples: List[str] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        self.dependencies = self.dependencies or []
        self.tags = self.tags or []
        self.examples = self.examples or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'plugin_id': self.plugin_id,
            'version': self.version,
            'author': self.author,
            'dependencies': self.dependencies,
            'tags': self.tags,
            'examples': self.examples
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandMetadata':
        """Create metadata instance from dictionary."""
        return cls(**data)


class CommandRegistryError(Exception):
    """Base exception for command registry errors."""
    pass


class DuplicateCommandError(CommandRegistryError):
    """Raised when attempting to register a command with a name that already exists."""
    pass


class DependencyError(CommandRegistryError):
    """Raised when command dependencies cannot be satisfied."""
    pass


class CommandRegistry:
    """
    Enhanced command registry that manages command registration, discovery,
    and metadata handling.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the command registry.
        
        Args:
            storage_path: Optional path for persistent storage of command metadata
        """
        self._commands: Dict[str, Command] = {}
        self._metadata: Dict[str, CommandMetadata] = {}
        self._categories: Dict[str, List[str]] = {}
        self._storage_path = storage_path
        
        if storage_path:
            self._load_metadata()
    
    def register_command(
        self,
        command: Command,
        category: str,
        plugin_id: Optional[str] = None,
        version: Optional[str] = None,
        author: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """
        Register a command with metadata.
        
        Args:
            command: Command instance to register
            category: Category for organizing commands
            plugin_id: Optional ID of the plugin providing this command
            version: Optional version of the command
            author: Optional author information
            dependencies: Optional list of command dependencies
            tags: Optional tags for categorization
            examples: Optional usage examples
            
        Raises:
            DuplicateCommandError: If command name already exists
            DependencyError: If dependencies cannot be satisfied
        """
        if command.name in self._commands:
            raise DuplicateCommandError(f"Command '{command.name}' already registered")
        
        # Verify dependencies if specified
        if dependencies:
            missing = [dep for dep in dependencies if dep not in self._commands]
            if missing:
                raise DependencyError(f"Missing dependencies: {', '.join(missing)}")
        
        # Create and store metadata
        metadata = CommandMetadata(
            name=command.name,
            description=command.description,
            category=category,
            plugin_id=plugin_id,
            version=version,
            author=author,
            dependencies=dependencies or [],
            tags=tags or [],
            examples=examples or []
        )
        
        # Register command and metadata
        self._commands[command.name] = command
        self._metadata[command.name] = metadata
        
        # Update category index
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(command.name)
        
        # Persist metadata if storage is configured
        if self._storage_path:
            self._save_metadata()
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        Get a command by name.
        
        Args:
            name: Name of the command
            
        Returns:
            Command instance or None if not found
        """
        return self._commands.get(name)
    
    def get_metadata(self, name: str) -> Optional[CommandMetadata]:
        """
        Get metadata for a command.
        
        Args:
            name: Name of the command
            
        Returns:
            CommandMetadata instance or None if not found
        """
        return self._metadata.get(name)
    
    def get_commands_by_category(self, category: str) -> List[Command]:
        """
        Get all commands in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of commands in the category
        """
        command_names = self._categories.get(category, [])
        return [self._commands[name] for name in command_names]
    
    def get_commands_by_tag(self, tag: str) -> List[Command]:
        """
        Get all commands with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of commands with the tag
        """
        return [
            self._commands[name]
            for name, metadata in self._metadata.items()
            if tag in metadata.tags
        ]
    
    def get_all_categories(self) -> List[str]:
        """
        Get all registered categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_command_tree(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get hierarchical view of commands organized by category.
        
        Returns:
            Dictionary mapping categories to lists of command metadata
        """
        tree = {}
        for category, commands in self._categories.items():
            tree[category] = [
                self._metadata[name].to_dict()
                for name in commands
            ]
        return tree
    
    def _load_metadata(self) -> None:
        """Load command metadata from storage."""
        if not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r') as f:
                data = json.load(f)
                
            self._metadata = {
                name: CommandMetadata.from_dict(meta_dict)
                for name, meta_dict in data.items()
            }
        except Exception as e:
            # Log error but continue with empty metadata
            print(f"Error loading command metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save command metadata to storage."""
        try:
            data = {
                name: metadata.to_dict()
                for name, metadata in self._metadata.items()
            }
            
            # Ensure directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but continue
            print(f"Error saving command metadata: {e}") 