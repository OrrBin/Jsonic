"""Resolver for classes with type hints."""

import inspect
from typing import Any, Dict, Type, get_type_hints
from jsonic.type_resolver import TypeResolver


class TypeHintedResolver(TypeResolver):
    """Resolver for classes with type-hinted __init__ parameters."""
    
    def can_resolve(self, cls: Type) -> bool:
        """Check if class has type hints in __init__."""
        if not hasattr(cls, '__init__'):
            return False
        
        try:
            hints = get_type_hints(cls.__init__)
            # Has type hints if there are any hints besides 'return'
            return len(hints) > 0 and any(k != 'return' for k in hints.keys())
        except:
            return False
    
    def serialize(self, obj: Any, serialize_private_attributes: bool = True) -> Dict[str, Any]:
        """Serialize object by extracting __dict__ or __slots__, handling tuples and sets."""
        from jsonic.serializable import _serialize_fields, _get_attribute_names
        names = _get_attribute_names(obj)
        return _serialize_fields(names, lambda key: getattr(obj, key), serialize_private_attributes)

    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data using type hints from __init__."""
        from jsonic.constructors import constructor_kwargs, restore_attributes
        from jsonic.context import current_context
        private = current_context().deserialize_private_attributes
        init_params = constructor_kwargs(cls, data, private=private)
        
        # Create instance
        instance = cls(**init_params)
        
        # Set any additional attributes not in __init__
        restore_attributes(instance, {k: v for k, v in data.items() if k not in init_params}, private=private)
        
        return instance
    
    def priority(self) -> int:
        """TypeHinted resolver has lowest priority."""
        return 25
