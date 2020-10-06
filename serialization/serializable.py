import json
from datetime import datetime
from typing import List, Dict
import inspect

SERIALIZED_TYPE_ATTRIBUTE_NAME = '_serialized_type'


class SerializableTypeData:
    def __init__(self, cls: type, transient_attributes=None, init_parameters_mapping=None):
        if transient_attributes is None:
            transient_attributes = []
        if init_parameters_mapping is None:
            init_parameters_mapping = {}
        self.cls = cls
        self.transient_attributes = transient_attributes
        self.init_parameters_mapping = init_parameters_mapping


class Serializable:
    """
    Classes extending this class can be serialized into dict representing the object,
    and deserialized back to class instance.
    If nested objects exists in such class, they should be one of the following:
    1. Implement Serializable
    2. Be registered using the register_serializable_type function
    """

    serializable_types: Dict[str, SerializableTypeData] = {}
    transient_attributes: List[str] = None
    init_parameters_mapping: Dict[str, str] = None

    def __init__(self, **kwargs) -> None:
        super().__init__()

    def __init_subclass__(cls) -> None:
        register_serializable_type(cls, cls.transient_attributes, cls.init_parameters_mapping)

    @classmethod
    def serialize_object(cls, obj, serialize_private_attributes=False):
        typ = type(obj)
        if typ in Serializer.serializers:
            value = Serializer.serializers[typ](obj)
            value[SERIALIZED_TYPE_ATTRIBUTE_NAME] = typ.__name__
            return value

        elif hasattr(obj, '__dict__'):
            type_name = fullname(typ)
            if type_name not in Serializable.serializable_types:
                raise TypeError(f'Could not find registered serializable type with name: {type_name}')

            type_data = Serializable.serializable_types[type_name]
            ignored_attributes = {}

            if not serialize_private_attributes:  # Do not serialize private attributes
                to_remove = [key for key in obj.__dict__.keys() if key.startswith('_')]
                for key in to_remove:
                    ignored_attributes[key] = getattr(obj, key)
                    delattr(obj, key)

            if type_data.transient_attributes:  # Do not serialize transient attributes
                to_remove = [key for key in obj.__dict__.keys() if key in type_data.transient_attributes]
                for key in to_remove:
                    ignored_attributes[key] = getattr(obj, key)
                    delattr(obj, key)

            setattr(obj, SERIALIZED_TYPE_ATTRIBUTE_NAME, fullname(typ))
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = value
            for key, val in ignored_attributes.items():
                setattr(obj, key, val)

            return result

        raise TypeError(f'Could not find serializer for type: {typ}')


def serialize(obj, serialize_private_attributes=False):
    json_str = json.dumps(obj, default=lambda o: Serializable.serialize_object(o, serialize_private_attributes))
    return json.loads(json_str)


def register_serializable_type(cls, transient_attributes: List[str] = None,
                               init_parameters_mapping: Dict[str, str] = None):
    class_name = fullname(cls)
    Serializable.serializable_types[class_name] = SerializableTypeData(cls, transient_attributes,
                                                                       init_parameters_mapping)


def deserialize(obj, deserialize_private_attributes=False):
    if type(obj) == list:
        return deserialize_list(obj, deserialize_private_attributes)
    elif type(obj) == dict:
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj and obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] in Deserializer.deserializers:
            # There is custom deserializer for given objects serialized type, so use it
            return deserialize_with_custom_deserializer(obj)
        return deserialize_dict(obj, deserialize_private_attributes)
    else:
        return obj


def deserialize_with_custom_deserializer(obj):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        if type_name in Deserializer.deserializers:
            del obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
            result = Deserializer.deserializers[type_name](obj)
            obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
            return result

        raise TypeError('Could not find custom deserializer')

    raise TypeError('Missing attribute _serialized_type')


def deserialize_dict(obj: dict, deserialize_private_attributes=False):
    deserialized_dict = {}

    for key, value in obj.items():
        if key == SERIALIZED_TYPE_ATTRIBUTE_NAME:
            pass
        elif not deserialize_private_attributes and key.startswith('_'):
            pass
        elif type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes)
        elif type(value) == dict and SERIALIZED_TYPE_ATTRIBUTE_NAME in value:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    class_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
    cls = Serializable.serializable_types[class_name].cls

    init_dict = {}

    sign = inspect.signature(cls.__init__)

    init_parameters_mapping = Serializable.serializable_types[class_name].init_parameters_mapping

    for parameter_name, parameter_data in sign.parameters.items():
        if not deserialize_private_attributes and parameter_name.startswith('_'):
            continue
        if parameter_name == 'self':
            pass
        elif parameter_data.kind == inspect.Parameter.VAR_KEYWORD or \
                parameter_data.kind == inspect.Parameter.VAR_POSITIONAL:
            pass
        elif parameter_name in init_parameters_mapping:
            init_dict[parameter_name] = deserialized_dict[init_parameters_mapping[parameter_name]]
        else:  # assuming parameter has same name as corresponding attribute
            init_dict[parameter_name] = deserialized_dict[parameter_name]

    attributes_not_to_constructor = {}
    for candidate in deserialized_dict.keys():
        if candidate not in sign.parameters:
            attributes_not_to_constructor[candidate] = deserialized_dict[candidate]

    created_instance = cls(**init_dict)
    for attr_name, attr_value in attributes_not_to_constructor.items():
        setattr(created_instance, attr_name, attr_value)

    return created_instance


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
    """
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
