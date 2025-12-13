"""Custom serializer/deserializer for tuple support."""

from jsonic.decorators import jsonic_serializer, jsonic_deserializer


@jsonic_serializer(tuple)
def serialize_tuple(obj: tuple) -> dict:
    """Serialize tuple to dict with type marker."""
    from jsonic.serializable import _preprocess_for_serialization
    # Recursively serialize items to handle nested objects
    items = [_preprocess_for_serialization(item, path=f"[{i}]") for i, item in enumerate(obj)]
    return {
        'items': items,
        '_is_tuple': True
    }


@jsonic_deserializer(tuple)
def deserialize_tuple(obj: dict) -> tuple:
    """Deserialize dict back to tuple."""
    from jsonic.serializable import deserialize
    # Recursively deserialize all items
    items = [deserialize(item, _path=f"[{i}]") for i, item in enumerate(obj['items'])]
    return tuple(items)
