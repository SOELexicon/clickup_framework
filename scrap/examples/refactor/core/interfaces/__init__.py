"""
Interfaces Module - Public API interfaces for the Core Module.

This package contains the interface definitions that make up the public API
for the Core Module of the ClickUp JSON Manager.
"""

from refactor.core.interfaces.core_manager import CoreManager, CoreManagerError, InvalidQueryError

__all__ = [
    'CoreManager',
    'CoreManagerError',
    'InvalidQueryError',
] 