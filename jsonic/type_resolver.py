"""Type resolver system for automatic serialization/deserialization based on type hints."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional


class TypeResolver(ABC):
    """Base class for type resolvers."""
    
    @abstractmethod
    def can_resolve(self, cls: Type) -> bool:
        """Check if this resolver can handle the given type."""
        pass
    
    @abstractmethod
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize an object of the resolved type."""
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any], cls: Type) -> Any:
        """Deserialize data into an instance of the resolved type."""
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
