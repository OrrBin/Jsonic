"""Type resolver system for automatic serialization/deserialization based on type hints."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional
import inspect
from jsonic.context import TraversalContext


class TypeResolver(ABC):
    """Base class for type resolvers."""
    
    @abstractmethod
    def can_resolve(self, cls: Type) -> bool:
        """Check if this resolver can handle the given type."""
        pass
    
    @abstractmethod
    def serialize(self, obj: Any, *, context: Optional[TraversalContext] = None) -> Dict[str, Any]:
        """Return a mapping; use optional context.serialize for nested children.

        Existing one-argument implementations and legacy (obj, private_flag)
        implementations remain supported by the public dispatcher.
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any], cls: Type, *, context: Optional[TraversalContext] = None) -> Any:
        """Construct cls from children already decoded by the dispatcher.

        Do not deserialize those children again. Optional context provides the
        current parent path/options for additional adapter-owned traversal.
        """
        pass
    
    @abstractmethod
    def priority(self) -> int:
        """Return priority for resolver selection (higher = higher priority)."""
        pass


class TypeResolverRegistry:
    """Registry for type resolvers with priority-based selection."""
    
    def __init__(self):
        self._resolvers = []
    
    def register(self, resolver: TypeResolver):
        """Register a type resolver."""
        self._resolvers.append(resolver)
        self._resolvers.sort(key=lambda r: r.priority(), reverse=True)
    
    def get_resolver(self, cls: Type) -> Optional[TypeResolver]:
        """Get the highest priority resolver that can handle the type."""
        for resolver in self._resolvers:
            if resolver.can_resolve(cls):
                return resolver
        return None


# Global registry instance
_registry = TypeResolverRegistry()


def register_resolver(resolver: TypeResolver):
    """Register a type resolver in the global registry."""
    _registry.register(resolver)


def get_resolver_for_type(cls: Type) -> Optional[TypeResolver]:
    """Get resolver for a given type from the global registry."""
    return _registry.get_resolver(cls)


def _invoke(method, candidates, context):
    """Choose a supported signature before invoking user code exactly once."""
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        # Opaque/C-backed callables retain the dispatcher's historical call
        # shape. There is no safe way to infer a new protocol or retry them.
        return method(*candidates[0])
    kwargs = {'context': context} if 'context' in signature.parameters else {}
    for args in candidates:
        try:
            signature.bind(*args, **kwargs)
        except TypeError:
            continue
        return method(*args, **kwargs)
    raise TypeError(f'Unsupported resolver signature: {signature}')


def serialize_with_resolver(resolver, obj, context):
    return _invoke(resolver.serialize,
                   [(obj, context.serialize_private_attributes), (obj,)], context)


def deserialize_with_resolver(resolver, data, cls, context):
    return _invoke(resolver.deserialize, [(data, cls)], context)
