import inspect
import json
from typing import List, Dict

from serialization.decorators import _Serializer, _Deserializer
from serialization.util import full_type_name

SERIALIZED_TYPE_ATTRIBUTE_NAME = '_serialized_type'


class SerializableTypeData:
    """
    Class holding meta-data used for serializing and deserializing for a specific type

    Attributes:
        cls (type): The serializable type
        transient_attributes (List[str]): list of attribute names that won't be serialized and deserialized
        init_parameters_mapping: (Dict[str, str]): mapping from __init__ parameter name to it's matching instance attribute
    """

    def __init__(self, cls: type, transient_attributes: List[str] = None,
                 init_parameters_mapping: Dict[str, str] = None):
        if transient_attributes is None:
            transient_attributes = []
        if init_parameters_mapping is None:
            init_parameters_mapping = {}
        self.cls = cls
        self.transient_attributes = transient_attributes
        self.init_parameters_mapping = init_parameters_mapping


class Serializable:
    """
    Classes extending this class can be serialized into json dict/string representing the object,
    and deserialized back to class instance.
    Extending classes that needs to declare some attributes as transient, should have
    class attribute:
        transient_attributes: List[str]
    which should be a list of attributes names that would be transient (won't be serialized and deserialized)

    Classes that has __init__ parameter with a different name that it's corresponding instance attribute should have class attribute:
        init_parameters_mapping: Dict[str, str]
    which should be a dictionary mapping from __init__ parameter name to the corresponding instance attribute name.
    When deserializing class instance, the corresponding instance attribute will be passed to the __init__ function.
    For __init__ parameter which has no mapping defined, it is assumed that the corresponding instance variable has
    the same name as the parameter.


    Note:
        If nested objects exists in such class, their type should be one of the following:
            1. Implement Serializable
            2. Be registered using the register_serializable_type function
    """

    serializable_types: Dict[str, SerializableTypeData] = {}
    transient_attributes: List[str] = None
    init_parameters_mapping: Dict[str, str] = None

    def __init__(self) -> None:
        super().__init__()

    def __init_subclass__(cls) -> None:
        register_serializable_type(cls, cls.transient_attributes, cls.init_parameters_mapping)


def serialize(obj, serialize_private_attributes=False, string_output=False):
    """
     Serializes ``object`` / ``class instance`` / ``dict`` / ``list`` into ``dictionary`` / ``json string`` representing the input

    Args:
        obj: ``object`` / ``class instance`` / ``dict`` / ``list`` to be serializes
        serialize_private_attributes: should serialize private attributes (attributes which their name starts with ``_``)
        string_output: serialize into json string or ``dict`` / ``list

    Returns:
        ``dictionary`` / ``json string`` representing the input

    Note:
        Only class instances of classes extending ``Serializable`` or registered using ``register_serializable_type`` can be serialized
    """
    json_str = json.dumps(obj, default=lambda o: _serialize_object(o, serialize_private_attributes))
    return json_str if string_output else json.loads(json_str)


def deserialize(obj, deserialize_private_attributes: bool = False, string_input: bool = False, expected_type: type = None):
    """
    Deserializes dictionary/json string representing dictionary, that was returned by ``serialize`` function call on an object

    Args:
        obj: dictionary/json string representing dictionary, that is a result of ``serialize`` function on an object
        deserialize_private_attributes (bool): should deserialize private attributes (attributes which their name starts with ``_``)
        string_input (bool): is the input of type ``json string``, or ``dict``
        expected_type: the deserialized result expected type
    Returns:
        object / class instance / dict / list, depending on the serialized input

    Raises:
        AttributeError: When the serialized type is different from the expected type
    """
    if string_input:
        if type(obj) != str:
            raise TypeError(f'deserializing string, but input was not of type str. given input: {obj}')
        return deserialize(json.loads(obj), expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes)

    if type(obj) == list:
        return _deserialize_list(obj, expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes)
    elif type(obj) == dict:
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj and obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] in _Deserializer.deserializers:
            # There is custom deserializer for given objects serialized type, so use it
            return _deserialize_with_custom_deserializer(obj, expected_type=expected_type)
        return _deserialize_dict(obj, expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes)
    else:
        return obj


def register_serializable_type(cls, transient_attributes: List[str] = None,
                               init_parameters_mapping: Dict[str, str] = None):
    """
    Registers serializable type with it's metadata.
    Can be used to register classes that doesn't extend ``Serializable``, from example classes from external source.
    Only registered classes or classes extending ``Serializable`` can be serialized using ``serialize`` function
    and deserialized using ``deserialized`` function

    Args:
        cls (type):
        transient_attributes (List[str]): list of attribute names that won't be serialized and deserialized
        init_parameters_mapping: (Dict[str, str]): mapping from __init__ parameter name to it's matching instance attribute
    """
    class_name = full_type_name(cls)
    Serializable.serializable_types[class_name] = SerializableTypeData(cls, transient_attributes,
                                                                       init_parameters_mapping)


def _serialize_object(obj, serialize_private_attributes=False):
    typ = type(obj)
    if typ in _Serializer.serializers:
        value = _Serializer.serializers[typ](obj)
        value[SERIALIZED_TYPE_ATTRIBUTE_NAME] = typ.__name__
        return value

    elif hasattr(obj, '__dict__'):
        type_name = full_type_name(typ)
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

        setattr(obj, SERIALIZED_TYPE_ATTRIBUTE_NAME, full_type_name(typ))
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = value
        for key, val in ignored_attributes.items():
            setattr(obj, key, val)

        return result

    raise TypeError(f'Could not find serializer for type: {typ}')


def _deserialize_with_custom_deserializer(obj, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        if expected_type and full_type_name(expected_type) != type_name:
            raise AttributeError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}')
        if type_name in _Deserializer.deserializers:
            del obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
            result = _Deserializer.deserializers[type_name](obj)
            obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
            return result

        raise TypeError(f'Could not find custom deserializer for object with type tag: {type_name}')

    raise TypeError(f'Missing attribute _serialized_type for object: {obj}')


def _deserialize_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        return _deserialize_serializable_type_dict(obj, deserialize_private_attributes=deserialize_private_attributes,
                                                   expected_type=expected_type)

    return _deserialize_generic_dict(obj, deserialize_private_attributes=deserialize_private_attributes, expected_type=expected_type)


def _deserialize_generic_dict(obj: dict, deserialize_private_attributes: bool = False, expected_type: type = None):
    if expected_type and expected_type != dict:
        raise AttributeError(f'Deserializing type dict, which is not the expected type: {expected_type}')

    deserialized_dict = {}

    for key, value in obj.items():
        if (type(value) == dict and SERIALIZED_TYPE_ATTRIBUTE_NAME in value) or type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        elif type(value) == dict:  # value is is a dict but not serializable type dict
            deserialized_dict[key] = _deserialize_generic_dict(value, deserialize_private_attributes=deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    return deserialized_dict


def _deserialize_serializable_type_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME not in obj:
        raise TypeError(f'Deserializing dict of serializable type but could not find {SERIALIZED_TYPE_ATTRIBUTE_NAME} attribute')

    type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
    cls = Serializable.serializable_types[type_name].cls

    if expected_type and full_type_name(expected_type) != type_name:
        raise AttributeError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}')

    deserialized_dict = {}

    for key, value in obj.items():
        if key == SERIALIZED_TYPE_ATTRIBUTE_NAME:
            pass
        elif not deserialize_private_attributes and key.startswith('_'):
            pass
        elif type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        elif type(value) == dict and SERIALIZED_TYPE_ATTRIBUTE_NAME in value:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    init_dict = {}

    sign = inspect.signature(cls.__init__)

    init_parameters_mapping = Serializable.serializable_types[type_name].init_parameters_mapping

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


def _deserialize_list(lst: list, deserialize_private_attributes=False, expected_type: type = None):
    if expected_type and expected_type != list:
        raise AttributeError(f'Deserializing list, which is not the expected type: {expected_type}')
    deserialized_list = []
    for element in lst:
        deserialized_list.append(deserialize(element, deserialize_private_attributes=deserialize_private_attributes))

    return deserialized_list
