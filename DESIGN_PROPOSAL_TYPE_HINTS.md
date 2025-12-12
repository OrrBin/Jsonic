# Design Proposal: Type Hints & Dataclass Support

## Executive Summary

Add native support for Python type hints and dataclasses to enable automatic serialization/deserialization without manual registration, while maintaining full backward compatibility with existing `Serializable` classes.

## Current State Analysis

**Current Limitations:**
1. Requires explicit `Serializable` inheritance or `register_jsonic_type()` calls
2. No automatic field detection from type hints
3. Manual `init_parameters_mapping` for mismatched parameter/attribute names
4. No native dataclass support
5. Type information is lost during serialization (only stored as string)

**Current Strengths:**
1. Simple, explicit API
2. Flexible custom serializers/deserializers
3. Transient attributes support
4. Works with any class structure

## Proposed Solution

### Architecture: Type Resolver Pattern

Introduce a **Type Resolver** abstraction layer that determines how to serialize/deserialize objects based on their type characteristics. This enables extensibility for future integrations (Pydantic, attrs, etc.).

```
┌─────────────────────────────────────────────────┐
│           serialize() / deserialize()           │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              TypeResolverRegistry               │
│  (Checks resolvers in priority order)           │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Custom       │ │Dataclass │ │TypeHinted│ │Serializable│
│ Serializer   │ │ Resolver │ │ Resolver │ │ Resolver  │
│ (existing)   │ │  (new)   │ │  (new)   │ │ (existing)│
└──────────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Benefits

1. **Zero Boilerplate**: Dataclasses work automatically
2. **Type Safety**: Leverage Python's type system
3. **Better IDE Support**: Full autocomplete and type checking
4. **Extensibility**: Easy to add Pydantic/attrs support later
5. **Backward Compatible**: Existing code continues to work
6. **Performance**: Cache type metadata for fast lookups

## Implementation Plan

### Phase 1: Core Infrastructure (Foundation)

**1.1 Create Type Resolver Interface**

```python
# jsonic/resolvers/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Dict

class TypeResolver(ABC):
    """Base interface for type-specific serialization strategies"""
    
    @abstractmethod
    def can_handle(self, obj_or_type: Any) -> bool:
        """Check if this resolver can handle the given object/type"""
        pass
    
    @abstractmethod
    def get_metadata(self, cls: Type) -> 'TypeMetadata':
        """Extract serialization metadata from type"""
        pass
    
    @abstractmethod
    def serialize_instance(self, obj: Any, metadata: 'TypeMetadata') -> Dict:
        """Serialize object using metadata"""
        pass
    
    @abstractmethod
    def deserialize_dict(self, data: Dict, metadata: 'TypeMetadata') -> Any:
        """Deserialize dict to object using metadata"""
        pass


class TypeMetadata:
    """Unified metadata structure for all resolvers"""
    def __init__(self, cls: Type, fields: Dict[str, 'FieldInfo'], 
                 transient: set = None, init_mapping: Dict[str, str] = None):
        self.cls = cls
        self.fields = fields  # field_name -> FieldInfo
        self.transient = transient or set()
        self.init_mapping = init_mapping or {}


class FieldInfo:
    """Information about a single field"""
    def __init__(self, name: str, type_hint: Optional[Type] = None, 
                 default: Any = None, has_default: bool = False):
        self.name = name
        self.type_hint = type_hint
        self.default = default
        self.has_default = has_default
```

**1.2 Create Resolver Registry**

```python
# jsonic/resolvers/registry.py
from typing import List, Optional, Type, Any
from jsonic.resolvers.base import TypeResolver, TypeMetadata

class TypeResolverRegistry:
    """Manages type resolvers in priority order"""
    
    def __init__(self):
        self._resolvers: List[TypeResolver] = []
        self._metadata_cache: Dict[Type, TypeMetadata] = {}
    
    def register(self, resolver: TypeResolver, priority: int = 0):
        """Register resolver (higher priority = checked first)"""
        self._resolvers.append((priority, resolver))
        self._resolvers.sort(key=lambda x: x[0], reverse=True)
    
    def find_resolver(self, obj_or_type: Any) -> Optional[TypeResolver]:
        """Find first resolver that can handle this object/type"""
        for _, resolver in self._resolvers:
            if resolver.can_handle(obj_or_type):
                return resolver
        return None
    
    def get_metadata(self, cls: Type) -> Optional[TypeMetadata]:
        """Get cached metadata or compute it"""
        if cls not in self._metadata_cache:
            resolver = self.find_resolver(cls)
            if resolver:
                self._metadata_cache[cls] = resolver.get_metadata(cls)
        return self._metadata_cache.get(cls)
```

### Phase 2: Implement Resolvers

**2.1 Dataclass Resolver**

```python
# jsonic/resolvers/dataclass_resolver.py
import dataclasses
from typing import Any, Dict, Type, get_type_hints
from jsonic.resolvers.base import TypeResolver, TypeMetadata, FieldInfo

class DataclassResolver(TypeResolver):
    """Handles Python dataclasses"""
    
    def can_handle(self, obj_or_type: Any) -> bool:
        cls = obj_or_type if isinstance(obj_or_type, type) else type(obj_or_type)
        return dataclasses.is_dataclass(cls)
    
    def get_metadata(self, cls: Type) -> TypeMetadata:
        fields = {}
        type_hints = get_type_hints(cls)
        
        for field in dataclasses.fields(cls):
            fields[field.name] = FieldInfo(
                name=field.name,
                type_hint=type_hints.get(field.name),
                default=field.default if field.default is not dataclasses.MISSING else None,
                has_default=field.default is not dataclasses.MISSING
            )
        
        return TypeMetadata(cls=cls, fields=fields)
    
    def serialize_instance(self, obj: Any, metadata: TypeMetadata) -> Dict:
        result = {}
        for field_name, field_info in metadata.fields.items():
            if field_name not in metadata.transient:
                result[field_name] = getattr(obj, field_name)
        return result
    
    def deserialize_dict(self, data: Dict, metadata: TypeMetadata) -> Any:
        init_kwargs = {}
        for field_name in metadata.fields:
            if field_name in data:
                init_kwargs[field_name] = data[field_name]
        return metadata.cls(**init_kwargs)
```

**2.2 Type-Hinted Class Resolver**

```python
# jsonic/resolvers/typehint_resolver.py
import inspect
from typing import Any, Dict, Type, get_type_hints
from jsonic.resolvers.base import TypeResolver, TypeMetadata, FieldInfo

class TypeHintedResolver(TypeResolver):
    """Handles regular classes with type hints"""
    
    def can_handle(self, obj_or_type: Any) -> bool:
        cls = obj_or_type if isinstance(obj_or_type, type) else type(obj_or_type)
        
        # Skip if already handled by other resolvers
        if hasattr(cls, '__dataclass_fields__'):
            return False
        
        # Check if __init__ has type hints
        try:
            hints = get_type_hints(cls.__init__)
            return len(hints) > 1  # More than just 'return'
        except:
            return False
    
    def get_metadata(self, cls: Type) -> TypeMetadata:
        fields = {}
        sig = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, 
                            inspect.Parameter.VAR_KEYWORD):
                continue
            
            fields[param_name] = FieldInfo(
                name=param_name,
                type_hint=type_hints.get(param_name),
                default=param.default if param.default is not inspect.Parameter.empty else None,
                has_default=param.default is not inspect.Parameter.empty
            )
        
        return TypeMetadata(cls=cls, fields=fields)
    
    def serialize_instance(self, obj: Any, metadata: TypeMetadata) -> Dict:
        result = {}
        for field_name in metadata.fields:
            if hasattr(obj, field_name) and field_name not in metadata.transient:
                result[field_name] = getattr(obj, field_name)
        return result
    
    def deserialize_dict(self, data: Dict, metadata: TypeMetadata) -> Any:
        init_kwargs = {}
        for field_name in metadata.fields:
            if field_name in data:
                init_kwargs[field_name] = data[field_name]
        
        instance = metadata.cls(**init_kwargs)
        
        # Set any additional attributes not in __init__
        for key, value in data.items():
            if key not in metadata.fields and not key.startswith('_'):
                setattr(instance, key, value)
        
        return instance
```

**2.3 Legacy Serializable Resolver**

```python
# jsonic/resolvers/serializable_resolver.py
from typing import Any, Dict, Type
from jsonic.resolvers.base import TypeResolver, TypeMetadata, FieldInfo
from jsonic.serializable import Serializable
from jsonic.util import full_type_name

class SerializableResolver(TypeResolver):
    """Handles existing Serializable classes (backward compatibility)"""
    
    def can_handle(self, obj_or_type: Any) -> bool:
        cls = obj_or_type if isinstance(obj_or_type, type) else type(obj_or_type)
        type_name = full_type_name(cls)
        return type_name in Serializable.jsonic_types
    
    def get_metadata(self, cls: Type) -> TypeMetadata:
        type_name = full_type_name(cls)
        jsonic_data = Serializable.jsonic_types[type_name]
        
        # Extract fields from __init__ signature
        import inspect
        sig = inspect.signature(cls.__init__)
        fields = {}
        
        for param_name, param in sig.parameters.items():
            if param_name != 'self':
                fields[param_name] = FieldInfo(name=param_name)
        
        return TypeMetadata(
            cls=cls,
            fields=fields,
            transient=set(jsonic_data.transient_attributes or []),
            init_mapping=jsonic_data.init_parameters_mapping or {}
        )
    
    def serialize_instance(self, obj: Any, metadata: TypeMetadata) -> Dict:
        # Use existing logic
        result = {}
        for key, value in obj.__dict__.items():
            if key not in metadata.transient and not key.startswith('_'):
                result[key] = value
        return result
    
    def deserialize_dict(self, data: Dict, metadata: TypeMetadata) -> Any:
        # Use existing logic with init_mapping
        init_kwargs = {}
        for param_name in metadata.fields:
            attr_name = metadata.init_mapping.get(param_name, param_name)
            if attr_name in data:
                init_kwargs[param_name] = data[attr_name]
        
        instance = metadata.cls(**init_kwargs)
        
        for attr_name, value in data.items():
            setattr(instance, attr_name, value)
        
        return instance
```

### Phase 3: Integration

**3.1 Modify Core Serialization**

```python
# jsonic/serializable.py (modifications)

# Add at module level
_resolver_registry = TypeResolverRegistry()

# Register resolvers in priority order
_resolver_registry.register(SerializableResolver(), priority=100)  # Highest - explicit
_resolver_registry.register(DataclassResolver(), priority=50)
_resolver_registry.register(TypeHintedResolver(), priority=25)

def _serialize_object(obj, serialize_private_attributes=False):
    typ = type(obj)
    
    # Check custom serializers first (existing behavior)
    if typ in _JsonicSerializer.serializers:
        value = _JsonicSerializer.serializers[typ](obj)
        value[SERIALIZED_TYPE_ATTRIBUTE_NAME] = typ.__name__
        return value
    
    # Try resolver registry (NEW)
    resolver = _resolver_registry.find_resolver(obj)
    if resolver:
        metadata = _resolver_registry.get_metadata(typ)
        result = resolver.serialize_instance(obj, metadata)
        result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = full_type_name(typ)
        return result
    
    # Fallback to existing logic for backward compatibility
    elif hasattr(obj, '__dict__'):
        # ... existing code ...
    
    raise TypeError(f'Could not find serializer for type: {typ}')

def _deserialize_jsonic_type_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None):
    type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
    cls = get_type_by_name(type_name)
    
    # Try resolver registry (NEW)
    resolver = _resolver_registry.find_resolver(cls)
    if resolver:
        metadata = _resolver_registry.get_metadata(cls)
        # Recursively deserialize nested objects first
        deserialized_data = {}
        for key, value in obj.items():
            if key == SERIALIZED_TYPE_ATTRIBUTE_NAME:
                continue
            deserialized_data[key] = deserialize(value, deserialize_private_attributes)
        
        return resolver.deserialize_dict(deserialized_data, metadata)
    
    # Fallback to existing logic
    # ... existing code ...
```

**3.2 Add Public API for Extensibility**

```python
# jsonic/__init__.py (additions)

from jsonic.resolvers.registry import TypeResolverRegistry
from jsonic.resolvers.base import TypeResolver

def register_type_resolver(resolver: TypeResolver, priority: int = 0):
    """
    Register a custom type resolver for extensibility.
    
    Args:
        resolver: TypeResolver instance
        priority: Higher priority resolvers are checked first (default: 0)
    
    Example:
        # Future Pydantic support
        register_type_resolver(PydanticResolver(), priority=75)
    """
    _resolver_registry.register(resolver, priority)

__all__ = [
    'serialize', 'deserialize', 'Serializable', 
    'register_jsonic_type', 'jsonic_serializer', 'jsonic_deserializer',
    'register_type_resolver', 'TypeResolver'  # NEW
]
```

### Phase 4: Enhanced Features

**4.1 Generic Type Support**

```python
# jsonic/resolvers/generic_support.py
from typing import get_origin, get_args, List, Dict, Optional

def resolve_generic_type(type_hint, value):
    """Handle List[int], Dict[str, User], Optional[str], etc."""
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    if origin is list and args:
        return [deserialize(item, expected_type=args[0]) for item in value]
    elif origin is dict and args:
        return {k: deserialize(v, expected_type=args[1]) for k, v in value.items()}
    elif origin is Union:  # Optional is Union[X, None]
        # Try each type in union
        for arg in args:
            if arg is type(None) and value is None:
                return None
            try:
                return deserialize(value, expected_type=arg)
            except:
                continue
    
    return value
```

**4.2 Validation Support**

```python
# jsonic/validation.py
from typing import Any, Callable

class ValidationError(Exception):
    """Raised when validation fails"""
    pass

def validate_field(field_name: str, value: Any, type_hint: type) -> Any:
    """Basic type validation"""
    if type_hint and not isinstance(value, type_hint):
        # Try to coerce
        try:
            return type_hint(value)
        except:
            raise ValidationError(
                f"Field '{field_name}' expected {type_hint}, got {type(value)}"
            )
    return value
```

## Migration Path

### For Existing Users (No Changes Required)

```python
# This continues to work exactly as before
class User(Serializable):
    def __init__(self, name: str, id: int):
        super().__init__()
        self.name = name
        self.id = id

user = User("Alice", 1)
serialize(user)  # Works
```

### For New Users (Zero Boilerplate)

```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class User:
    name: str
    id: int
    email: str = "default@example.com"

user = User("Alice", 1)
data = serialize(user)  # Just works!
new_user = deserialize(data, expected_type=User)
```

### For Type-Hinted Classes

```python
class User:
    def __init__(self, name: str, id: int, email: str = "default@example.com"):
        self.name = name
        self.id = id
        self.email = email

user = User("Alice", 1)
serialize(user)  # Automatically detected and handled
```

## Testing Strategy

1. **Backward Compatibility Tests**: Run all existing tests - must pass
2. **Dataclass Tests**: Test all dataclass features (defaults, frozen, etc.)
3. **Type Hint Tests**: Test classes with various type hint patterns
4. **Integration Tests**: Mix old and new styles
5. **Performance Tests**: Ensure no regression
6. **Edge Cases**: Circular refs, complex generics, inheritance

## Performance Considerations

1. **Metadata Caching**: Cache type metadata to avoid repeated introspection
2. **Lazy Resolution**: Only resolve types when first encountered
3. **Fast Path**: Custom serializers bypass resolver system
4. **Benchmark Target**: <10% overhead vs current implementation

## Future Extensibility

This design enables easy addition of:

```python
# Future: Pydantic support
class PydanticResolver(TypeResolver):
    def can_handle(self, obj_or_type):
        return isinstance(obj_or_type, BaseModel)
    # ... implement methods

register_type_resolver(PydanticResolver(), priority=75)

# Future: attrs support
class AttrsResolver(TypeResolver):
    def can_handle(self, obj_or_type):
        return attr.has(obj_or_type)
    # ... implement methods

register_type_resolver(AttrsResolver(), priority=60)
```

## Implementation Timeline

- **Week 1**: Phase 1 (Infrastructure) + Tests
- **Week 2**: Phase 2 (Resolvers) + Tests  
- **Week 3**: Phase 3 (Integration) + Backward compatibility tests
- **Week 4**: Phase 4 (Enhanced features) + Documentation
- **Week 5**: Performance optimization + Final testing

## Success Metrics

1. All existing tests pass without modification
2. Dataclasses work with zero configuration
3. Type-hinted classes work automatically
4. <10% performance overhead
5. Clear migration path documented
6. Extensibility proven with example resolver

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes | High | Comprehensive test suite, resolver priority system |
| Performance regression | Medium | Caching, benchmarks, fast paths |
| Complex edge cases | Medium | Incremental rollout, extensive testing |
| Type hint limitations | Low | Fallback to existing behavior |

## Conclusion

This design provides a clean, extensible foundation for modern Python serialization while maintaining 100% backward compatibility. The resolver pattern enables future integrations (Pydantic, attrs) without core changes, and the metadata caching ensures performance remains competitive.
