"""Type resolvers for automatic serialization/deserialization."""

from jsonic.resolvers.dataclass_resolver import DataclassResolver
from jsonic.resolvers.typehinted_resolver import TypeHintedResolver

__all__ = ['DataclassResolver', 'TypeHintedResolver']
