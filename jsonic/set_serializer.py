"""Custom serializer/deserializer for set support."""

from jsonic.decorators import jsonic_serializer, jsonic_deserializer


@jsonic_serializer(set)
def serialize_set(obj: set) -> dict:
    """Serialize set to dict with type marker."""
    from jsonic.serializable import serialize
    # Convert to list for JSON serialization, recursively serialize items
    items = [serialize(item) if isinstance(item, (tuple, set)) else item for item in obj]
    return {
        'items': items,
        '_is_set': True
    }


@jsonic_deserializer(set)
def deserialize_set(obj: dict) -> set:
    """Deserialize dict back to set."""
    from jsonic.serializable import deserialize
    # Recursively deserialize all items
    items = [deserialize(item) for item in obj['items']]
    return set(items)
