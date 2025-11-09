"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/sandbox/plugin_sandbox.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Uses sandbox to safely load and execute plugins
    - CoreManager: Configures sandbox security policies
    - CustomPlugins: All third-party plugins are executed within this sandbox
    - SecurityModule: Monitors sandbox violations and resource usage

Purpose:
    Provides a sandboxing mechanism for plugins to enhance security and
    limit access to resources based on permissions. Implements multiple
    security levels with granular control over file access, network connectivity,
    resource usage, and code execution capabilities.

Requirements:
    - Must properly isolate plugin code execution from the main application
    - Must restrict unauthorized file system access
    - Must prevent unauthorized network access
    - Must limit resource consumption (memory, CPU)
    - CRITICAL: Plugin sandbox must be applied consistently
    - CRITICAL: All file/network/execution operations must be intercepted
    - CRITICAL: Security violations must be properly logged
    - CRITICAL: Sandbox deactivation must restore original system state

Plugin Sandboxing System

This module provides a sandboxing mechanism for plugins to enhance security
and limit access to resources based on permissions.
"""

import importlib
import inspect
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from ...common.exceptions import PluginSandboxError
from ..plugin_interface import Plugin

logger = logging.getLogger(__name__)


class SandboxRestriction:
    """Enumeration of possible sandbox restrictions."""
    
    # File system restrictions
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    
    # Network restrictions
    NETWORK_ACCESS = "network_access"
    
    # System restrictions
    EXEC_EXTERNAL = "exec_external"
    IMPORT_RESTRICTION = "import_restriction"
    
    # Resources restrictions
    MEMORY_LIMIT = "memory_limit"
    CPU_LIMIT = "cpu_limit"
    
    # All restrictions combined
    ALL_RESTRICTIONS = [
        FILE_WRITE, FILE_READ, NETWORK_ACCESS, 
        EXEC_EXTERNAL, IMPORT_RESTRICTION,
        MEMORY_LIMIT, CPU_LIMIT
    ]


class SecurityLevel:
    """Predefined security levels for plugins."""
    
    UNTRUSTED = "untrusted"  # Maximum restrictions
    LOW_TRUST = "low_trust"  # Many restrictions, minimal permissions
    MEDIUM_TRUST = "medium_trust"  # Balanced restrictions/permissions
    HIGH_TRUST = "high_trust"  # Minimal restrictions, many permissions
    FULL_TRUST = "full_trust"  # No restrictions (internal plugins only)
    
    # Define restrictions for each security level
    LEVEL_RESTRICTIONS = {
        UNTRUSTED: SandboxRestriction.ALL_RESTRICTIONS,
        LOW_TRUST: [
            SandboxRestriction.FILE_WRITE,
            SandboxRestriction.NETWORK_ACCESS,
            SandboxRestriction.EXEC_EXTERNAL,
            SandboxRestriction.IMPORT_RESTRICTION,
            SandboxRestriction.MEMORY_LIMIT,
            SandboxRestriction.CPU_LIMIT
        ],
        MEDIUM_TRUST: [
            SandboxRestriction.FILE_WRITE,
            SandboxRestriction.EXEC_EXTERNAL,
            SandboxRestriction.IMPORT_RESTRICTION,
            SandboxRestriction.MEMORY_LIMIT
        ],
        HIGH_TRUST: [
            SandboxRestriction.EXEC_EXTERNAL,
            SandboxRestriction.MEMORY_LIMIT
        ],
        FULL_TRUST: []  # No restrictions
    }


class SandboxPolicy:
    """Defines security policies for a sandboxed plugin."""
    
    def __init__(self, 
                security_level: str = SecurityLevel.MEDIUM_TRUST,
                allowed_imports: Optional[List[str]] = None,
                allowed_paths: Optional[List[str]] = None,
                memory_limit_mb: int = 100,
                cpu_limit_percent: int = 50,
                allowed_network_hosts: Optional[List[str]] = None):
        """
        Initialize a sandbox policy.
        
        Args:
            security_level: Predefined security level
            allowed_imports: List of module import patterns that are allowed
            allowed_paths: List of file paths that plugin can access
            memory_limit_mb: Maximum memory usage in MB
            cpu_limit_percent: Maximum CPU usage as percentage
            allowed_network_hosts: List of hostnames the plugin can connect to
        """
        self.security_level = security_level
        self.restrictions = SecurityLevel.LEVEL_RESTRICTIONS.get(
            security_level, SecurityLevel.LEVEL_RESTRICTIONS[SecurityLevel.MEDIUM_TRUST]
        )
        
        # Initialize with defaults if not provided
        self.allowed_imports = allowed_imports or []
        self.allowed_paths = allowed_paths or []
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self.allowed_network_hosts = allowed_network_hosts or []


class PluginSandbox:
    """
    Sandbox for executing plugin code with restricted permissions.
    
    This class provides mechanisms to:
    1. Limit file system access
    2. Restrict network access
    3. Control memory and CPU usage
    4. Prevent execution of unauthorized code
    5. Monitor plugin activities for security
    """
    
    def __init__(self, plugin_id: str, policy: Optional[SandboxPolicy] = None):
        """
        Initialize a plugin sandbox.
        
        Args:
            plugin_id: ID of the plugin being sandboxed
            policy: Sandbox policy to apply, or None for default policy
        """
        self.plugin_id = plugin_id
        self.policy = policy or SandboxPolicy()
        self.active = False
        self._original_modules: Dict[str, Any] = {}
        self._original_builtins: Dict[str, Any] = {}
        self._monitored_actions: List[Dict[str, Any]] = []
    
    def __enter__(self):
        """Activate sandbox restrictions when entering context."""
        self.activate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Deactivate sandbox restrictions when exiting context."""
        self.deactivate()
        return False  # Don't suppress exceptions
    
    def activate(self):
        """Apply sandbox restrictions."""
        if self.active:
            return
        
        logger.debug(f"Activating sandbox for plugin '{self.plugin_id}'")
        
        # Apply import restrictions if needed
        if SandboxRestriction.IMPORT_RESTRICTION in self.policy.restrictions:
            self._restrict_imports()
        
        # Apply file system restrictions if needed
        if SandboxRestriction.FILE_READ in self.policy.restrictions or \
           SandboxRestriction.FILE_WRITE in self.policy.restrictions:
            self._restrict_file_operations()
        
        # Apply network restrictions if needed
        if SandboxRestriction.NETWORK_ACCESS in self.policy.restrictions:
            self._restrict_network_access()
        
        # Apply execution restrictions if needed
        if SandboxRestriction.EXEC_EXTERNAL in self.policy.restrictions:
            self._restrict_exec()
        
        # Apply resource limitations if needed
        if SandboxRestriction.MEMORY_LIMIT in self.policy.restrictions or \
           SandboxRestriction.CPU_LIMIT in self.policy.restrictions:
            self._limit_resources()
        
        self.active = True
        logger.info(f"Sandbox activated for plugin '{self.plugin_id}' with security level "
                   f"'{self.policy.security_level}'")
    
    def deactivate(self):
        """Remove sandbox restrictions."""
        if not self.active:
            return
        
        logger.debug(f"Deactivating sandbox for plugin '{self.plugin_id}'")
        
        # Restore original import functionality
        if SandboxRestriction.IMPORT_RESTRICTION in self.policy.restrictions:
            self._restore_imports()
        
        # Restore original file operations
        if SandboxRestriction.FILE_READ in self.policy.restrictions or \
           SandboxRestriction.FILE_WRITE in self.policy.restrictions:
            self._restore_file_operations()
        
        # Restore original network access
        if SandboxRestriction.NETWORK_ACCESS in self.policy.restrictions:
            self._restore_network_access()
        
        # Restore original execution capabilities
        if SandboxRestriction.EXEC_EXTERNAL in self.policy.restrictions:
            self._restore_exec()
        
        # Remove resource limitations
        if SandboxRestriction.MEMORY_LIMIT in self.policy.restrictions or \
           SandboxRestriction.CPU_LIMIT in self.policy.restrictions:
            self._restore_resources()
        
        self.active = False
        logger.info(f"Sandbox deactivated for plugin '{self.plugin_id}'")
    
    def log_action(self, action_type: str, details: Dict[str, Any]):
        """
        Log an action performed by the plugin for auditing.
        
        Args:
            action_type: Type of action being performed
            details: Detailed information about the action
        """
        action = {
            "plugin_id": self.plugin_id,
            "type": action_type,
            "details": details,
            "timestamp": int(importlib.import_module("time").time())
        }
        
        self._monitored_actions.append(action)
        logger.debug(f"Plugin '{self.plugin_id}' action: {action_type} - {details}")
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """
        Get the log of actions performed by the plugin.
        
        Returns:
            List[Dict[str, Any]]: List of logged actions
        """
        return self._monitored_actions.copy()
    
    def is_path_allowed(self, path: str) -> bool:
        """
        Check if a file path is allowed for access by the plugin.
        
        Args:
            path: File path to check
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        # If no file restriction, allow access
        if (SandboxRestriction.FILE_READ not in self.policy.restrictions and 
            SandboxRestriction.FILE_WRITE not in self.policy.restrictions):
            return True
        
        # If path is None, don't allow
        if not path:
            return False
        
        # Check against allowed paths
        path = os.path.abspath(path)
        for allowed_path in self.policy.allowed_paths:
            allowed_path = os.path.abspath(allowed_path)
            if path == allowed_path or path.startswith(allowed_path + os.sep):
                return True
        
        return False
    
    def is_import_allowed(self, module_name: str) -> bool:
        """
        Check if a module import is allowed.
        
        Args:
            module_name: Name of the module to import
            
        Returns:
            bool: True if import is allowed, False otherwise
        """
        # If no import restriction, allow all imports
        if SandboxRestriction.IMPORT_RESTRICTION not in self.policy.restrictions:
            return True
        
        # Check against allowed imports
        for allowed_pattern in self.policy.allowed_imports:
            if module_name == allowed_pattern or module_name.startswith(allowed_pattern + "."):
                return True
        
        return False
    
    def is_network_host_allowed(self, hostname: str) -> bool:
        """
        Check if network access to a host is allowed.
        
        Args:
            hostname: Hostname to check
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        # If no network restriction, allow all hosts
        if SandboxRestriction.NETWORK_ACCESS not in self.policy.restrictions:
            return True
        
        # Check against allowed hosts
        for allowed_host in self.policy.allowed_network_hosts:
            if hostname == allowed_host or hostname.endswith("." + allowed_host):
                return True
        
        return False
    
    def execute_sandboxed(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function within the sandbox.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the function call
            
        Raises:
            PluginSandboxError: If an error occurs during sandboxed execution
        """
        if not self.active:
            self.activate()
            auto_deactivate = True
        else:
            auto_deactivate = False
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in sandboxed execution for plugin '{self.plugin_id}': {str(e)}")
            raise PluginSandboxError(f"Sandboxed execution failed: {str(e)}") from e
        finally:
            if auto_deactivate:
                self.deactivate()
    
    def _restrict_imports(self):
        """Apply import restrictions."""
        # Store original import functionality
        self._original_modules = {
            "__import__": __import__
        }
        
        # Replace __import__ with restricted version
        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            if not self.is_import_allowed(name):
                self.log_action("import_blocked", {"module": name})
                raise PluginSandboxError(
                    f"Plugin '{self.plugin_id}' attempted to import restricted module: {name}"
                )
            
            self.log_action("import_allowed", {"module": name})
            return self._original_modules["__import__"](name, globals, locals, fromlist, level)
        
        __builtins__["__import__"] = restricted_import
    
    def _restore_imports(self):
        """Restore original import functionality."""
        if "__import__" in self._original_modules:
            __builtins__["__import__"] = self._original_modules["__import__"]
    
    def _restrict_file_operations(self):
        """Apply file system restrictions."""
        # Store original file operations
        builtins_module = importlib.import_module("builtins")
        self._original_builtins.update({
            "open": builtins_module.open
        })
        
        # Replace open with restricted version
        def restricted_open(file, mode="r", *args, **kwargs):
            if not isinstance(file, str):
                # Handle file-like objects or file descriptors
                return self._original_builtins["open"](file, mode, *args, **kwargs)
            
            # Check read/write restrictions
            write_mode = any(char in mode for char in "wxa+")
            if write_mode and SandboxRestriction.FILE_WRITE in self.policy.restrictions:
                if not self.is_path_allowed(file):
                    self.log_action("file_write_blocked", {"path": file})
                    raise PluginSandboxError(
                        f"Plugin '{self.plugin_id}' attempted to write to restricted path: {file}"
                    )
            
            if SandboxRestriction.FILE_READ in self.policy.restrictions:
                if not self.is_path_allowed(file):
                    self.log_action("file_read_blocked", {"path": file})
                    raise PluginSandboxError(
                        f"Plugin '{self.plugin_id}' attempted to read from restricted path: {file}"
                    )
            
            self.log_action("file_access", {"path": file, "mode": mode})
            return self._original_builtins["open"](file, mode, *args, **kwargs)
        
        builtins_module.open = restricted_open
    
    def _restore_file_operations(self):
        """Restore original file operations."""
        if "open" in self._original_builtins:
            importlib.import_module("builtins").open = self._original_builtins["open"]
    
    def _restrict_network_access(self):
        """Apply network access restrictions."""
        # This is a simplified implementation and would need to be expanded
        # with real socket interception in a production system
        
        # Try to import socket module
        try:
            socket_module = importlib.import_module("socket")
            
            # Store original socket functionality
            self._original_modules.update({
                "socket_create_connection": socket_module.create_connection,
                "socket_socket": socket_module.socket
            })
            
            # Replace socket creation with restricted version
            def restricted_create_connection(address, *args, **kwargs):
                host, _ = address
                if not self.is_network_host_allowed(host):
                    self.log_action("network_blocked", {"host": host})
                    raise PluginSandboxError(
                        f"Plugin '{self.plugin_id}' attempted to connect to restricted host: {host}"
                    )
                
                self.log_action("network_access", {"host": host})
                return self._original_modules["socket_create_connection"](address, *args, **kwargs)
            
            # Replace socket constructor
            original_socket = self._original_modules["socket_socket"]
            def restricted_socket(*args, **kwargs):
                socket = original_socket(*args, **kwargs)
                original_connect = socket.connect
                
                def restricted_connect(address):
                    if isinstance(address, tuple) and len(address) >= 1:
                        host = address[0]
                        if not self.is_network_host_allowed(host):
                            self.log_action("network_blocked", {"host": host})
                            raise PluginSandboxError(
                                f"Plugin '{self.plugin_id}' attempted to connect to restricted host: {host}"
                            )
                        self.log_action("network_access", {"host": host})
                    
                    return original_connect(address)
                
                socket.connect = restricted_connect
                return socket
            
            socket_module.create_connection = restricted_create_connection
            socket_module.socket = restricted_socket
            
        except ImportError:
            logger.warning("Could not restrict socket module - not available")
    
    def _restore_network_access(self):
        """Restore original network access."""
        try:
            socket_module = importlib.import_module("socket")
            
            # Restore original socket functionality
            if "socket_create_connection" in self._original_modules:
                socket_module.create_connection = self._original_modules["socket_create_connection"]
            
            if "socket_socket" in self._original_modules:
                socket_module.socket = self._original_modules["socket_socket"]
                
        except ImportError:
            pass
    
    def _restrict_exec(self):
        """Apply execution restrictions."""
        # Store original exec/eval functions
        builtins_module = importlib.import_module("builtins")
        self._original_builtins.update({
            "exec": builtins_module.exec,
            "eval": builtins_module.eval
        })
        
        # Replace exec with restricted version
        def restricted_exec(*args, **kwargs):
            self.log_action("exec_blocked", {"args": str(args)})
            raise PluginSandboxError(
                f"Plugin '{self.plugin_id}' attempted to use exec(), which is not allowed"
            )
        
        # Replace eval with restricted version
        def restricted_eval(*args, **kwargs):
            self.log_action("eval_blocked", {"args": str(args)})
            raise PluginSandboxError(
                f"Plugin '{self.plugin_id}' attempted to use eval(), which is not allowed"
            )
        
        builtins_module.exec = restricted_exec
        builtins_module.eval = restricted_eval
        
        # Also block subprocess
        try:
            subprocess_module = importlib.import_module("subprocess")
            self._original_modules.update({
                "subprocess_run": subprocess_module.run,
                "subprocess_Popen": subprocess_module.Popen
            })
            
            # Replace subprocess.run
            def restricted_run(*args, **kwargs):
                self.log_action("subprocess_blocked", {"args": str(args)})
                raise PluginSandboxError(
                    f"Plugin '{self.plugin_id}' attempted to use subprocess.run(), which is not allowed"
                )
            
            # Replace subprocess.Popen
            def restricted_Popen(*args, **kwargs):
                self.log_action("subprocess_blocked", {"args": str(args)})
                raise PluginSandboxError(
                    f"Plugin '{self.plugin_id}' attempted to use subprocess.Popen(), which is not allowed"
                )
            
            subprocess_module.run = restricted_run
            subprocess_module.Popen = restricted_Popen
            
        except ImportError:
            logger.warning("Could not restrict subprocess module - not available")
    
    def _restore_exec(self):
        """Restore original execution capabilities."""
        builtins_module = importlib.import_module("builtins")
        
        # Restore exec/eval
        if "exec" in self._original_builtins:
            builtins_module.exec = self._original_builtins["exec"]
        
        if "eval" in self._original_builtins:
            builtins_module.eval = self._original_builtins["eval"]
        
        # Restore subprocess
        try:
            subprocess_module = importlib.import_module("subprocess")
            
            if "subprocess_run" in self._original_modules:
                subprocess_module.run = self._original_modules["subprocess_run"]
            
            if "subprocess_Popen" in self._original_modules:
                subprocess_module.Popen = self._original_modules["subprocess_Popen"]
                
        except ImportError:
            pass
    
    def _limit_resources(self):
        """Apply resource limitations."""
        # This is a simplified implementation
        # In practice, you would use OS-specific mechanisms like:
        # - Linux: cgroups or resource module
        # - Windows: job objects
        # - Cross-platform: use of resource limits libraries
        
        # Here we'll use the resource module if available
        try:
            resource_module = importlib.import_module("resource")
            
            # Memory limit
            if SandboxRestriction.MEMORY_LIMIT in self.policy.restrictions:
                # Convert MB to bytes
                memory_limit_bytes = self.policy.memory_limit_mb * 1024 * 1024
                
                # RLIMIT_AS limits the process's virtual memory size
                if hasattr(resource_module, "RLIMIT_AS"):
                    # Get the current limit
                    soft, hard = resource_module.getrlimit(resource_module.RLIMIT_AS)
                    
                    # Store it for restoration
                    self._original_modules["rlimit_as"] = (soft, hard)
                    
                    # Set new limit
                    resource_module.setrlimit(
                        resource_module.RLIMIT_AS, 
                        (memory_limit_bytes, hard)
                    )
                    
                    self.log_action("resource_limit", {
                        "type": "memory", 
                        "limit_mb": self.policy.memory_limit_mb
                    })
            
            # CPU limit is harder to enforce directly
            # This would require more complex mechanisms like
            # thread monitoring or OS-specific APIs
            
        except ImportError:
            logger.warning("Could not apply resource limits - resource module not available")
            
    def _restore_resources(self):
        """Remove resource limitations."""
        try:
            resource_module = importlib.import_module("resource")
            
            # Restore memory limit
            if "rlimit_as" in self._original_modules and hasattr(resource_module, "RLIMIT_AS"):
                soft, hard = self._original_modules["rlimit_as"]
                resource_module.setrlimit(resource_module.RLIMIT_AS, (soft, hard))
                
        except ImportError:
            pass


# Decorator to apply sandboxing to a method
def sandboxed(security_level: Optional[str] = None,
             allowed_imports: Optional[List[str]] = None,
             allowed_paths: Optional[List[str]] = None):
    """
    Decorator to apply sandboxing to a plugin method.
    
    Example:
        @sandboxed(security_level=SecurityLevel.LOW_TRUST)
        def risky_operation(self, data):
            # This code will run in a sandbox
            return process_data(data)
    
    Args:
        security_level: Override the plugin's security level for this method
        allowed_imports: Additional allowed imports for this method
        allowed_paths: Additional allowed paths for this method
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Only apply to Plugin instances
            if not isinstance(self, Plugin):
                return func(self, *args, **kwargs)
            
            # Create a policy for this method
            base_policy = getattr(self, "_sandbox_policy", SandboxPolicy())
            
            # Override settings if specified
            method_policy = SandboxPolicy(
                security_level=security_level or base_policy.security_level,
                allowed_imports=(allowed_imports or []) + base_policy.allowed_imports,
                allowed_paths=(allowed_paths or []) + base_policy.allowed_paths,
                memory_limit_mb=base_policy.memory_limit_mb,
                cpu_limit_percent=base_policy.cpu_limit_percent,
                allowed_network_hosts=base_policy.allowed_network_hosts
            )
            
            # Create a sandbox for this method
            sandbox = PluginSandbox(self.plugin_id, method_policy)
            
            # Execute in sandbox
            return sandbox.execute_sandboxed(func, self, *args, **kwargs)
            
        return wrapper
    return decorator


# Sandbox manager for handling plugin sandboxes
class SandboxManager:
    """
    Manages sandboxes for all plugins in the system.
    
    This class is responsible for:
    1. Creating sandboxes for plugins
    2. Assigning security policies to plugins
    3. Monitoring sandbox activity
    """
    
    def __init__(self):
        """Initialize the sandbox manager."""
        self.sandboxes: Dict[str, PluginSandbox] = {}
        self.policies: Dict[str, SandboxPolicy] = {}
        
        # Default plugin directories for security levels
        self.security_levels_paths = {
            SecurityLevel.UNTRUSTED: [],
            SecurityLevel.LOW_TRUST: [],
            SecurityLevel.MEDIUM_TRUST: [],
            SecurityLevel.HIGH_TRUST: [],
            SecurityLevel.FULL_TRUST: []
        }
    
    def create_sandbox(self, plugin_id: str, 
                      security_level: Optional[str] = None) -> PluginSandbox:
        """
        Create a sandbox for a plugin.
        
        Args:
            plugin_id: ID of the plugin
            security_level: Override the default security level
            
        Returns:
            PluginSandbox: The created sandbox
        """
        # Get the policy for this plugin
        policy = self.policies.get(plugin_id)
        
        if not policy:
            # Create a new policy
            policy = SandboxPolicy(
                security_level=security_level or SecurityLevel.MEDIUM_TRUST
            )
            self.policies[plugin_id] = policy
        elif security_level:
            # Override the security level
            policy.security_level = security_level
            policy.restrictions = SecurityLevel.LEVEL_RESTRICTIONS.get(
                security_level, SecurityLevel.LEVEL_RESTRICTIONS[SecurityLevel.MEDIUM_TRUST]
            )
        
        # Create the sandbox
        sandbox = PluginSandbox(plugin_id, policy)
        self.sandboxes[plugin_id] = sandbox
        
        logger.info(f"Created sandbox for plugin '{plugin_id}' with security level "
                   f"'{policy.security_level}'")
        
        return sandbox
    
    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """
        Get the sandbox for a plugin.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Optional[PluginSandbox]: The plugin's sandbox, or None if not found
        """
        return self.sandboxes.get(plugin_id)
    
    def set_plugin_policy(self, plugin_id: str, policy: SandboxPolicy):
        """
        Set the security policy for a plugin.
        
        Args:
            plugin_id: ID of the plugin
            policy: Security policy to apply
        """
        self.policies[plugin_id] = policy
        
        # Update existing sandbox if one exists
        if plugin_id in self.sandboxes:
            self.sandboxes[plugin_id].policy = policy
            logger.info(f"Updated policy for plugin '{plugin_id}' to security level "
                       f"'{policy.security_level}'")
    
    def determine_security_level(self, plugin_id: str, 
                                plugin_path: str,
                                manifest: Dict[str, Any]) -> str:
        """
        Determine the appropriate security level for a plugin.
        
        Args:
            plugin_id: ID of the plugin
            plugin_path: Path to the plugin directory
            manifest: Plugin manifest data
            
        Returns:
            str: The determined security level
        """
        # Check for internal plugins (in trusted directories)
        if any(plugin_path.startswith(trusted_path) for trusted_path in 
              self.security_levels_paths[SecurityLevel.FULL_TRUST]):
            return SecurityLevel.FULL_TRUST
        
        # Check requested security level from manifest
        requested_level = manifest.get("requested_security_level")
        
        # Check if plugin is digitally signed
        is_signed = manifest.get("signed", False)
        
        # Check permissions requested
        requested_permissions = manifest.get("permissions", [])
        
        # Simple heuristic for determining security level
        if is_signed and not requested_permissions:
            # Signed plugin with no special permissions
            return SecurityLevel.HIGH_TRUST
        elif is_signed and requested_permissions:
            # Signed plugin with some permissions
            return SecurityLevel.MEDIUM_TRUST
        elif not is_signed and not requested_permissions:
            # Unsigned plugin with no special permissions
            return SecurityLevel.LOW_TRUST
        else:
            # Unsigned plugin with permissions
            return SecurityLevel.UNTRUSTED
    
    def register_plugin_sandbox(self, plugin: Plugin, 
                              manifest: Dict[str, Any],
                              plugin_path: str) -> PluginSandbox:
        """
        Register a plugin with the sandbox manager.
        
        Args:
            plugin: The plugin instance
            manifest: Plugin manifest data
            plugin_path: Path to the plugin directory
            
        Returns:
            PluginSandbox: The created sandbox
        """
        # Determine security level
        security_level = self.determine_security_level(
            plugin.plugin_id, plugin_path, manifest
        )
        
        # Create policy based on manifest and security level
        policy = SandboxPolicy(
            security_level=security_level,
            allowed_imports=manifest.get("allowed_imports", []),
            allowed_paths=[plugin_path] + manifest.get("allowed_paths", []),
            memory_limit_mb=manifest.get("memory_limit_mb", 100),
            cpu_limit_percent=manifest.get("cpu_limit_percent", 50),
            allowed_network_hosts=manifest.get("allowed_network_hosts", [])
        )
        
        # Set the policy
        self.set_plugin_policy(plugin.plugin_id, policy)
        
        # Create and return sandbox
        sandbox = self.create_sandbox(plugin.plugin_id)
        
        # Attach policy to plugin
        setattr(plugin, "_sandbox_policy", policy)
        
        return sandbox
    
    def get_security_report(self, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a security report for plugins.
        
        Args:
            plugin_id: Optional ID to get report for a specific plugin
            
        Returns:
            Dict[str, Any]: Security report data
        """
        result = {"plugins": []}
        
        plugin_ids = [plugin_id] if plugin_id else list(self.sandboxes.keys())
        
        for pid in plugin_ids:
            if pid not in self.sandboxes:
                continue
                
            sandbox = self.sandboxes[pid]
            policy = self.policies.get(pid, SandboxPolicy())
            
            # Get action logs
            actions = sandbox.get_action_log()
            
            # Count actions by type
            action_counts = {}
            for action in actions:
                action_type = action["type"]
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # Calculate risk score based on actions
            risk_score = 0
            risk_factors = []
            
            if "file_write_blocked" in action_counts:
                risk_score += action_counts["file_write_blocked"] * 10
                risk_factors.append("Attempted unauthorized file writes")
                
            if "file_read_blocked" in action_counts:
                risk_score += action_counts["file_read_blocked"] * 5
                risk_factors.append("Attempted unauthorized file reads")
                
            if "network_blocked" in action_counts:
                risk_score += action_counts["network_blocked"] * 8
                risk_factors.append("Attempted unauthorized network access")
                
            if "import_blocked" in action_counts:
                risk_score += action_counts["import_blocked"] * 6
                risk_factors.append("Attempted to import unauthorized modules")
                
            if "exec_blocked" in action_counts or "eval_blocked" in action_counts:
                risk_score += 15
                risk_factors.append("Attempted to use exec/eval")
                
            if "subprocess_blocked" in action_counts:
                risk_score += 12
                risk_factors.append("Attempted to spawn subprocesses")
            
            # Compile plugin report
            plugin_report = {
                "plugin_id": pid,
                "security_level": policy.security_level,
                "restrictions": policy.restrictions,
                "allowed_imports": policy.allowed_imports,
                "allowed_paths": policy.allowed_paths,
                "allowed_network_hosts": policy.allowed_network_hosts,
                "actions": action_counts,
                "risk_score": risk_score,
                "risk_factors": risk_factors
            }
            
            result["plugins"].append(plugin_report)
        
        return result


# Global sandbox manager instance
sandbox_manager = SandboxManager() 