"""Call-local traversal options and paths shared by built-in adapters."""
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class TraversalContext:
    path: str = ''
    serialize_private_attributes: bool = False
    deserialize_private_attributes: bool = False
    uuid_format: str = 'legacy'
    pydantic_mode: str = 'presentation'
    wire_format: str = 'legacy'

    def child_path(self, key):
        if isinstance(key, int):
            return f'{self.path}[{key}]'
        return f'{self.path}.{key}' if self.path else str(key)

    def serialize(self, value, key):
        """Serialize a child with inherited selection, options and type policy."""
        from jsonic.serializable import _preprocess_for_serialization, _handle_serialization_error, _selection
        path = self.child_path(key)
        token = None
        selection = _selection.get()
        if not isinstance(key, int) and selection is not None:
            child = selection.child(key)
            if child is None:
                # The dispatcher's output filtering removes this field. Do not
                # traverse a value whose selector already excludes it.
                return None
            token = _selection.set(child)
        try:
            return _handle_serialization_error(
                lambda: _preprocess_for_serialization(value, self.serialize_private_attributes, path), path
            )
        finally:
            if token is not None:
                _selection.reset(token)

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


class _SerializationFrame:
    __slots__ = ('value', 'owner', 'active')

    def __init__(self, value, owner):
        self.value, self.owner, self.active = value, owner, True


_serializing = ContextVar('jsonic_active_serialization', default=())
