"""
Entity Serializer

This module implements entity-specific serialization, extending the JSON serializer with:
- Relationship handling
- ID-based entity lookup
- Partial updates
- Entity validation

It's designed to work with domain entities from the core module.
"""
from typing import Dict, List, Any, Optional, Type, TypeVar, Callable, Union, Set
import copy
from .serializer_interface import EntitySerializerInterface
from .json_serializer import JsonSerializer


T = TypeVar('T')


class EntitySerializer(EntitySerializerInterface[T]):
    """
    Entity serializer implementation.
    
    This class extends JsonSerializer with entity-specific functionality:
    - Relationship resolution
    - ID-based lookup
    - Batch operations
    - Partial updates
    """
    
    def __init__(self, 
                 cls: Type[T], 
                 schema: Optional[Dict[str, Any]] = None,
                 relationship_resolver: Optional[Callable[[str, str, int], Optional[Dict[str, Any]]]] = None):
        """
        Initialize the entity serializer.
        
        Args:
            cls: The entity class type this serializer handles
            schema: Optional schema for validation
            relationship_resolver: Optional function to resolve related entities
        """
        self.json_serializer = JsonSerializer(cls, schema)
        self.cls = cls
        self.relationship_resolver = relationship_resolver
        
    def serialize(self, obj: T) -> Dict[str, Any]:
        """
        Serialize an entity to a dictionary.
        
        Args:
            obj: Entity to serialize
            
        Returns:
            Dictionary representation of the entity
            
        Raises:
            TypeError: If object cannot be serialized
            ValueError: If object is invalid
        """
        return self.json_serializer.serialize(obj)
    
    def deserialize(self, data: Dict[str, Any]) -> T:
        """
        Deserialize a dictionary into an entity.
        
        Args:
            data: Dictionary representation to deserialize
            
        Returns:
            Deserialized entity
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid
            KeyError: If required field is missing
        """
        return self.json_serializer.deserialize(data)
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate if data conforms to the entity schema.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return self.json_serializer.validate(data)
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema for this entity serializer.
        
        Returns:
            Dictionary representing the schema
        """
        return self.json_serializer.get_schema()
    
    def serialize_list(self, objects: List[T]) -> List[Dict[str, Any]]:
        """
        Serialize a list of entities.
        
        Args:
            objects: List of entities to serialize
            
        Returns:
            List of serialized dictionary representations
            
        Raises:
            TypeError: If objects cannot be serialized
            ValueError: If objects are invalid
        """
        return [self.serialize(obj) for obj in objects]
    
    def deserialize_list(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Deserialize a list of dictionary representations into entities.
        
        Args:
            data_list: List of dictionary representations
            
        Returns:
            List of deserialized entities
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid
            KeyError: If required field is missing
        """
        return [self.deserialize(data) for data in data_list]
    
    def serialize_with_relationships(self, obj: T, depth: int = 1) -> Dict[str, Any]:
        """
        Serialize an entity with its relationships.
        
        Args:
            obj: Entity to serialize
            depth: Depth of relationship traversal (default: 1)
            
        Returns:
            Dictionary representation with relationships included
            
        Raises:
            TypeError: If object cannot be serialized
            ValueError: If object is invalid
        """
        # Start with basic serialization
        result = self.serialize(obj)
        
        # Stop if no relationship resolver or depth is 0
        if self.relationship_resolver is None or depth <= 0:
            return result
            
        # Process relationship fields
        processed_ids: Set[str] = set()
        
        # Track the entity ID to avoid circular references
        entity_id = result.get('id', None)
        if entity_id:
            processed_ids.add(entity_id)
            
        # Process standard relationship fields
        relationship_fields = ['depends_on', 'blocks', 'linked_to', 'parent_id', 'subtasks']
        for field in relationship_fields:
            if field in result:
                self._resolve_relationship_field(result, field, processed_ids, depth)
                
        return result
    
    def update_from_dict(self, obj: T, data: Dict[str, Any]) -> T:
        """
        Update an existing entity with data from a dictionary.
        
        Args:
            obj: Entity to update
            data: Dictionary with update data
            
        Returns:
            Updated entity
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid for the object
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dictionary, got {type(data).__name__}")
            
        # Create a copy of the object to avoid modifying the original
        updated_obj = copy.deepcopy(obj)
        
        # Update fields from data
        for key, value in data.items():
            if hasattr(updated_obj, key):
                # Use type hints if available
                expected_type = None
                if hasattr(self.json_serializer, '_type_hints'):
                    expected_type = self.json_serializer._type_hints.get(key, None)
                    
                if expected_type:
                    # Convert to appropriate type
                    converted_value = self.json_serializer._convert_from_json_compatible(value, expected_type)
                    setattr(updated_obj, key, converted_value)
                else:
                    # Set directly if no type hint
                    setattr(updated_obj, key, value)
                    
        return updated_obj
    
    def _resolve_relationship_field(self, 
                                    data: Dict[str, Any], 
                                    field: str, 
                                    processed_ids: Set[str], 
                                    depth: int) -> None:
        """
        Resolve relationships for a specific field.
        
        Args:
            data: Entity data being processed
            field: Relationship field name
            processed_ids: Set of already processed entity IDs
            depth: Remaining depth for relationship traversal
        """
        field_value = data[field]
        
        # Handle different field types
        if isinstance(field_value, str) and self.relationship_resolver:
            # Single relationship ID
            related_data = self.relationship_resolver(field_value, field, depth - 1)
            if related_data and related_data.get('id') not in processed_ids:
                processed_ids.add(related_data.get('id'))
                data[f"{field}_data"] = related_data
                
        elif isinstance(field_value, list) and self.relationship_resolver:
            # List of relationship IDs
            resolved_items = []
            for item_id in field_value:
                # Skip already processed IDs
                if item_id in processed_ids:
                    continue
                    
                related_data = self.relationship_resolver(item_id, field, depth - 1)
                if related_data:
                    processed_ids.add(item_id)
                    resolved_items.append(related_data)
                    
            if resolved_items:
                data[f"{field}_data"] = resolved_items 