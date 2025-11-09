"""
Platform Abstraction Layer

This module provides platform-specific file system operations with a consistent interface.
It handles differences between Windows, macOS, and Linux to ensure cross-platform compatibility.

Features:
- Platform detection
- Path normalization
- Newline handling
- File operation abstractions
- Permission handling
"""
import os
import sys
import platform
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, BinaryIO, TextIO


class PlatformInfo:
    """
    Utility class for detecting and providing platform information.
    """
    
    @staticmethod
    def is_windows() -> bool:
        """Check if the current platform is Windows."""
        return sys.platform.startswith('win') or platform.system() == 'Windows'
    
    @staticmethod
    def is_macos() -> bool:
        """Check if the current platform is macOS."""
        return sys.platform.startswith('darwin') or platform.system() == 'Darwin'
    
    @staticmethod
    def is_linux() -> bool:
        """Check if the current platform is Linux."""
        return sys.platform.startswith('linux') or platform.system() == 'Linux'
    
    @staticmethod
    def get_platform_name() -> str:
        """Get the name of the current platform."""
        if PlatformInfo.is_windows():
            return "Windows"
        elif PlatformInfo.is_macos():
            return "macOS"
        elif PlatformInfo.is_linux():
            return "Linux"
        else:
            return platform.system()
    
    @staticmethod
    def get_newline() -> str:
        """Get the platform-specific newline character(s)."""
        return os.linesep
    
    @staticmethod
    def get_path_separator() -> str:
        """Get the platform-specific path separator."""
        return os.path.sep


class PlatformHandler(ABC):
    """
    Abstract base class for platform-specific file operations.
    """
    
    @abstractmethod
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        pass
    
    @abstractmethod
    def ensure_directory_exists(self, path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_permissions(self, path: str) -> Dict[str, Any]:
        """
        Get file permissions in a platform-specific manner.
        
        Args:
            path: File path
            
        Returns:
            Dictionary with permission information
        """
        pass
    
    @abstractmethod
    def set_file_permissions(self, path: str, permissions: Dict[str, Any]) -> bool:
        """
        Set file permissions in a platform-specific manner.
        
        Args:
            path: File path
            permissions: Dictionary with permission information
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_temp_directory(self) -> str:
        """
        Get the platform-specific temporary directory.
        
        Returns:
            Path to the temporary directory
        """
        pass
    
    @abstractmethod
    def get_user_data_directory(self) -> str:
        """
        Get the platform-specific user data directory.
        
        Returns:
            Path to the user data directory
        """
        pass


class WindowsPlatformHandler(PlatformHandler):
    """
    Windows-specific implementation of PlatformHandler.
    """
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path for Windows.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert forward slashes to backslashes
        normalized_path = path.replace('/', '\\')
        
        # Use os.path to handle other normalization tasks
        return os.path.normpath(normalized_path)
    
    def ensure_directory_exists(self, path: str) -> bool:
        """
        Ensure a directory exists on Windows, creating it if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            if os.path.exists(path):
                return os.path.isdir(path)
            
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    def get_file_permissions(self, path: str) -> Dict[str, Any]:
        """
        Get file permissions on Windows.
        
        Args:
            path: File path
            
        Returns:
            Dictionary with permission information
        """
        import stat
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get mode and determine if file is read-only
        mode = os.stat(path).st_mode
        is_readonly = not bool(mode & stat.S_IWRITE)
        
        # Check if file is hidden
        is_hidden = bool(os.stat(path).st_file_attributes & 0x2)
        
        # Create a Windows-specific permissions dictionary
        return {
            "readonly": is_readonly,
            "hidden": is_hidden,
            "executable": bool(mode & stat.S_IEXEC),
            "isdir": os.path.isdir(path)
        }
    
    def set_file_permissions(self, path: str, permissions: Dict[str, Any]) -> bool:
        """
        Set file permissions on Windows.
        
        Args:
            path: File path
            permissions: Dictionary with permission information
            
        Returns:
            True if successful, False otherwise
        """
        import stat
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            current_mode = os.stat(path).st_mode
            new_mode = current_mode
            
            # Handle readonly permission
            if "readonly" in permissions:
                if permissions["readonly"]:
                    # Remove write permission
                    new_mode = new_mode & ~stat.S_IWRITE
                else:
                    # Add write permission
                    new_mode = new_mode | stat.S_IWRITE
            
            # Set the file mode
            os.chmod(path, new_mode)
            
            # Handle hidden attribute (Windows-specific)
            if "hidden" in permissions:
                import subprocess
                import ctypes
                
                if permissions["hidden"]:
                    # Set hidden attribute
                    ctypes.windll.kernel32.SetFileAttributesW(path, 0x2)
                else:
                    # Remove hidden attribute
                    current_attributes = ctypes.windll.kernel32.GetFileAttributesW(path)
                    ctypes.windll.kernel32.SetFileAttributesW(path, current_attributes & ~0x2)
            
            return True
        except Exception:
            return False
    
    def get_temp_directory(self) -> str:
        """
        Get the Windows temporary directory.
        
        Returns:
            Path to the temporary directory
        """
        return os.environ.get('TEMP', os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Temp'))
    
    def get_user_data_directory(self) -> str:
        """
        Get the Windows user data directory.
        
        Returns:
            Path to the user data directory
        """
        return os.path.join(os.environ.get('APPDATA', ''), 'ClickUpJsonManager')


class UnixPlatformHandler(PlatformHandler):
    """
    Base class for Unix-like platforms (Linux and macOS).
    """
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path for Unix-like systems.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Ensure forward slashes and normalize
        normalized_path = path.replace('\\', '/')
        return os.path.normpath(normalized_path)
    
    def ensure_directory_exists(self, path: str) -> bool:
        """
        Ensure a directory exists on Unix-like systems, creating it if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            if os.path.exists(path):
                return os.path.isdir(path)
            
            os.makedirs(path, mode=0o755, exist_ok=True)
            return True
        except Exception:
            return False
    
    def get_file_permissions(self, path: str) -> Dict[str, Any]:
        """
        Get file permissions on Unix-like systems.
        
        Args:
            path: File path
            
        Returns:
            Dictionary with permission information
        """
        import stat
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get the mode
        mode = os.stat(path).st_mode
        
        # Create permissions dictionary
        return {
            "owner_read": bool(mode & stat.S_IRUSR),
            "owner_write": bool(mode & stat.S_IWUSR),
            "owner_exec": bool(mode & stat.S_IXUSR),
            "group_read": bool(mode & stat.S_IRGRP),
            "group_write": bool(mode & stat.S_IWGRP),
            "group_exec": bool(mode & stat.S_IXGRP),
            "other_read": bool(mode & stat.S_IROTH),
            "other_write": bool(mode & stat.S_IWOTH),
            "other_exec": bool(mode & stat.S_IXOTH),
            "isdir": os.path.isdir(path)
        }
    
    def set_file_permissions(self, path: str, permissions: Dict[str, Any]) -> bool:
        """
        Set file permissions on Unix-like systems.
        
        Args:
            path: File path
            permissions: Dictionary with permission information
            
        Returns:
            True if successful, False otherwise
        """
        import stat
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            # Start with no permissions
            mode = 0
            
            # Set owner permissions
            if permissions.get("owner_read", False):
                mode |= stat.S_IRUSR
            if permissions.get("owner_write", False):
                mode |= stat.S_IWUSR
            if permissions.get("owner_exec", False):
                mode |= stat.S_IXUSR
            
            # Set group permissions
            if permissions.get("group_read", False):
                mode |= stat.S_IRGRP
            if permissions.get("group_write", False):
                mode |= stat.S_IWGRP
            if permissions.get("group_exec", False):
                mode |= stat.S_IXGRP
            
            # Set other permissions
            if permissions.get("other_read", False):
                mode |= stat.S_IROTH
            if permissions.get("other_write", False):
                mode |= stat.S_IWOTH
            if permissions.get("other_exec", False):
                mode |= stat.S_IXOTH
            
            # Set the file mode
            os.chmod(path, mode)
            return True
        except Exception:
            return False


class LinuxPlatformHandler(UnixPlatformHandler):
    """
    Linux-specific implementation of PlatformHandler.
    """
    
    def get_temp_directory(self) -> str:
        """
        Get the Linux temporary directory.
        
        Returns:
            Path to the temporary directory
        """
        return os.environ.get('TMPDIR', '/tmp')
    
    def get_user_data_directory(self) -> str:
        """
        Get the Linux user data directory.
        
        Returns:
            Path to the user data directory
        """
        xdg_data_home = os.environ.get('XDG_DATA_HOME', '')
        if not xdg_data_home:
            home = os.environ.get('HOME', '')
            xdg_data_home = os.path.join(home, '.local', 'share')
        
        return os.path.join(xdg_data_home, 'clickup-json-manager')


class MacOSPlatformHandler(UnixPlatformHandler):
    """
    macOS-specific implementation of PlatformHandler.
    """
    
    def get_temp_directory(self) -> str:
        """
        Get the macOS temporary directory.
        
        Returns:
            Path to the temporary directory
        """
        return os.environ.get('TMPDIR', '/tmp')
    
    def get_user_data_directory(self) -> str:
        """
        Get the macOS user data directory.
        
        Returns:
            Path to the user data directory
        """
        home = os.environ.get('HOME', '')
        return os.path.join(home, 'Library', 'Application Support', 'ClickUpJsonManager')


class PlatformAbstraction:
    """
    Factory class that provides the appropriate platform handler.
    """
    
    @staticmethod
    def get_handler() -> PlatformHandler:
        """
        Get the platform-specific handler for the current system.
        
        Returns:
            PlatformHandler implementation for the current platform
        """
        if PlatformInfo.is_windows():
            return WindowsPlatformHandler()
        elif PlatformInfo.is_macos():
            return MacOSPlatformHandler()
        elif PlatformInfo.is_linux():
            return LinuxPlatformHandler()
        else:
            # Default to Unix-like if the specific platform is not recognized
            return UnixPlatformHandler() 