"""
JSON Serializer

This module implements the serializer interface for JSON data format.
It provides serialization and deserialization between Python objects and JSON-compatible dictionaries.

Features:
- Default JSON serialization
- Custom type handling
- Schema validation
"""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, get_type_hints
from .serializer_interface import SerializerInterface


T = TypeVar('T')


class JsonSerializer(SerializerInterface[T]):
    """
    Generic JSON serializer implementation.
    
    This class provides:
    - Basic JSON serialization and deserialization
    - Type conversion for common Python types
    - Support for custom serialization rules
    """
    
    def __init__(self, cls: Optional[Type[T]] = None, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the JSON serializer.
        
        Args:
            cls: The class type this serializer handles (optional for backward compatibility)
            schema: Optional schema for validation (defaults to auto-generated)
            
        Note:
            When cls is not provided, the serializer operates in a more flexible mode
            where it doesn't enforce type checks during serialization/deserialization.
        """
        self.cls = cls
        self._schema = schema or (self._generate_schema() if cls else {})
        self._type_hints = get_type_hints(cls) if cls else {}
        
    def serialize(self, obj: T) -> Dict[str, Any]:
        """
        Serialize an object to a JSON-compatible dictionary.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Dictionary representation of the object
            
        Raises:
            TypeError: If object cannot be serialized
            ValueError: If object is invalid
        """
        if self.cls and not isinstance(obj, self.cls):
            raise TypeError(f"Expected object of type {self.cls.__name__}, got {type(obj).__name__}")
            
        result = {}
        
        # Convert object attributes to dictionary
        for key, value in obj.__dict__.items():
            # Skip private attributes (starting with underscore)
            if key.startswith('_'):
                continue
                
            # Convert value to JSON-compatible format
            result[key] = self._convert_to_json_compatible(value)
            
        return result
    
    def deserialize(self, data: Dict[str, Any]) -> T:
        """
        Deserialize a dictionary into an object.
        
        Args:
            data: Dictionary representation to deserialize
            
        Returns:
            Deserialized object
            
        Raises:
            TypeError: If data has invalid type
            ValueError: If data is invalid
            KeyError: If required field is missing
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dictionary, got {type(data).__name__}")
            
        # Validate data against schema
        if not self.validate(data):
            raise ValueError(f"Data does not conform to schema for {self.cls.__name__}")
            
        # Create object from dictionary
        converted_data = {}
        for key, value in data.items():
            # Convert to appropriate Python type based on type hints
            if key in self._type_hints:
                expected_type = self._type_hints[key]
                converted_data[key] = self._convert_from_json_compatible(value, expected_type)
            else:
                converted_data[key] = value
                
        return self.cls(**converted_data)
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate if data conforms to the schema.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        schema = self.get_schema()
        
        # Check required fields
        for field_name, field_schema in schema.items():
            if field_schema.get('required', False) and field_name not in data:
                return False
                
            # Validate field if present
            if field_name in data:
                field_value = data[field_name]
                
                # Check type
                if 'type' in field_schema:
                    if not self._check_type(field_value, field_schema['type']):
                        return False
                        
                # Check enum
                if 'enum' in field_schema and field_value not in field_schema['enum']:
                    return False
                    
                # Check pattern (for strings)
                if 'pattern' in field_schema and isinstance(field_value, str):
                    import re
                    if not re.match(field_schema['pattern'], field_value):
                        return False
                        
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema for this serializer.
        
        Returns:
            Dictionary representing the schema
        """
        return self._schema
    
    def _generate_schema(self) -> Dict[str, Any]:
        """
        Generate a schema based on the class type hints.
        
        Returns:
            Dictionary representing the schema
        """
        schema = {}
        type_hints = get_type_hints(self.cls)
        
        # Analyze class initialization parameters
        import inspect
        init_signature = inspect.signature(self.cls.__init__)
        
        for param_name, param in init_signature.parameters.items():
            # Skip 'self' parameter
            if param_name == 'self':
                continue
                
            field_schema = {}
            
            # Mark as required if no default value
            field_schema['required'] = param.default == inspect.Parameter.empty
            
            # Add type information if available
            if param_name in type_hints:
                field_type = type_hints[param_name]
                field_schema['type'] = self._type_to_schema_type(field_type)
                
            schema[param_name] = field_schema
            
        return schema
    
    def _type_to_schema_type(self, typ: Type) -> str:
        """
        Convert Python type to schema type.
        
        Args:
            typ: Python type
            
        Returns:
            Schema type name
        """
        import typing
        
        # Handle primitive types
        if typ == str:
            return 'string'
        elif typ == int:
            return 'integer'
        elif typ == float:
            return 'number'
        elif typ == bool:
            return 'boolean'
        elif typ == dict or getattr(typ, '__origin__', None) == dict:
            return 'object'
        elif typ == list or getattr(typ, '__origin__', None) == list:
            return 'array'
            
        # Handle Optional types
        if getattr(typ, '__origin__', None) == typing.Union:
            # Check if it's Optional (Union with None)
            if type(None) in typ.__args__:
                # Get the other type(s)
                other_types = [t for t in typ.__args__ if t != type(None)]
                if len(other_types) == 1:
                    return self._type_to_schema_type(other_types[0])
                    
        # Default to string for complex types
        return 'string'
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if value matches the expected type.
        
        Args:
            value: Value to check
            expected_type: Schema type name
            
        Returns:
            True if type matches, False otherwise
        """
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == 'number':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'null':
            return value is None
        else:
            return True  # Unknown type, assume valid
    
    def _convert_to_json_compatible(self, value: Any) -> Any:
        """
        Convert a Python value to a JSON-compatible value.
        
        Args:
            value: Python value to convert
            
        Returns:
            JSON-compatible value
        """
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, dict):
            return {k: self._convert_to_json_compatible(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._convert_to_json_compatible(item) for item in value]
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            # Handle nested objects
            return {k: self._convert_to_json_compatible(v) for k, v in value.__dict__.items()
                   if not k.startswith('_')}
        else:
            # Try to convert to string as a fallback
            return str(value)
    
    def _convert_from_json_compatible(self, value: Any, expected_type: Type) -> Any:
        """
        Convert a JSON-compatible value to a Python value.
        
        Args:
            value: JSON-compatible value to convert
            expected_type: Expected Python type
            
        Returns:
            Python value
        """
        import typing
        
        # Handle None value
        if value is None:
            return None
            
        # Handle primitive types
        if expected_type == str:
            return str(value)
        elif expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == bool:
            return bool(value)
        elif expected_type == dict or getattr(expected_type, '__origin__', None) == dict:
            if not isinstance(value, dict):
                value = {}
            return value
        elif expected_type == list or getattr(expected_type, '__origin__', None) == list:
            if not isinstance(value, list):
                value = []
            return value
        elif expected_type == datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
            
        # Handle Optional types
        if getattr(expected_type, '__origin__', None) == typing.Union:
            # Check if it's Optional (Union with None)
            if type(None) in expected_type.__args__:
                # Get the other type(s)
                other_types = [t for t in expected_type.__args__ if t != type(None)]
                if len(other_types) == 1:
                    return self._convert_from_json_compatible(value, other_types[0])
                    
        # Try to create an instance of the expected type
        try:
            if isinstance(value, dict) and hasattr(expected_type, '__init__'):
                return expected_type(**value)
            return expected_type(value)
        except Exception:
            # Return as is if conversion fails
            return value 