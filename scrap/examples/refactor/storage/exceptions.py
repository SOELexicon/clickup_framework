"""
Exceptions for storage operations.

This module defines the exceptions thrown by storage layer components.
"""
from refactor.core.exceptions import ErrorCode


class StorageError(Exception):
    """Base exception for storage-related errors."""
    
    def __init__(self, message, code=None):
        """
        Initialize a storage error.
        
        Args:
            message: Error message
            code: Error code or identifier
        """
        super().__init__(message)
        self.message = message
        self.code = code


class FileAccessError(StorageError):
    """Exception raised when a file cannot be accessed."""
    
    def __init__(self, message, code=None):
        """
        Initialize a file access error.
        
        Args:
            message: Error message
            code: Error code or identifier
        """
        super().__init__(message, code or "STORAGE-FILE-001")


class RepositoryError(StorageError):
    """Exception raised for repository operations failures."""
    
    def __init__(self, message, code=None):
        """
        Initialize a repository error.
        
        Args:
            message: Error message
            code: Error code or identifier
        """
        super().__init__(message, code or "STORAGE-REPO-001")


class DataIntegrityError(StorageError):
    """Exception raised when data integrity is compromised."""
    
    def __init__(self, message, code=None):
        """
        Initialize a data integrity error.
        
        Args:
            message: Error message
            code: Error code or identifier
        """
        super().__init__(message, code or "STORAGE-INTEGRITY-001")


class ConfigurationError(StorageError):
    """Exception raised for storage configuration issues."""
    
    def __init__(self, message, code=None):
        """
        Initialize a configuration error.
        
        Args:
            message: Error message
            code: Error code or identifier
        """
        super().__init__(message, code or "STORAGE-CONFIG-001")


def get_storage_error_code(error_type, error_id=None):
    """
    Generate a standardized error code for storage errors.
    
    Args:
        error_type: Type of error (e.g., FILE, REPO, INTEGRITY)
        error_id: Optional error identifier
        
    Returns:
        ErrorCode object with standardized format
    """
    return ErrorCode("STORAGE", error_type, "ERROR", error_id or "001") 