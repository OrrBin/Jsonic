# wrap Serializer to allow for deferred calling
def serializer(serialized_type):
    """
    Decorator that registers serializer function for a specific type
    serializer function must return the dictionary with string keys.

    the registered function will be used to serialize registered type instances
    when calling ``serialize`` function

    wraps ``_Serializer`` to allow for deferred calling

    Args:
       serialized_type: The type this wrapped function serializes to dictionary

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
        return _Serializer(function, serialized_type)

    return wrapper


def deserializer(deserialized_type_name):
    """
    Decorator that registers deserializer function for a specific type
    deserializer function must return the type it is registered with.

    the registered function will be used to deserialize objects of the registered type
    when calling ``deserialize`` function

    wraps ``_Deserializer`` to allow for deferred calling

    Args:
        deserialized_type_name: The return type of the wrapped deserializer function

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
        return _Deserializer(function, deserialized_type_name)

    return wrapper


class _Serializer:
    serializers = dict()

    def __init__(self, function, serialized_type):
        self.function = function
        _Serializer.serializers[serialized_type] = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class _Deserializer:
    deserializers = dict()

    def __init__(self, function, deserialized_type_name):
        self.function = function

        _Deserializer.deserializers[deserialized_type_name.__name__] = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
