"""
Serializer Interface

This module defines the abstract interface for data serializers.
Serializers handle the conversion between in-memory objects and their serialized representation.

Features:
- Common interface for all serializers
- Support for entity-specific serialization
- Customizable serialization options
"""
from typing import Dict, List, Any, Optional, TypeVar, Generic, Type
from abc import ABC, abstractmethod

T = TypeVar('T')


class SerializerInterface(Generic[T], ABC):
    """
    Abstract base class for serializers.
    
    This interface provides methods for:
    - Serializing objects to a specific format
    - Deserializing data into objects
    - Schema validation
    """
    
    @abstractmethod
    def serialize(self, obj: T) -> Dict[str, Any]:
        """
        Serialize an object to a dictionary representation.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Dictionary representation of the object
            
        Raises:
            TypeError: If object cannot be serialized
            ValueError: If object is invalid
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any]) -> T:
        """
        Deserialize data into an object.
        
        Args:
            data: Dictionary representation to deserialize
            
        Returns:
            Deserialized object
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid
            KeyError: If required field is missing
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate if data conforms to the expected schema.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema for this serializer.
        
        Returns:
            Dictionary representing the schema
        """
        pass


class EntitySerializerInterface(SerializerInterface[T], ABC):
    """
    Specialized serializer interface for entity objects.
    
    This interface adds methods specific to entity serialization:
    - ID-based lookup
    - Relationship handling
    - Partial updates
    """
    
    @abstractmethod
    def serialize_list(self, objects: List[T]) -> List[Dict[str, Any]]:
        """
        Serialize a list of objects.
        
        Args:
            objects: List of objects to serialize
            
        Returns:
            List of serialized dictionary representations
            
        Raises:
            TypeError: If objects cannot be serialized
            ValueError: If objects are invalid
        """
        pass
    
    @abstractmethod
    def deserialize_list(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Deserialize a list of dictionary representations into objects.
        
        Args:
            data_list: List of dictionary representations
            
        Returns:
            List of deserialized objects
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid
            KeyError: If required field is missing
        """
        pass
    
    @abstractmethod
    def serialize_with_relationships(self, obj: T, depth: int = 1) -> Dict[str, Any]:
        """
        Serialize an object with its relationships.
        
        Args:
            obj: Object to serialize
            depth: Depth of relationship traversal (default: 1)
            
        Returns:
            Dictionary representation with relationships included
            
        Raises:
            TypeError: If object cannot be serialized
            ValueError: If object is invalid
        """
        pass
    
    @abstractmethod
    def update_from_dict(self, obj: T, data: Dict[str, Any]) -> T:
        """
        Update an existing object with data from a dictionary.
        
        Args:
            obj: Object to update
            data: Dictionary with update data
            
        Returns:
            Updated object
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid for the object
        """
        pass 