"""Custom serializer/deserializer for tuple support."""

from jsonic.decorators import jsonic_serializer, jsonic_deserializer


@jsonic_serializer(tuple)
def serialize_tuple(obj: tuple) -> dict:
    """Serialize tuple to dict with type marker."""
    from jsonic.serializable import serialize
    # Recursively serialize items to handle nested tuples
    items = [serialize(item) if isinstance(item, tuple) else item for item in obj]
    return {
        'items': items,
        '_is_tuple': True
    }


@jsonic_deserializer(tuple)
def deserialize_tuple(obj: dict) -> tuple:
    """Deserialize dict back to tuple."""
    from jsonic.serializable import deserialize
    # Recursively deserialize items to handle nested tuples
    items = [deserialize(item) if isinstance(item, dict) and item.get('_is_tuple') else item 
             for item in obj['items']]
    return tuple(items)
