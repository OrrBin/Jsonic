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
    
    def serialize(self, obj: Any, serialize_private_attributes: bool = True) -> Dict[str, Any]:
        """Serialize a dataclass instance, handling enums, tuples, and sets specially."""
        from jsonic.serializable import _serialize_fields
        from jsonic.constructors import reject_required_initvars
        reject_required_initvars(type(obj), serializing=True)
        return _serialize_fields([field.name for field in dataclasses.fields(obj)],
                                 lambda key: getattr(obj, key), serialize_private_attributes)

    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data into a dataclass instance."""
        from jsonic.constructors import reject_required_initvars, restore_attributes
        reject_required_initvars(cls)
        # Get field names and types
        fields = {f.name: f for f in dataclasses.fields(cls)}
        
        # Filter data to only include fields that are in __init__ (init=True)
        init_data = {k: v for k, v in data.items() if k in fields and fields[k].init}
        
        # Create instance
        instance = cls(**init_data)
        
        # Set fields with init=False after creation
        restore_attributes(instance, {k: v for k, v in data.items() if k in fields and not fields[k].init})
        
        return instance
    
    def priority(self) -> int:
        """Dataclass resolver priority."""
        return 50
