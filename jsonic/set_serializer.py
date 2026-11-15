"""Custom serializer/deserializer for set support."""

from jsonic.decorators import jsonic_serializer, jsonic_deserializer


@jsonic_serializer(set)
def serialize_set(obj: set) -> dict:
    """Serialize set to dict with type marker."""
    from jsonic.context import current_context
    context = current_context()
    items = [context.serialize(item, i) for i, item in enumerate(obj)]
    return {
        'items': items,
        '_is_set': True
    }


@jsonic_deserializer(set)
def deserialize_set(obj: dict) -> set:
    """Deserialize dict back to set."""
    from jsonic.context import current_context
    context = current_context()
    items = [context.deserialize(item, i) for i, item in enumerate(obj['items'])]
    return set(items)
