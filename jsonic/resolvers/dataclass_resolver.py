"""Resolver for Python dataclasses."""

import dataclasses
from typing import Any, Dict, Type
from jsonic.type_resolver import TypeResolver


class DataclassResolver(TypeResolver):
    """Resolver for dataclass types."""
    
    def can_resolve(self, cls: Type) -> bool:
        """Check if type is a dataclass."""
        return dataclasses.is_dataclass(cls) and not isinstance(cls, type(type))
    
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize a dataclass instance."""
        return dataclasses.asdict(obj)
    
    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data into a dataclass instance."""
        # Get field names and types
        fields = {f.name: f for f in dataclasses.fields(cls)}
        
        # Filter data to only include fields that exist in the dataclass
        init_data = {k: v for k, v in data.items() if k in fields}
        
        return cls(**init_data)
    
    def priority(self) -> int:
        """Dataclass resolver priority."""
        return 50
