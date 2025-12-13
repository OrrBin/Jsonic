"""Custom serializer/deserializer for set support."""

from jsonic.decorators import jsonic_serializer, jsonic_deserializer


@jsonic_serializer(set)
def serialize_set(obj: set) -> dict:
    """Serialize set to dict with type marker."""
    from jsonic.serializable import _preprocess_for_serialization
    # Convert to list for JSON serialization, recursively serialize items
    items = [_preprocess_for_serialization(item, path=f"[{i}]") for i, item in enumerate(obj)]
    return {
        'items': items,
        '_is_set': True
    }


@jsonic_deserializer(set)
def deserialize_set(obj: dict) -> set:
    """Deserialize dict back to set."""
    from jsonic.serializable import deserialize
    # Recursively deserialize all items
    items = [deserialize(item, _path=f"[{i}]") for i, item in enumerate(obj['items'])]
    return set(items)
