import json
from datetime import datetime


class Serializable:
    """
    Classes extending this class can be serialized into dict representing the object,
    and deserialized back to class instance.
    If nested objects exists in such class, they should be one of the following:
    1. Implement Serializable
    2. Be registered using the register_serializable_type function
    """

    serializable_types = {}

    def __init__(self, **kwargs) -> None:
        super().__init__()

    def __init_subclass__(cls) -> None:
        register_serializable_type(cls)

    @classmethod
    def serialize_object(cls, obj, serialize_private_attributes=False):
        typ = type(obj)
        if typ in Serializer.serializers:
            value = Serializer.serializers[typ](obj)
            value['_serialized_type'] = typ.__name__
            return value

        elif hasattr(obj, '__dict__'):
            private_attributes = {}
            if not serialize_private_attributes:
                to_remove = [key for key in obj.__dict__.keys() if key.startswith('_')]
                for key in to_remove:
                    private_attributes[key] = getattr(obj, key)
                    delattr(obj, key)
            setattr(obj, '_serialized_type', fullname(typ))
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = value
            for key, val in private_attributes.items():
                setattr(obj, key, val)

            return result

        raise TypeError(f'Could not find serializer for type: {typ}')


def register_serializable_type(cls):
    class_name = fullname(cls)
    Serializable.serializable_types[class_name] = cls


def serialize(obj, serialize_private_attributes=False):
    json_str = json.dumps(obj, default=lambda o: Serializable.serialize_object(o, serialize_private_attributes))
    return json.loads(json_str)


def deserialize(obj, deserialize_private_attributes=False):
    if type(obj) == list:
        return deserialize_list(obj, deserialize_private_attributes)
    elif type(obj) == dict:
        return deserialize_dict(obj, deserialize_private_attributes)
    else:
        return obj


def deserialize_dict(obj: dict, deserialize_private_attributes=False):
    deserialized_dict = {}

    if '_serialized_type' in obj:
        type_name = obj['_serialized_type']
        if type_name in Deserializer.deserializers:
            del obj['_serialized_type']
            result = Deserializer.deserializers[type_name](obj)
            obj['_serialized_type'] = type_name
            return result

    for key, value in obj.items():
        if key == '_serialized_type':
            pass
        elif not deserialize_private_attributes and key.startswith('_'):
            pass
        elif type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes)
        elif type(value) == dict and '_serialized_type' in value:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    class_name = obj['_serialized_type']
    cls = Serializable.serializable_types[class_name]
    return cls(**deserialized_dict)


def deserialize_list(lst: list, deserialize_private_attributes=False):
    deserialized_list = []
    for element in lst:
        deserialized_list.append(deserialize(element, deserialize_private_attributes))

    return deserialized_list


def fullname(o):
    module = o.__module__
    if module is None or module == str.__class__.__module__:
        return o.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__name__


class Serializer:
    serializers = dict()

    def __init__(self, function, serialized_type):
        self.function = function
        Serializer.serializers[serialized_type] = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


# wrap Serializer to allow for deferred calling
def serializer(serialized_type):
    def wrapper(function):
        return Serializer(function, serialized_type)

    return wrapper


class Deserializer:
    f"""
    Decorator that registers deserializer function for a specific type
    deserializer function must return the type it is registered with.
    
    the registered function will be used to deserialize objects of the registered type 
    when calling Serializable.deserialize
    
    If multiple deserializer functions are registered for the same type, only last one to be registered
    will have an effect.

    Usage example for type datetime:
    @deserializer(deserialized_type_name=datetime)
    def deserialize_datetime(serialized_datetime):
        return datetime.fromisoformat(serialized_datetime['datetime'])
    """
    deserializers = dict()

    def __init__(self, function, deserialized_type_name):
        self.function = function

        if deserialized_type_name.__name__ in Deserializer.deserializers:
            raise

        Deserializer.deserializers[deserialized_type_name.__name__] = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def deserializer(deserialized_type_name):
    """
    wrap Deserializer to allow for deferred calling
    :param deserialized_type_name: The return type of the wrapped function
    """

    def wrapper(function):
        return Deserializer(function, deserialized_type_name)

    return wrapper


@serializer(serialized_type=datetime)
def serialize_datetime(datetime_obj):
    return {'datetime': datetime_obj.__str__()}


@deserializer(deserialized_type_name=datetime)
def deserialize_datetime(serialized_datetime):
    return datetime.fromisoformat(serialized_datetime['datetime'])
