import importlib
import inspect
import json
from enum import Enum
from typing import List, Dict

from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer
from jsonic.util import full_type_name, is_private_attribute
from jsonic.exceptions import SerializationError, DeserializationError
from jsonic.pydantic_support import (
    is_pydantic_model,
    is_pydantic_class,
    serialize_pydantic_model,
    deserialize_pydantic_model
)

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


def serialize(obj, serialize_private_attributes=False, string_output=False, include=None, exclude=None):
    """
     Serializes ``class instance`` / ``dict`` / ``list`` / ``other python type`` into ``dictionary`` / ``json string`` representing the input

    Args:
        obj: ``object`` / ``class instance`` / ``dict`` / ``list`` to be serializes
        serialize_private_attributes: should serialize private attributes (attributes which their name starts with ``_``)
        string_output: serialize into json string or ``dict`` / ``list
        include: optional list/set of field names to include (only these fields will be serialized)
        exclude: optional list/set of field names to exclude (these fields will not be serialized)

    Returns:
        ``dictionary`` / ``json string`` representing the input

    Note:
        Only class instances of classes extending ``Serializable`` or registered using ``register_jsonic_type`` can be serialized
        If both include and exclude are provided, include takes precedence
    """
    # Pre-process everything recursively - this handles tuples, sets, and all objects
    obj = _handle_serialization_error(
        lambda: _preprocess_for_serialization(obj, serialize_private_attributes, ""),
        ""
    )
    
    # Apply include/exclude filtering if this is a dict (serialized object)
    if isinstance(obj, dict) and (include is not None or exclude is not None):
        obj = _apply_field_filter(obj, include, exclude)
    
    # Use custom encoder that handles nested enums
    json_str = json.dumps(obj, cls=EnumEncoder)
    return json_str if string_output else json.loads(json_str)


def _apply_field_filter(data, include=None, exclude=None, path=""):
    """Apply include/exclude filtering to a dictionary with nested field support."""
    if not isinstance(data, dict):
        return data
    
    # Separate top-level and nested filters
    top_include = set()
    nested_include = {}
    if include is not None:
        for field in include:
            if '.' in field:
                parts = field.split('.', 1)
                nested_include.setdefault(parts[0], set()).add(parts[1])
            else:
                top_include.add(field)
    
    top_exclude = set()
    nested_exclude = {}
    if exclude is not None:
        for field in exclude:
            if '.' in field:
                parts = field.split('.', 1)
                nested_exclude.setdefault(parts[0], set()).add(parts[1])
            else:
                top_exclude.add(field)
    
    result = {}
    for key, value in data.items():
        # Always keep _serialized_type
        if key == '_serialized_type':
            result[key] = value
            continue
        
        # Check top-level filtering
        if include is not None:
            # If include is specified, only include fields in top_include or nested_include
            if key not in top_include and key not in nested_include:
                continue
        if exclude is not None and key in top_exclude:
            continue
        
        # Apply nested filtering recursively
        if key in nested_include:
            if isinstance(value, dict):
                # Check if it's a set or tuple structure
                if value.get('_is_set') or value.get('_is_tuple'):
                    result[key] = dict(value)  # Copy structure
                    if 'items' in value:
                        result[key]['items'] = [_apply_field_filter(item, include=nested_include[key], exclude=None) if isinstance(item, dict) else item for item in value['items']]
                else:
                    result[key] = _apply_field_filter(value, include=nested_include[key], exclude=None)
            elif isinstance(value, list):
                result[key] = [_apply_field_filter(item, include=nested_include[key], exclude=None) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        elif key in nested_exclude:
            if isinstance(value, dict):
                # Check if it's a set or tuple structure
                if value.get('_is_set') or value.get('_is_tuple'):
                    result[key] = dict(value)  # Copy structure
                    if 'items' in value:
                        result[key]['items'] = [_apply_field_filter(item, include=None, exclude=nested_exclude[key]) if isinstance(item, dict) else item for item in value['items']]
                else:
                    result[key] = _apply_field_filter(value, include=None, exclude=nested_exclude[key])
            elif isinstance(value, list):
                result[key] = [_apply_field_filter(item, include=None, exclude=nested_exclude[key]) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result
    return json_str if string_output else json.loads(json_str)


def _handle_serialization_error(func, path):
    """Wrapper to handle exceptions consistently during serialization."""
    try:
        return func()
    except (SerializationError, ValueError):
        raise
    except RecursionError:
        raise ValueError("Circular reference detected during serialization")
    except (TypeError, Exception) as e:
        raise SerializationError(str(e), path)


def _handle_deserialization_error(func, path):
    """Wrapper to handle exceptions consistently during deserialization."""
    try:
        return func()
    except DeserializationError:
        raise
    except (TypeError, AttributeError) as e:
        raise DeserializationError(str(e), path)


def _preprocess_for_serialization(obj, serialize_private_attributes=False, path=""):
    """Recursively preprocess all objects for serialization."""
    # Handle primitives
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    
    # Handle lists
    if isinstance(obj, list):
        return [_handle_serialization_error(
            lambda item=item, i=i: _preprocess_for_serialization(item, serialize_private_attributes, f"{path}[{i}]" if path else f"[{i}]"),
            f"{path}[{i}]" if path else f"[{i}]"
        ) for i, item in enumerate(obj)]
    
    # Handle dicts
    if isinstance(obj, dict):
        return {k: _handle_serialization_error(
            lambda v=v, k=k: _preprocess_for_serialization(v, serialize_private_attributes, f"{path}.{k}" if path else k),
            f"{path}.{k}" if path else k
        ) for k, v in obj.items()}
    
    # Handle all other objects (tuples, sets, enums, custom objects)
    return _serialize_object(obj, serialize_private_attributes, path)


def deserialize(obj, deserialize_private_attributes: bool = False, string_input: bool = False, expected_type: type = None, _path: str = ""):
    """
    Deserializes dictionary/json string representing dictionary, that was returned by ``serialize`` function call on an object

    Args:
        obj: dictionary/json string representing dictionary, that is a result of ``serialize`` function on an object
        deserialize_private_attributes (bool): should deserialize private attributes (attributes which their name starts with ``_``)
        string_input (bool): is the input of type ``json string``, or ``dict``
        expected_type: the deserialized result expected type
        _path: internal parameter for tracking path (not for external use)
    Returns:
        object / class instance / dict / list, depending on the serialized input

    Raises:
        AttributeError: When the serialized type is different from the expected type
    """
    if string_input:
        if type(obj) != str:
            raise TypeError(f'deserializing string, but input was not of type str. given input: {obj}')
        return deserialize(json.loads(obj), expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes, _path=_path)

    if type(obj) == list:
        return _deserialize_list(obj, expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes, path=_path)
    elif type(obj) == dict:
        # Check for tuple/set markers first
        if obj.get('_is_tuple') and 'tuple' in _JsonicDeserializer.deserializers:
            return _JsonicDeserializer.deserializers['tuple'](obj)
        if obj.get('_is_set') and 'set' in _JsonicDeserializer.deserializers:
            return _JsonicDeserializer.deserializers['set'](obj)
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj and obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] in _JsonicDeserializer.deserializers:
            # There is custom deserializer for given objects serialized type, so use it
            return _deserialize_with_custom_deserializer(obj, expected_type=expected_type, path=_path)
        return _deserialize_dict(obj, expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes, path=_path)
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


def _serialize_object(obj, serialize_private_attributes=False, path=""):
    """Serialize an object with path tracking for better error messages."""
    typ = type(obj)
    
    # Check for Pydantic model first (before other checks)
    if is_pydantic_model(obj):
        # Get the dict from Pydantic
        pydantic_dict = serialize_pydantic_model(obj, serialize_private_attributes)
        # Recursively process the dict to handle sets, tuples, nested objects
        result = {}
        for key, value in pydantic_dict.items():
            if key == '_serialized_type':
                result[key] = value
            else:
                key_path = f"{path}.{key}" if path else key
                result[key] = _handle_serialization_error(
                    lambda v=value, kp=key_path: _preprocess_for_serialization(v, serialize_private_attributes, kp),
                    key_path
                )
        return result
    
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
                key_path = f"{path}.{key}" if path else key
                result[key] = _handle_serialization_error(
                    lambda v=value, kp=key_path: _preprocess_for_serialization(v, serialize_private_attributes, kp),
                    key_path
                )
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
                    slot_path = f"{path}.{slot}" if path else slot
                    result[slot] = _handle_serialization_error(
                        lambda v=value, sp=slot_path: _preprocess_for_serialization(v, serialize_private_attributes, sp),
                        slot_path
                    )
            return result
    
    # Priority 3: Type resolvers (dataclass=50, typehinted=25)
    from jsonic.type_resolver import get_resolver_for_type
    resolver = get_resolver_for_type(typ)
    if resolver:
        result = _handle_serialization_error(
            lambda: resolver.serialize(obj, serialize_private_attributes),
            path
        )
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
            key_path = f"{path}.{key}" if path else key
            result[key] = _handle_serialization_error(
                lambda v=value, kp=key_path: _preprocess_for_serialization(v, serialize_private_attributes, kp),
                key_path
            )
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
                slot_path = f"{path}.{slot}" if path else slot
                result[slot] = _handle_serialization_error(
                    lambda v=value, sp=slot_path: _preprocess_for_serialization(v, serialize_private_attributes, sp),
                    slot_path
                )
        return result

    raise SerializationError(f'Could not find serializer for type: {typ}', path)


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


def _deserialize_with_custom_deserializer(obj, expected_type: type = None, path=""):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        if expected_type and full_type_name(expected_type) != type_name:
            raise DeserializationError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}', path)
        if type_name in _JsonicDeserializer.deserializers:
            del obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
            result = _JsonicDeserializer.deserializers[type_name](obj)
            obj[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
            return result

        raise DeserializationError(f'Could not find custom deserializer for object with type tag: {type_name}', path)

    raise DeserializationError(f'Missing attribute _serialized_type for object: {obj}', path)


def _deserialize_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None, path=""):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        return _deserialize_jsonic_type_dict(obj, deserialize_private_attributes=deserialize_private_attributes,
                                             expected_type=expected_type, path=path)

    return _deserialize_generic_dict(obj, deserialize_private_attributes=deserialize_private_attributes, expected_type=expected_type, path=path)


def _deserialize_generic_dict(obj: dict, deserialize_private_attributes: bool = False, expected_type: type = None, path=""):
    if expected_type and expected_type != dict:
        raise DeserializationError(f'Deserializing type dict, which is not the expected type: {expected_type}', path)

    deserialized_dict = {}

    for key, value in obj.items():
        key_path = f"{path}.{key}" if path else key
        if type(value) == dict and (SERIALIZED_TYPE_ATTRIBUTE_NAME in value or value.get('_is_tuple') or value.get('_is_set')):
            deserialized_dict[key] = _handle_deserialization_error(
                lambda: deserialize(value, deserialize_private_attributes=deserialize_private_attributes, _path=key_path),
                key_path
            )
        elif type(value) == list:
            deserialized_dict[key] = _handle_deserialization_error(
                lambda: deserialize(value, deserialize_private_attributes=deserialize_private_attributes, _path=key_path),
                key_path
            )
        elif type(value) == dict:  # value is is a dict but not jsonic type dict
            deserialized_dict[key] = _handle_deserialization_error(
                lambda: _deserialize_generic_dict(value, deserialize_private_attributes=deserialize_private_attributes, path=key_path),
                key_path
            )
        else:
            deserialized_dict[key] = value

    return deserialized_dict


def _find_similar_types(type_name: str, max_suggestions: int = 5):
    """Find similar registered type names using fuzzy matching."""
    from difflib import get_close_matches
    
    # Get all registered type names
    registered_types = list(Serializable.jsonic_types.keys())
    
    if not registered_types:
        return []
    
    # Try exact case-insensitive match first
    type_name_lower = type_name.lower()
    for registered in registered_types:
        if registered.lower() == type_name_lower:
            return [registered]
    
    # Try fuzzy matching on full names
    matches = get_close_matches(type_name, registered_types, n=max_suggestions, cutoff=0.6)
    
    # Also try matching just the class name (last part after dot)
    if '.' in type_name:
        class_name = type_name.split('.')[-1]
        for registered in registered_types:
            if '.' in registered:
                registered_class = registered.split('.')[-1]
                if class_name.lower() == registered_class.lower() and registered not in matches:
                    matches.insert(0, registered)
    
    return matches[:max_suggestions]


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
    except (AttributeError, ValueError, ModuleNotFoundError) as e:
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
        
        # Build helpful error message with suggestions
        error_parts = [f'Could not find type: {type_name}']
        
        # Find similar types
        similar = _find_similar_types(type_name)
        if similar:
            error_parts.append('\n\nDid you mean one of these?')
            for suggestion in similar:
                error_parts.append(f'  - {suggestion}')
        
        # Add common causes
        error_parts.append('\n\nCommon causes:')
        if '.' in type_name:
            error_parts.append(f"  - Module '{module_name}' not imported")
        else:
            error_parts.append('  - Class defined locally (not accessible for deserialization)')
        error_parts.append('  - Typo in class name')
        error_parts.append('  - Class not registered with register_jsonic_type()')
        
        # Show some registered types if available
        registered_types = list(Serializable.jsonic_types.keys())
        if registered_types and not similar:
            error_parts.append(f'\n\nRegistered types ({len(registered_types)} total):')
            # Show first 5
            for reg_type in registered_types[:5]:
                error_parts.append(f'  - {reg_type}')
            if len(registered_types) > 5:
                error_parts.append(f'  ... and {len(registered_types) - 5} more')
        
        raise TypeError(''.join(error_parts))


def _deserialize_jsonic_type_dict(obj: dict, deserialize_private_attributes=False, expected_type: type = None, path=""):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME not in obj:
        raise DeserializationError(f'Deserializing dict of jsonic type but could not find {SERIALIZED_TYPE_ATTRIBUTE_NAME} attribute', path)

    type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
    is_jsonic_type = type_name in Serializable.jsonic_types
    cls = get_type_by_name(type_name)

    if expected_type and full_type_name(expected_type) != type_name:
        raise DeserializationError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}', path)

    # Check if it's a Pydantic model
    if is_pydantic_class(cls):
        return deserialize_pydantic_model(obj, cls)

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
                raise DeserializationError(f'Missing attribute in given dict to match __init__ parameter: {parameter_name}.\n'
                                     f'If relevant, consider registering type "{type_name}" using "register_jsonic_type" '
                                     f'and providing required "init_parameters_mapping".', path)
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


def _deserialize_list(lst: list, deserialize_private_attributes=False, expected_type: type = None, path=""):
    if expected_type and expected_type != list:
        raise DeserializationError(f'Deserializing list, which is not the expected type: {expected_type}', path)
    deserialized_list = []
    for i, element in enumerate(lst):
        element_path = f"{path}[{i}]" if path else f"[{i}]"
        deserialized_list.append(_handle_deserialization_error(
            lambda e=element: deserialize(e, deserialize_private_attributes=deserialize_private_attributes, _path=element_path),
            element_path
        ))

    return deserialized_list
