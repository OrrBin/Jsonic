"""Resolver for Python dataclasses."""

import dataclasses
from enum import Enum
from typing import Any, Dict, Type
from jsonic.type_resolver import TypeResolver


class DataclassResolver(TypeResolver):
    """Resolver for dataclass types."""
    
    def can_resolve(self, cls: Type) -> bool:
        """Check if type is a dataclass."""
        return dataclasses.is_dataclass(cls)
    
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize a dataclass instance, handling enums, tuples, and sets specially."""
        from jsonic.serializable import _serialize_object, _preprocess_tuples
        result = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            # Recursively serialize enums, tuples, and sets
            if isinstance(value, (Enum, tuple, set)):
                result[field.name] = _serialize_object(value)
            elif isinstance(value, (list, dict)):
                # Recursively preprocess lists and dicts for nested tuples/sets
                result[field.name] = _preprocess_tuples(value)
            else:
                result[field.name] = value
        return result
    
    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data into a dataclass instance."""
        # Get field names and types
        fields = {f.name: f for f in dataclasses.fields(cls)}
        
        # Filter data to only include fields that are in __init__ (init=True)
        init_data = {k: v for k, v in data.items() if k in fields and fields[k].init}
        
        # Create instance
        instance = cls(**init_data)
        
        # Set fields with init=False after creation
        for k, v in data.items():
            if k in fields and not fields[k].init:
                setattr(instance, k, v)
        
        return instance
    
    def priority(self) -> int:
        """Dataclass resolver priority."""
        return 50
