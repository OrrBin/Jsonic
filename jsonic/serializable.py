import importlib
import inspect
import json
from enum import Enum
from typing import List, Dict

from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer
from jsonic.util import full_type_name, is_private_attribute

SERIALIZED_TYPE_ATTRIBUTE_NAME = '_serialized_type'


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum types"""
    def encode(self, obj):
        # Pre-process to convert all enums before encoding
        obj = self._convert_enums(obj)
        return super().encode(obj)
    
    def _convert_enums(self, obj):
        """Recursively convert all enum instances"""
        if isinstance(obj, Enum):
            return {
                'name': obj.name,
                'value': obj.value,
                SERIALIZED_TYPE_ATTRIBUTE_NAME: full_type_name(type(obj))
            }
        elif isinstance(obj, dict):
            return {k: self._convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_enums(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_enums(item) for item in obj)
        return obj
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return {
                'name': obj.name,
                'value': obj.value,
                SERIALIZED_TYPE_ATTRIBUTE_NAME: full_type_name(type(obj))
            }
        return super().default(obj)


class JsonicTypeData:
    """
    Class holding meta-data used for serializing and deserializing for a specific type

    Attributes:
        cls (type): The jsonic type
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
            2. Be registered using the register_jsonic_type function
    """

    jsonic_types: Dict[str, JsonicTypeData] = {}
    transient_attributes: List[str] = None
    init_parameters_mapping: Dict[str, str] = None

    def __init__(self) -> None:
        super().__init__()

    def __init_subclass__(cls) -> None:
        register_jsonic_type(cls, cls.transient_attributes, cls.init_parameters_mapping)


def serialize(obj, serialize_private_attributes=False, string_output=False):
    """
     Serializes ``class instance`` / ``dict`` / ``list`` / ``other python type`` into ``dictionary`` / ``json string`` representing the input

    Args:
        obj: ``object`` / ``class instance`` / ``dict`` / ``list`` to be serializes
        serialize_private_attributes: should serialize private attributes (attributes which their name starts with ``_``)
        string_output: serialize into json string or ``dict`` / ``list

    Returns:
        ``dictionary`` / ``json string`` representing the input

    Note:
        Only class instances of classes extending ``Serializable`` or registered using ``register_jsonic_type`` can be serialized
    """
    # Pre-process tuples recursively
    obj = _preprocess_tuples(obj, serialize_private_attributes)
    
    # Use custom encoder that handles nested enums
    json_str = json.dumps(obj, cls=EnumEncoder, default=lambda o: _serialize_object(o, serialize_private_attributes))
    return json_str if string_output else json.loads(json_str)


def _preprocess_tuples(obj, serialize_private_attributes=False):
    """Recursively convert tuples and sets to serializable dict format."""
    if isinstance(obj, (tuple, set)):
        return _serialize_object(obj, serialize_private_attributes)
    elif isinstance(obj, list):
        return [_preprocess_tuples(item, serialize_private_attributes) for item in obj]
    elif isinstance(obj, dict):
        return {k: _preprocess_tuples(v, serialize_private_attributes) for k, v in obj.items()}
    elif isinstance(obj, Enum):
        return _serialize_object(obj, serialize_private_attributes)
    return obj


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
        # Check for tuple/set markers first
        if obj.get('_is_tuple') and 'tuple' in _JsonicDeserializer.deserializers:
            return _JsonicDeserializer.deserializers['tuple'](obj)
        if obj.get('_is_set') and 'set' in _JsonicDeserializer.deserializers:
            return _JsonicDeserializer.deserializers['set'](obj)
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj and obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] in _JsonicDeserializer.deserializers:
            # There is custom deserializer for given objects serialized type, so use it
            return _deserialize_with_custom_deserializer(obj, expected_type=expected_type)
        return _deserialize_dict(obj, expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes)
    else:
        return obj


def register_jsonic_type(cls, transient_attributes: List[str] = None,
                         init_parameters_mapping: Dict[str, str] = None):
    """
    Registers jsonic type with it's metadata.
    Can be used to register classes that doesn't extend ``Serializable``, from example classes from external source.
    Only registered classes, classes extending ``Serializable`` or classes that a custom serializer and deserializer were registered for
    can be serialized using ``serialize`` function and deserialized using ``deserialized`` function

    Args:
        cls (type):
        transient_attributes (List[str]): list of attribute names that won't be serialized and deserialized
        init_parameters_mapping: (Dict[str, str]): mapping from __init__ parameter name to it's matching instance attribute
    """
    class_name = full_type_name(cls)
    Serializable.jsonic_types[class_name] = JsonicTypeData(cls, transient_attributes,
                                                           init_parameters_mapping)


def _serialize_object(obj, serialize_private_attributes=False):
    typ = type(obj)
    
    # Check if it's an Enum
    if isinstance(obj, Enum):
        return {
            'name': obj.name,
            'value': obj.value,
            SERIALIZED_TYPE_ATTRIBUTE_NAME: full_type_name(typ)
        }
    
    # Priority 1: Custom serializers (100)
    if typ in _JsonicSerializer.serializers:
        value = _JsonicSerializer.serializers[typ](obj)
        value[SERIALIZED_TYPE_ATTRIBUTE_NAME] = typ.__name__
        return value

    # Priority 2: Serializable types (100)
    type_name = full_type_name(typ)
    is_jsonic_type = type_name in Serializable.jsonic_types
    
    if is_jsonic_type:
        type_data = Serializable.jsonic_types[type_name]
        ignored_attributes = {}
        
        # Handle both __dict__ and __slots__
        # If __dict__ exists but is empty and __slots__ exists, use __slots__
        has_dict = hasattr(obj, '__dict__') and len(obj.__dict__) > 0
        has_slots = hasattr(obj, '__slots__')
        
        if has_dict:
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

            setattr(obj, SERIALIZED_TYPE_ATTRIBUTE_NAME, type_name)
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, Enum):
                    result[key] = _serialize_object(value, serialize_private_attributes)
                elif isinstance(value, (tuple, set)):
                    result[key] = _serialize_object(value, serialize_private_attributes)
                else:
                    result[key] = value
            for key, val in ignored_attributes.items():
                setattr(obj, key, val)

            return result
        elif has_slots:
            # Handle __slots__ for Serializable
            result = {SERIALIZED_TYPE_ATTRIBUTE_NAME: type_name}
            slots = _get_all_slots(typ)
            for slot in slots:
                if hasattr(obj, slot):
                    # Skip private and transient attributes
                    if not serialize_private_attributes and slot.startswith('_'):
                        continue
                    if type_data.transient_attributes and slot in type_data.transient_attributes:
                        continue
                    
                    value = getattr(obj, slot)
                    if isinstance(value, Enum):
                        result[slot] = _serialize_object(value, serialize_private_attributes)
                    elif isinstance(value, (tuple, set)):
                        result[slot] = _serialize_object(value, serialize_private_attributes)
                    else:
                        result[slot] = value
            return result
    
    # Priority 3: Type resolvers (dataclass=50, typehinted=25)
    from jsonic.type_resolver import get_resolver_for_type
    resolver = get_resolver_for_type(typ)
    if resolver:
        result = resolver.serialize(obj, serialize_private_attributes)
        result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
        return result
    
    # Fallback: Generic object with __dict__ or __slots__
    if hasattr(obj, '__dict__'):
        setattr(obj, SERIALIZED_TYPE_ATTRIBUTE_NAME, type_name)
        result = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes if requested (but not _serialized_type)
            if not serialize_private_attributes and key.startswith('_') and key != SERIALIZED_TYPE_ATTRIBUTE_NAME:
                continue
            if isinstance(value, Enum):
                result[key] = _serialize_object(value, serialize_private_attributes)
            elif isinstance(value, (tuple, set)):
                result[key] = _serialize_object(value, serialize_private_attributes)
            else:
                result[key] = value
        return result
    elif hasattr(obj, '__slots__'):
        # Handle __slots__ classes
        result = {SERIALIZED_TYPE_ATTRIBUTE_NAME: type_name}
        slots = _get_all_slots(typ)
        for slot in slots:
            if hasattr(obj, slot):
                # Skip private attributes if requested
                if not serialize_private_attributes and slot.startswith('_'):
                    continue
                value = getattr(obj, slot)
                if isinstance(value, Enum):
                    result[slot] = _serialize_object(value, serialize_private_attributes)
                elif isinstance(value, (tuple, set)):
                    result[slot] = _serialize_object(value, serialize_private_attributes)
                else:
                    result[slot] = value
        return result

    raise TypeError(f'Could not find serializer for type: {typ}')


def _get_all_slots(cls):
    """Get all __slots__ from a class and its bases."""
    slots = []
    for c in cls.__mro__:
        if hasattr(c, '__slots__'):
            c_slots = c.__slots__
            # __slots__ can be a string, list, or tuple
            if isinstance(c_slots, str):
                slots.append(c_slots)
            else:
                slots.extend(c_slots)
    return slots


def _deserialize_with_custom_deserializer(obj, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        if expected_type and full_type_name(expected_type) != type_name:
            raise AttributeError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}')
        if type_name in _JsonicDeserializer.deserializers:
            del obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
            result = _JsonicDeserializer.deserializers[type_name](obj)
            obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
            return result

        raise TypeError(f'Could not find custom deserializer for object with type tag: {type_name}')

    raise TypeError(f'Missing attribute _serialized_type for object: {obj}')


def _deserialize_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        return _deserialize_jsonic_type_dict(obj, deserialize_private_attributes=deserialize_private_attributes,
                                             expected_type=expected_type)

    return _deserialize_generic_dict(obj, deserialize_private_attributes=deserialize_private_attributes, expected_type=expected_type)


def _deserialize_generic_dict(obj: dict, deserialize_private_attributes: bool = False, expected_type: type = None):
    if expected_type and expected_type != dict:
        raise AttributeError(f'Deserializing type dict, which is not the expected type: {expected_type}')

    deserialized_dict = {}

    for key, value in obj.items():
        if type(value) == dict and (SERIALIZED_TYPE_ATTRIBUTE_NAME in value or value.get('_is_tuple') or value.get('_is_set')):
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        elif type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        elif type(value) == dict:  # value is is a dict but not jsonic type dict
            deserialized_dict[key] = _deserialize_generic_dict(value, deserialize_private_attributes=deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    return deserialized_dict


def get_type_by_name(type_name: str):
    if type_name in Serializable.jsonic_types:
        return Serializable.jsonic_types[type_name].cls

    cls_name = None
    try:
        last_index = type_name.rindex('.')
        module_name = type_name[0:last_index]
        cls_name = type_name[last_index + 1:]
        module = importlib.import_module(module_name)
        return getattr(module, cls_name)
    except (AttributeError, ValueError):
        # Class might be defined locally (e.g., in a test function)
        # Try to find it in the type resolver's internal cache
        if cls_name:
            import sys
            for frame_info in inspect.stack():
                frame_locals = frame_info.frame.f_locals
                if cls_name in frame_locals:
                    cls = frame_locals[cls_name]
                    if inspect.isclass(cls) and full_type_name(cls) == type_name:
                        return cls
        raise TypeError(f'Could not find type: {type_name}')


def _deserialize_jsonic_type_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME not in obj:
        raise TypeError(f'Deserializing dict of jsonic type but could not find {SERIALIZED_TYPE_ATTRIBUTE_NAME} attribute')

    type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
    is_jsonic_type = type_name in Serializable.jsonic_types
    cls = get_type_by_name(type_name)

    if expected_type and full_type_name(expected_type) != type_name:
        raise AttributeError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}')

    # Check if it's an Enum
    if isinstance(cls, type) and issubclass(cls, Enum):
        # Deserialize enum by name (more reliable than value for aliases)
        # For combined flags, name might be None, use value instead
        if obj['name'] is not None:
            return cls[obj['name']]
        else:
            return cls(obj['value'])
    
    # Try type resolver (but not for Serializable types - they have priority)
    if not is_jsonic_type:
        from jsonic.type_resolver import get_resolver_for_type
        resolver = get_resolver_for_type(cls)
        if resolver:
            # Recursively deserialize nested structures first
            data = {}
            for key, value in obj.items():
                if key == SERIALIZED_TYPE_ATTRIBUTE_NAME:
                    continue
                elif type(value) == list:
                    data[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
                elif type(value) == dict:
                    if SERIALIZED_TYPE_ATTRIBUTE_NAME in value:
                        data[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
                    else:
                        data[key] = _deserialize_generic_dict(value, deserialize_private_attributes=deserialize_private_attributes)
                else:
                    data[key] = value
            
            return resolver.deserialize(data, cls)

    deserialized_dict = {}

    for key, value in obj.items():
        if key == SERIALIZED_TYPE_ATTRIBUTE_NAME:
            pass
        elif not deserialize_private_attributes and key.startswith('_'):
            pass
        elif type(value) == list:
            deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
        elif type(value) == dict:
            if SERIALIZED_TYPE_ATTRIBUTE_NAME in value or value.get('_is_tuple') or value.get('_is_set'):
                deserialized_dict[key] = deserialize(value, deserialize_private_attributes=deserialize_private_attributes)
            else:
                deserialized_dict[key] = _deserialize_generic_dict(value, deserialize_private_attributes=deserialize_private_attributes)
        else:
            deserialized_dict[key] = value

    init_dict = {}

    sign = inspect.signature(cls.__init__)

    init_parameters_mapping = Serializable.jsonic_types[type_name].init_parameters_mapping if is_jsonic_type else {}
    transient_attrs = Serializable.jsonic_types[type_name].transient_attributes if is_jsonic_type else []

    for parameter_name, parameter_data in sign.parameters.items():
        if not deserialize_private_attributes and is_private_attribute(parameter_name):
            continue
        if parameter_name == 'self':
            pass
        elif parameter_data.kind == inspect.Parameter.VAR_KEYWORD or \
                parameter_data.kind == inspect.Parameter.VAR_POSITIONAL:
            pass
        elif parameter_name in init_parameters_mapping:
            init_dict[parameter_name] = deserialized_dict[init_parameters_mapping[parameter_name]]
        else:  # assuming parameter has same name as corresponding attribute
            # Skip transient attributes only if they have a default value
            if transient_attrs and parameter_name in transient_attrs:
                if parameter_data.default != inspect.Parameter.empty:
                    continue
            if parameter_name not in deserialized_dict:
                raise AttributeError(f'Missing attribute in given dict to match __init__ parameter: {parameter_name}.\n'
                                     f'If relevant, consider registering type "{type_name}" using "register_jsonic_type" '
                                     f'and providing required "init_parameters_mapping".')
            init_dict[parameter_name] = deserialized_dict[parameter_name]

    created_instance = cls(**init_dict)

    # After creating the instance, set all it's attributes to deserialized value
    for attr_name, attr_value in deserialized_dict.items():
        if not deserialize_private_attributes and is_private_attribute(attr_name):
            continue
        # Skip transient attributes
        if transient_attrs and attr_name in transient_attrs:
            continue
        setattr(created_instance, attr_name, attr_value)

    return created_instance


def _deserialize_list(lst: list, deserialize_private_attributes=False, expected_type: type = None):
    if expected_type and expected_type != list:
        raise AttributeError(f'Deserializing list, which is not the expected type: {expected_type}')
    deserialized_list = []
    for element in lst:
        deserialized_list.append(deserialize(element, deserialize_private_attributes=deserialize_private_attributes))

    return deserialized_list
