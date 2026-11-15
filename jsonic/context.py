"""Call-local traversal options and paths shared by built-in adapters."""
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class TraversalContext:
    path: str = ''
    serialize_private_attributes: bool = False
    deserialize_private_attributes: bool = False

    def child_path(self, key):
        if isinstance(key, int):
            return f'{self.path}[{key}]'
        return f'{self.path}.{key}' if self.path else str(key)

    def serialize(self, value, key):
        """Serialize a child with inherited selection, options and type policy."""
        from jsonic.serializable import _preprocess_for_serialization, _handle_serialization_error
        path = self.child_path(key)
        return _handle_serialization_error(
            lambda: _preprocess_for_serialization(value, self.serialize_private_attributes, path), path
        )

    def deserialize(self, value, key):
        """Decode a child without relaxing the active safe-mode policy."""
        from jsonic.serializable import deserialize, _handle_deserialization_error
        path = self.child_path(key)
        return _handle_deserialization_error(
            lambda: deserialize(value, deserialize_private_attributes=self.deserialize_private_attributes,
                                _path=path), path
        )


_traversal = ContextVar('jsonic_traversal', default=TraversalContext())


def current_context():
    return _traversal.get()
