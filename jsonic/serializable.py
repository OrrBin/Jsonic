import importlib
import inspect
import json
from contextvars import ContextVar
from dataclasses import replace
from jsonic.context import _traversal, current_context, _serializing, _SerializationFrame
from threading import get_ident
from enum import Enum, Flag
from typing import List, Dict, get_origin
from uuid import UUID

from jsonic.wire import LiteralDict
from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer
from jsonic.util import full_type_name, is_private_attribute
from jsonic.exceptions import SerializationError, DeserializationError
from jsonic.pydantic_support import (
    is_pydantic_model,
    is_pydantic_class,
    serialize_pydantic_model,
    deserialize_pydantic_model,
    split_pydantic_type_tag
)

SERIALIZED_TYPE_ATTRIBUTE_NAME = '_serialized_type'

# A call-local policy also reaches legacy callbacks that recursively call deserialize.
_safe_types = ContextVar('jsonic_safe_types', default=None)
_selection = ContextVar('jsonic_field_selection', default=None)


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum types"""
    def encode(self, obj):
        # Pre-process to convert all enums before encoding
        obj = self._convert_enums(obj)
        return super().encode(obj)
    
    def _convert_enums(self, obj, _active=None):
        """Convert enum values while rejecting cycles in raw codec mappings."""
        if isinstance(obj, Enum):
            return {'name': obj.name, 'value': obj.value,
                    SERIALIZED_TYPE_ATTRIBUTE_NAME: full_type_name(type(obj))}
        if not isinstance(obj, (dict, list, tuple)):
            return obj
        active = set() if _active is None else _active
        identity = id(obj)
        if identity in active:
            raise ValueError('Circular reference detected during serialization')
        active.add(identity)
        try:
            if isinstance(obj, dict):
                return type(obj)((key, self._convert_enums(value, active)) for key, value in obj.items())
            if isinstance(obj, list):
                return [self._convert_enums(value, active) for value in obj]
            return tuple(self._convert_enums(value, active) for value in obj)
        finally:
            active.remove(identity)

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


def serialize(obj, serialize_private_attributes=False, string_output=False, include=None, exclude=None, *, uuid_format=None, pydantic_mode=None, wire_format=None):
    """
     Serializes ``class instance`` / ``dict`` / ``list`` / ``other python type`` into ``dictionary`` / ``json string`` representing the input

    Args:
        obj: ``object`` / ``class instance`` / ``dict`` / ``list`` to be serializes
        serialize_private_attributes: should serialize private attributes (attributes which their name starts with ``_``)
        string_output: serialize into json string or ``dict`` / ``list
        include: optional list/set of field names to include (only these fields will be serialized)
        exclude: optional list/set of field names to exclude (these fields will not be serialized)
        uuid_format: 'legacy' (default) or opt-in portable 'string' representation
        pydantic_mode: 'presentation' (default) or opt-in canonical-field 'roundtrip' format

    Returns:
        ``dictionary`` / ``json string`` representing the input

    Note:
        Only class instances of classes extending ``Serializable`` or registered using ``register_jsonic_type`` can be serialized
        If both include and exclude select a field, exclude takes precedence
    """
    context = current_context()
    uuid_format = context.uuid_format if uuid_format is None else uuid_format
    if uuid_format not in ('legacy', 'string'):
        raise ValueError("uuid_format must be 'legacy' or 'string'")
    pydantic_mode = context.pydantic_mode if pydantic_mode is None else pydantic_mode
    if pydantic_mode not in ('presentation', 'roundtrip'):
        raise ValueError("pydantic_mode must be 'presentation' or 'roundtrip'")
    wire_format = context.wire_format if wire_format is None else wire_format
    if wire_format not in ('legacy', 'v2'):
        raise ValueError("wire_format must be 'legacy' or 'v2'")
    selection = _FieldSelection(include, exclude)
    context_token = _traversal.set(replace(context, uuid_format=uuid_format, pydantic_mode=pydantic_mode, wire_format=wire_format))
    token = _selection.set(selection)
    try:
        obj = _handle_serialization_error(
            lambda: _preprocess_for_serialization(obj, serialize_private_attributes, ""), ""
        )
    finally:
        _selection.reset(token)
        _traversal.reset(context_token)

    if wire_format == 'v2':
        from jsonic.wire import envelope
        # Normalize enums returned directly by custom codecs before tagging nodes.
        obj = envelope(EnumEncoder()._convert_enums(obj))

    # Use custom encoder that handles nested enums
    json_str = json.dumps(obj, cls=EnumEncoder)
    return json_str if string_output else json.loads(json_str)


class _FieldSelection:
    """Compile dotted selectors once per field scope; exclusion always wins."""
    def __init__(self, include=None, exclude=None):
        self.include = None if include is None else frozenset(include)
        self.exclude = frozenset(exclude or ())
        self.inc = self._split(self.include or ())
        self.exc = self._split(self.exclude)

    @staticmethod
    def _split(paths):
        result = {}
        for field in paths:
            head, dot, tail = field.partition('.')
            result.setdefault(head, set()).add(tail if dot else '')
        return result

    def child(self, key):
        inc = self.inc.get(key, set())
        exc = self.exc.get(key, set())
        if '' in exc or (self.include is not None and not inc):
            return None
        return _FieldSelection(None if self.include is None or '' in inc else inc, exc)


def _serialize_fields(names, getter, private=False, path=None, transient=(), filter_private=True, literal=False):
    """Select a field before reading or traversing its value."""
    selection = _selection.get() or _FieldSelection()
    path = current_context().path if path is None else path
    result = {}
    for key in names:
        if key == SERIALIZED_TYPE_ATTRIBUTE_NAME and not literal:
            continue
        if filter_private and not private and key.startswith('_'):
            continue
        if key in transient:
            continue
        child = selection.child(key)
        if child is None:
            continue
        key_path = f"{path}.{key}" if path else str(key)
        token = _selection.set(child)
        try:
            result[key] = _handle_serialization_error(
                lambda: _preprocess_for_serialization(getter(key), private, key_path), key_path
            )
        finally:
            _selection.reset(token)
    return result


def _apply_field_filter(data, include=None, exclude=None, path=""):
    """Filter custom codec output; codecs control their own value extraction."""
    if isinstance(data, list):
        return [_apply_field_filter(v, include, exclude) for v in data]
    if not isinstance(data, dict):
        return data
    if not isinstance(data, LiteralDict) and (data.get('_is_tuple') or data.get('_is_set')):
        return {**data, 'items': _apply_field_filter(data['items'], include, exclude)}
    selection = _FieldSelection(include, exclude)
    result = LiteralDict() if isinstance(data, LiteralDict) else {}
    for key, value in data.items():
        if key == SERIALIZED_TYPE_ATTRIBUTE_NAME and not isinstance(data, LiteralDict):
            result[key] = value
            continue
        child = selection.child(key)
        if child is not None:
            result[key] = _apply_field_filter(value, child.include, child.exclude)
    return result


def _handle_serialization_error(func, path):
    """Wrapper to handle exceptions consistently during serialization."""
    try:
        return func()
    except (SerializationError, ValueError):
        raise
    except RecursionError:
        raise ValueError("Circular reference detected during serialization")
    except (TypeError, Exception) as e:
        raise SerializationError(str(e), path) from e


def _handle_deserialization_error(func, path):
    """Wrapper to handle exceptions consistently during deserialization."""
    try:
        return func()
    except DeserializationError:
        raise
    except (TypeError, AttributeError) as e:
        # Preserve specialized native/application exception classes, e.g.
        # FrozenInstanceError, which callers may already catch specifically.
        if type(e) not in (TypeError, AttributeError):
            raise
        raise DeserializationError(str(e), path) from e


def _preprocess_for_serialization(obj, serialize_private_attributes=None, path=None):
    context = current_context()
    private = context.serialize_private_attributes if serialize_private_attributes is None else serialize_private_attributes
    path = context.path if path is None else path
    token = _traversal.set(replace(context, path=path, serialize_private_attributes=private))
    active_token = None
    frame = None
    try:
        if obj is not None and not isinstance(obj, (bool, int, float, str)):
            owner = get_ident()
            ancestors = tuple(f for f in _serializing.get() if f.active and f.owner == owner)
            if any(f.value is obj for f in ancestors):
                raise ValueError('Circular reference detected during serialization')
            frame = _SerializationFrame(obj, owner)
            active_token = _serializing.set(ancestors + (frame,))
        return _preprocess_impl(obj, private, path)
    finally:
        if frame is not None:
            # Copied task contexts must not retain a live ancestor after its
            # synchronous call finishes, or hold on to the source object.
            frame.active, frame.value = False, None
        if active_token is not None:
            _serializing.reset(active_token)
        _traversal.reset(token)


def _preprocess_impl(obj, serialize_private_attributes=False, path=""):
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
    
    # A dictionary's private-looking keys are ordinary user data.
    if isinstance(obj, dict):
        result = _serialize_fields(obj, obj.__getitem__, serialize_private_attributes, path, filter_private=False, literal=current_context().wire_format == 'v2')
        if current_context().wire_format == 'v2':
            return LiteralDict(result)
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
            result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        return result

    # Handle all other objects (tuples, sets, enums, custom objects)
    return _serialize_object(obj, serialize_private_attributes, path)


def _validate_safe_payload(obj, allowed, path=""):
    """Validate the entire tree before executing any reconstruction callbacks."""
    if isinstance(obj, list):
        for i, value in enumerate(obj):
            _validate_safe_payload(value, allowed, f"{path}[{i}]")
    elif isinstance(obj, LiteralDict):
        for key, value in obj.items():
            _validate_safe_payload(value, allowed, f"{path}.{key}" if path else str(key))
    elif isinstance(obj, dict):
        tag = obj.get(SERIALIZED_TYPE_ATTRIBUTE_NAME)
        if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
            base, persistence = tag, False
            if isinstance(tag, str) and tag not in _JsonicDeserializer.deserializers:
                base, persistence = split_pydantic_type_tag(tag)
            authorized = isinstance(base, str) and base in allowed
            if persistence:
                authorized = authorized and is_pydantic_class(allowed[base])
            if not authorized:
                raise DeserializationError(f"Type tag is not registered for safe decoding: {tag!r}", path)
        for marker, name in (("_is_tuple", "tuple"), ("_is_set", "set")):
            if obj.get(marker):
                if tag != name or obj[marker] is not True or not isinstance(obj.get("items"), list):
                    raise DeserializationError(f"Invalid {name} envelope", path)
        for key, value in obj.items():
            _validate_safe_payload(value, allowed, f"{path}.{key}" if path else str(key))


def _check_expected_type(actual, expected, path):
    if actual is not expected:
        raise DeserializationError(f"Deserializing type {actual}, which is not the expected type: {expected}", path,
                                   code='type_mismatch', expected_type=expected, actual_type=actual)


def _payload_type(obj, expected):
    """Identify a root type without input-directed imports or callback execution."""
    if isinstance(obj, LiteralDict):
        return dict
    if not isinstance(obj, dict):
        return type(obj)
    if obj.get('_is_tuple'):
        return tuple
    if obj.get('_is_set'):
        return set
    tag = obj.get(SERIALIZED_TYPE_ATTRIBUTE_NAME)
    if tag is None:
        return dict
    if not isinstance(tag, str):
        raise DeserializationError("Type tag must be a string")
    if tag in _JsonicDeserializer.types:
        return _JsonicDeserializer.types[tag]
    tag, _ = split_pydantic_type_tag(tag)
    if tag in Serializable.jsonic_types:
        return Serializable.jsonic_types[tag].cls
    # Identity cannot be resolved safely from a module name. Compare the name
    # now, then verify the actual constructed type after legacy dispatch.
    return expected if tag == full_type_name(expected) else None


def deserialize(obj, deserialize_private_attributes=None, string_input=False,
                expected_type=None, _path=None, *, safe=None, wire_format='legacy', validation=None, unknown_fields='forbid'):
    """Decode data; omitted private-field options inherit the active traversal.

    Use safe=True for externally supplied data. Safe decoding only reconstructs
    explicitly authorized classes/codecs; legacy decoding is for trusted data.
    Root expected_type uses exact identity and does not validate field values.
    validation='strict' explicitly structures a supported schema from plain or
    tagged input, with no coercion and unknown_fields='forbid' (or 'ignore').
    See VALIDATION_MODES.md for the scoped contract.
    """
    if wire_format not in ('legacy', 'v2'):
        raise ValueError("wire_format must be 'legacy' or 'v2'")
    if wire_format == 'v2':
        from jsonic.wire import unpack
        obj = unpack(json.loads(obj) if string_input else obj)
        string_input = False
    if validation not in (None, 'strict'):
        raise ValueError("validation must be None or 'strict'")
    if validation == 'strict':
        if expected_type is None:
            raise ValueError('Strict validation requires expected_type')
        from jsonic.structuring import structure
        if string_input:
            if not isinstance(obj, str):
                raise DeserializationError('string_input requires str')
            obj = json.loads(obj)
        return structure(obj, expected_type, unknown_fields, _path or '', safe=safe)
    if unknown_fields != 'forbid':
        raise ValueError('unknown_fields applies only to strict validation')
    context = current_context()
    private = context.deserialize_private_attributes if deserialize_private_attributes is None else deserialize_private_attributes
    path = context.path if _path is None else _path
    token = _traversal.set(replace(context, path=path, deserialize_private_attributes=private))
    try:
        return _deserialize_with_policy(obj, private, string_input, expected_type, path, safe=safe)
    except (TypeError, AttributeError) as error:
        # Keep this boundary inline: extra callback frames per container would
        # reduce supported nesting depth on older Python versions.
        if type(error) not in (TypeError, AttributeError):
            raise
        raise DeserializationError(str(error), path) from error
    finally:
        _traversal.reset(token)


def _deserialize_with_policy(obj, deserialize_private_attributes=False, string_input=False,
                expected_type=None, _path="", *, safe=None):
    """Decode Jsonic data.

    Pass safe=True for externally controlled data. Only registered classes and
    codecs (plus an explicitly supplied root expected_type) are authorized.
    The policy propagates through nested callbacks. Registration authorizes
    trusted application code; it does not sandbox constructors or hooks.
    The default retains legacy dynamic imports for backward compatibility.
    """
    if expected_type is not None and (not isinstance(expected_type, type) or get_origin(expected_type) is not None):
        raise TypeError('expected_type must be a concrete Python type')
    policy = _safe_types.get()
    token = None
    if safe is True and policy is None:
        allowed = {name: data.cls for name, data in Serializable.jsonic_types.items()}
        allowed.update(_JsonicDeserializer.types)
        if expected_type is not None:
            allowed[full_type_name(expected_type)] = expected_type
        token = _safe_types.set(allowed)
        policy = allowed
    try:
        if policy is not None:
            if string_input:
                if not isinstance(obj, str):
                    raise TypeError("string_input requires str")
                obj = json.loads(obj)
                string_input = False
            _validate_safe_payload(obj, policy, _path)
        if expected_type is not None:
            source = json.loads(obj) if string_input and isinstance(obj, str) else obj
            actual = _payload_type(source, expected_type)
            _check_expected_type(actual, expected_type, _path)
        result = _deserialize_impl(obj, deserialize_private_attributes, string_input, expected_type, _path)
        if expected_type is not None:
            _check_expected_type(type(result), expected_type, _path)
        return result
    finally:
        if token is not None:
            _safe_types.reset(token)


def _deserialize_impl(obj, deserialize_private_attributes: bool = False, string_input: bool = False, expected_type: type = None, _path: str = ""):
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
            raise TypeError('deserializing string: string_input requires str')
        return deserialize(json.loads(obj), expected_type=expected_type, deserialize_private_attributes=deserialize_private_attributes, _path=_path)

    if isinstance(obj, LiteralDict):
        return {key: current_context().deserialize(value, key) for key, value in obj.items()}
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
    if typ is UUID and current_context().uuid_format == 'string':
        return {'uuid': str(obj), SERIALIZED_TYPE_ATTRIBUTE_NAME: 'uuid.UUID'}

    # Check for Pydantic model first (before other checks)
    if is_pydantic_model(obj):
        selection = _selection.get() or _FieldSelection()
        pydantic_dict = serialize_pydantic_model(obj, serialize_private_attributes,
                                                 selection.include, selection.exclude,
                                                 persistence=current_context().pydantic_mode == 'roundtrip')
        result = _serialize_fields(pydantic_dict, pydantic_dict.__getitem__, serialize_private_attributes, path, filter_private=False)
        result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = pydantic_dict[SERIALIZED_TYPE_ATTRIBUTE_NAME]
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
        value = dict(_JsonicSerializer.serializers[typ](obj))
        value[SERIALIZED_TYPE_ATTRIBUTE_NAME] = _JsonicSerializer.type_ids.get(typ, typ.__name__)
        selection = _selection.get() or _FieldSelection()
        if typ not in (tuple, set) and (selection.include is not None or selection.exclude):
            value = _apply_field_filter(value, selection.include, selection.exclude)
        return value

    # Priority 2: Serializable types (100)
    type_name = full_type_name(typ)
    is_jsonic_type = type_name in Serializable.jsonic_types
    
    if is_jsonic_type:
        import dataclasses
        if dataclasses.is_dataclass(typ):
            from jsonic.constructors import reject_required_initvars
            reject_required_initvars(typ, serializing=True)
        type_data = Serializable.jsonic_types[type_name]
        
        if hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
            names = _get_attribute_names(obj)
            result = _serialize_fields(names, lambda key: getattr(obj, key),
                                       serialize_private_attributes, path, type_data.transient_attributes)
            result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
            return result

    # Priority 3: Type resolvers (dataclass=50, typehinted=25)
    from jsonic.type_resolver import get_resolver_for_type, serialize_with_resolver
    resolver = get_resolver_for_type(typ)
    if resolver:
        result = _handle_serialization_error(
            lambda: serialize_with_resolver(resolver, obj, current_context()),
            path
        )
        result = dict(result)
        result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
        selection = _selection.get() or _FieldSelection()
        if selection.include is not None or selection.exclude:
            result = _apply_field_filter(result, selection.include, selection.exclude)
        return result
    
    # Fallback: Generic object with __dict__ or __slots__.
    if hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
        names = _get_attribute_names(obj)
        result = _serialize_fields(names, lambda key: getattr(obj, key), serialize_private_attributes, path)
        result[SERIALIZED_TYPE_ATTRIBUTE_NAME] = type_name
        return result

    raise SerializationError(f'Could not find serializer for type: {typ}', path)


def _get_all_slots(cls):
    """Return distinct storage names, walking the MRO from most derived."""
    slots = []
    for owner in cls.__mro__:
        declared = owner.__dict__.get('__slots__', ())
        if isinstance(declared, str):
            declared = (declared,)
        for name in declared:
            if name in ('__dict__', '__weakref__'):
                continue
            # Slot descriptors store name-mangled private attributes.
            if name.startswith('__') and not name.endswith('__'):
                class_name = owner.__name__.lstrip('_')
                if class_name:
                    name = '_' + class_name + name
            if name not in slots:
                slots.append(name)
    return slots


def _get_attribute_names(obj):
    """Merge dynamic and initialized slot attributes without infrastructure."""
    names = list(vars(obj)) if hasattr(obj, '__dict__') else []
    for name in _get_all_slots(type(obj)):
        if name not in names and hasattr(obj, name):
            names.append(name)
    return names


def _deserialize_with_custom_deserializer(obj, expected_type: type = None, path=""):
    if SERIALIZED_TYPE_ATTRIBUTE_NAME in obj:
        type_name = obj[SERIALIZED_TYPE_ATTRIBUTE_NAME]
        if type_name in _JsonicDeserializer.deserializers:
            # A shallow copy protects the outer mapping. Nested values remain
            # shared with custom hooks for backward-compatible identity semantics.
            data = {key: value for key, value in obj.items()
                    if key != SERIALIZED_TYPE_ATTRIBUTE_NAME}
            return _JsonicDeserializer.deserializers[type_name](data)

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
        if isinstance(value, LiteralDict):
            deserialized_dict[key] = current_context().deserialize(value, key)
        elif type(value) == dict and (SERIALIZED_TYPE_ATTRIBUTE_NAME in value or value.get('_is_tuple') or value.get('_is_set')):
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
    policy = _safe_types.get()
    if policy is not None:
        cls = policy.get(type_name)
        if cls is None:
            raise DeserializationError(f"Type tag is not registered for safe decoding: {type_name!r}")
        return cls
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

    type_name, persistence = split_pydantic_type_tag(obj[SERIALIZED_TYPE_ATTRIBUTE_NAME])
    is_jsonic_type = type_name in Serializable.jsonic_types
    if expected_type and full_type_name(expected_type) != type_name:
        raise DeserializationError(f'Deserializing type {type_name}, which is not the expected type: {expected_type}', path)
    cls = get_type_by_name(type_name)

    # Check if it's a Pydantic model
    if is_pydantic_class(cls):
        return deserialize_pydantic_model(obj, cls, persistence=persistence)
    if persistence:
        raise DeserializationError('Pydantic persistence tag requires a Pydantic model', path)

    # Check if it's an Enum
    if isinstance(cls, type) and issubclass(cls, Enum):
        try:
            # Combined Flag names (e.g. READ|WRITE) are not member-map keys.
            # Let the class enforce its declared unknown-bit boundary policy.
            if issubclass(cls, Flag):
                return cls(obj['value'])
            if obj['name'] is not None:
                return cls[obj['name']]
            return cls(obj['value'])
        except (KeyError, ValueError, TypeError) as exc:
            raise DeserializationError(f"Invalid enum payload for {full_type_name(cls)}", path) from exc

    # Try type resolver (but not for Serializable types - they have priority)
    if not is_jsonic_type:
        from jsonic.type_resolver import get_resolver_for_type, deserialize_with_resolver
        resolver = get_resolver_for_type(cls)
        if resolver:
            context = current_context()
            data = {key: context.deserialize(value, key) for key, value in obj.items()
                    if key != SERIALIZED_TYPE_ATTRIBUTE_NAME}
            return _handle_deserialization_error(
                lambda: deserialize_with_resolver(resolver, data, cls, context), path
            )

    context = current_context()
    deserialized_dict = {key: context.deserialize(value, key) for key, value in obj.items()
                         if key != SERIALIZED_TYPE_ATTRIBUTE_NAME
                         and (deserialize_private_attributes or not key.startswith('_'))}

    from jsonic.constructors import constructor_kwargs, restore_attributes, reject_required_initvars
    import dataclasses
    if dataclasses.is_dataclass(cls):
        reject_required_initvars(cls)
    type_data = Serializable.jsonic_types.get(type_name)
    mapping = type_data.init_parameters_mapping if type_data else {}
    transient = type_data.transient_attributes if type_data else ()
    init_dict = constructor_kwargs(cls, deserialized_dict, mapping, transient, deserialize_private_attributes)
    created_instance = cls(**init_dict)
    restore_attributes(created_instance, deserialized_dict, transient, deserialize_private_attributes)

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
