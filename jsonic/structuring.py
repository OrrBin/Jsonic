"""Scoped, non-coercing typed input. Validate the whole tree before construction."""
import dataclasses
import inspect
import types
import typing

from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name
from jsonic.wire import LiteralDict, reject_cycles


class _Build:
    def __init__(self, factory, values):
        self.factory, self.values = factory, values

    def run(self):
        return self.factory(_materialize(self.values))


def _materialize(value):
    if isinstance(value, _Build):
        return value.run()
    if isinstance(value, dict):
        return {key: _materialize(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_materialize(child) for child in value]
    return value


def _error(message, path, code='type_mismatch', expected=None, actual=None):
    raise DeserializationError(message, path, code=code, expected_type=expected, actual_type=actual)


def structure(value, annotation, unknown_fields, path='', safe=None):
    if unknown_fields not in ('forbid', 'ignore'):
        raise ValueError("unknown_fields must be 'forbid' or 'ignore'")
    reject_cycles(value)
    classes = set()
    plan = _plan(value, annotation, path, unknown_fields, classes)
    from jsonic.serializable import _safe_types, Serializable
    from jsonic.decorators import _JsonicDeserializer
    policy = _safe_types.get()
    token = None
    if policy is not None:
        for cls in classes:
            if cls not in policy.values():
                _error('Schema class is not authorized by the active safe policy', path, 'unsafe_type')
    elif safe is True:
        allowed = {name: data.cls for name, data in Serializable.jsonic_types.items()}
        allowed.update(_JsonicDeserializer.types)
        allowed.update({full_type_name(cls): cls for cls in classes})
        token = _safe_types.set(allowed)
    try:
        return _materialize(plan)
    finally:
        if token is not None:
            _safe_types.reset(token)


def _plan(value, annotation, path, unknown, classes):
    origin, args = typing.get_origin(annotation), typing.get_args(annotation)
    if annotation is typing.Any:
        # Any means JSON values, never implicit Jsonic tag dispatch.
        return _json_value(value, path)
    if annotation is None:
        annotation = type(None)
    if origin in (typing.Union, getattr(types, 'UnionType', typing.Union)):
        for choice in args:
            branch_classes = set()
            try:
                candidate = _plan(value, choice, path, unknown, branch_classes)
            except DeserializationError as error:
                if error.code not in ('type_mismatch', 'missing_field', 'unknown_field', 'tag_mismatch'):
                    raise
            else:
                classes.update(branch_classes)
                return candidate
        _error('Value does not match any union alternative', path, expected=annotation, actual=type(value))
    if origin is typing.Literal:
        if not any(type(value) is type(option) and value == option for option in args):
            _error('Value does not match a literal alternative', path, expected=annotation, actual=type(value))
        return value
    if annotation in (str, bool, int, float, type(None)):
        if type(value) is not annotation:
            _error('Field type mismatch', path, expected=annotation, actual=type(value))
        return value
    container = origin or annotation
    if container in (list, set, tuple):
        if container in (tuple, set) and type(value) is dict:
            marker = '_is_' + container.__name__
            if (set(value) == {marker, 'items', '_serialized_type'} and value.get(marker) is True
                    and value.get('_serialized_type') == container.__name__):
                value = value['items']
        if not args:
            _error('Containers require element annotations', path, 'unsupported_annotation')
        if type(value) not in (list, tuple, set) or (container is list and type(value) is not list) or (container is tuple and type(value) is set):
            _error('Expected a collection', path, expected=annotation, actual=type(value))
        if container is tuple and not (len(args) == 2 and args[1] is Ellipsis):
            if len(value) != len(args):
                _error('Tuple length mismatch', path, expected=annotation, actual=type(value))
            annotations = args
        else:
            annotations = [args[0]] * len(value)
        children = [_plan(child, typ, f'{path}[{i}]', unknown, classes)
                    for i, (child, typ) in enumerate(zip(value, annotations))]
        def build(items):
            try:
                return container(items)
            except TypeError as error:
                raise DeserializationError('Unhashable set element', path, code='unhashable_element') from error
        return _Build(build, children)
    if container is dict:
        if len(args) != 2 or args[0] is not str:
            _error('Only Dict[str, T] is supported', path, 'unsupported_annotation')
        if not isinstance(value, dict):
            _error('Expected a dictionary', path, expected=annotation, actual=type(value))
        result = {}
        for key, child in value.items():
            if type(key) is not str:
                _error('Dictionary keys must be strings', path, expected=str, actual=type(key))
            result[key] = _plan(child, args[1], _child(path, key), unknown, classes)
        return result
    if not inspect.isclass(annotation):
        _error('Unsupported annotation', path, 'unsupported_annotation', annotation)
    from jsonic.pydantic_support import is_pydantic_class
    if is_pydantic_class(annotation):
        _error('Use native Pydantic validation for Pydantic models', path, 'unsupported_annotation')
    if not isinstance(value, dict):
        _error('Expected an object mapping', path, expected=annotation, actual=type(value))
    try:
        hints = typing.get_type_hints(annotation)
        init_hints = typing.get_type_hints(annotation.__init__)
        parameters = inspect.signature(annotation).parameters
    except (NameError, TypeError, ValueError, AttributeError) as error:
        raise DeserializationError('Cannot resolve schema annotations', path, code='unsupported_annotation') from error
    hints.update({key: typ for key, typ in init_hints.items() if key != 'return'})
    if dataclasses.is_dataclass(annotation):
        from jsonic.constructors import reject_required_initvars
        reject_required_initvars(annotation)
        fields = {field.name: field for field in dataclasses.fields(annotation)}
        hints = {key: hints[key] for key in fields if key in hints}
    else:
        fields = None
        if not hints:
            _error('Class requires annotated fields or constructor parameters', path, 'unsupported_annotation')
    from jsonic.serializable import Serializable
    metadata = Serializable.jsonic_types.get(full_type_name(annotation))
    mapping = metadata.init_parameters_mapping if metadata else {}
    transient = metadata.transient_attributes if metadata else ()
    for parameter, attribute in mapping.items():
        if parameter in hints:
            hints[attribute] = hints.pop(parameter)
    data = dict(value)
    if not isinstance(value, LiteralDict) and '_serialized_type' in data:
        if data.pop('_serialized_type') != full_type_name(annotation):
            _error('Type tag does not match the selected schema', path, 'tag_mismatch')
    extras = set(data) - set(hints)
    if extras and unknown == 'forbid':
        _error('Unknown field', _child(path, sorted(extras, key=str)[0]), 'unknown_field')
    parsed = {key: _plan(child, hints[key], _child(path, key), unknown, classes)
              for key, child in data.items() if key in hints}
    kwargs = {}
    for key, parameter in parameters.items():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        if parameter.kind == parameter.POSITIONAL_ONLY:
            _error('Positional-only constructors are unsupported', path, 'unsupported_annotation')
        attribute = mapping.get(key, key)
        if attribute in transient:
            if parameter.default is parameter.empty:
                _error('Required transient constructor field', _child(path, attribute), 'missing_field')
            continue
        if attribute in parsed:
            kwargs[key] = parsed[attribute]
        elif parameter.default is parameter.empty:
            _error('Missing required field', _child(path, attribute), 'missing_field')
    classes.add(annotation)
    def build(values):
        attributes = values
        arguments = {name: attributes[mapping.get(name, name)] for name in kwargs}
        from dataclasses import replace
        from jsonic.context import _traversal, current_context
        from jsonic.constructors import restore_attributes
        token = _traversal.set(replace(current_context(), path=path))
        try:
            instance = annotation(**arguments)
            # Constructor parameters remain authoritative; typed extra fields
            # follow normal immutable-invariant restoration.
            remaining = {key: child for key, child in attributes.items()
                         if key not in {mapping.get(name, name) for name in arguments}}
            restore_attributes(instance, remaining, transient, private=True)
            return instance
        finally:
            _traversal.reset(token)
    return _Build(build, parsed)


def _child(path, key):
    return f'{path}.{key}' if path else str(key)


def _json_value(value, path):
    if value is None or type(value) in (str, bool, int, float):
        return value
    if type(value) is list:
        return [_json_value(child, f'{path}[{i}]') for i, child in enumerate(value)]
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return {key: _json_value(child, _child(path, key)) for key, child in value.items()}
    _error('Any accepts only JSON values', path, actual=type(value))
