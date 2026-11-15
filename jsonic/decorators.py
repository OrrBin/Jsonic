from jsonic.util import full_type_name

# wrap Serializer to allow for deferred calling
def jsonic_serializer(serialized_type, *, type_id=None):
    """
    Decorator that registers serializer function for a specific type
    serializer function must return the dictionary with string keys.

    the registered function will be used to serialize registered type instances
    when calling ``serialize`` function

    wraps ``_Serializer`` to allow for deferred calling

    Args:
       serialized_type: The type this wrapped function serializes to dictionary
       type_id: Optional stable wire ID; use the same ID on its decoder.

    Note:
       If multiple serializer functions are registered for the same type, only last one to be registered
       will have an effect.

    Example:
       Usage example for type datetime:

           @serializer(serialized_type=datetime)
            def serialize_datetime(datetime_obj):
            return {'datetime': datetime_obj.__str__()}
   """

    def wrapper(function):
        return _JsonicSerializer(function, serialized_type, type_id)

    return wrapper


def jsonic_deserializer(deserialized_type_name, *, type_id=None, aliases=()):
    """
    Decorator that registers deserializer function for a specific type
    deserializer function must return the type it is registered with.

    the registered function will be used to deserialize objects of the registered type
    when calling ``deserialize`` function

    wraps ``_Deserializer`` to allow for deferred calling

    Args:
        deserialized_type_name: The return type of the wrapped deserializer function
        type_id: Optional stable wire ID; defaults to the legacy short name.
        aliases: Explicit additional IDs accepted when decoding older data.

    Note:
        If multiple deserializer functions are registered for the same type, only last one to be registered
        will have an effect.

    Example:
        Usage example for type datetime:

            @deserializer(deserialized_type_name=datetime)
            def deserialize_datetime(serialized_datetime):
                return datetime.fromisoformat(serialized_datetime['datetime'])
    """

    def wrapper(function):
        return _JsonicDeserializer(function, deserialized_type_name, type_id, aliases)

    return wrapper


class _JsonicSerializer:
    serializers = dict()
    type_ids = dict()
    types = dict()

    def __init__(self, function, serialized_type, type_id=None):
        if not isinstance(serialized_type, type):
            raise TypeError("jsonic_serializer requires a Python type")
        if type_id is not None and (not isinstance(type_id, str) or not type_id):
            raise ValueError("type_id must be a nonempty string")
        tags = {full_type_name(serialized_type), type_id or serialized_type.__name__}
        for tag in tags:
            for registry in (self.types, _JsonicDeserializer.types):
                if tag in registry and registry[tag] is not serialized_type:
                    raise ValueError(f"Ambiguous codec type ID: {tag!r}; use an explicit unique type_id")
        self.function = function
        _JsonicSerializer.serializers[serialized_type] = function
        _JsonicSerializer.type_ids[serialized_type] = type_id or serialized_type.__name__
        for tag in tags:
            self.types[tag] = serialized_type

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class _JsonicDeserializer:
    deserializers = dict()
    types = dict()

    def __init__(self, function, deserialized_type_name, type_id=None, aliases=()):
        typ = deserialized_type_name
        if not isinstance(typ, type):
            raise TypeError("jsonic_deserializer requires a Python type")
        if type_id is not None and (not isinstance(type_id, str) or not type_id):
            raise ValueError("type_id must be a nonempty string")
        tags = {full_type_name(typ), type_id or typ.__name__, *aliases}
        for tag in tags:
            if not isinstance(tag, str) or not tag:
                raise ValueError("type IDs and aliases must be nonempty strings")
            for registry in (self.types, _JsonicSerializer.types):
                existing = registry.get(tag)
                if existing is not None and existing is not typ:
                    raise ValueError(f"Ambiguous codec type ID: {tag!r}; use an explicit unique type_id")
        self.function = function
        for tag in tags:
            self.deserializers[tag] = function
            self.types[tag] = typ

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
