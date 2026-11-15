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
        from jsonic.serializable import _serialize_fields, _get_all_slots
        names = list(vars(obj)) if hasattr(obj, '__dict__') and vars(obj) else [name for name in _get_all_slots(type(obj)) if hasattr(obj, name)]
        return _serialize_fields(names, lambda key: getattr(obj, key), serialize_private_attributes)

    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data using type hints from __init__."""
        sig = inspect.signature(cls.__init__)
        init_params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            
            if param_name in data:
                init_params[param_name] = data[param_name]
            elif param.default != inspect.Parameter.empty:
                # Has default, will be used automatically
                pass
            # If no value and no default, let __init__ raise the error
        
        # Create instance
        instance = cls(**init_params)
        
        # Set any additional attributes not in __init__
        for key, value in data.items():
            if key not in init_params:
                setattr(instance, key, value)
        
        return instance
    
    def priority(self) -> int:
        """TypeHinted resolver has lowest priority."""
        return 25
