"""Shared constructor defaults and invariant-preserving attribute restoration."""
import dataclasses
import inspect

from jsonic.context import current_context
from jsonic.exceptions import DeserializationError, SerializationError
from jsonic.util import full_type_name, is_private_attribute


def constructor_kwargs(cls, data, mapping=None, transient=(), private=True):
    mapping = mapping or {}
    result = {}
    for name, parameter in inspect.signature(cls.__init__).parameters.items():
        if name == 'self' or parameter.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue
        if not private and is_private_attribute(name):
            continue
        attribute = mapping.get(name, name)
        if (name in transient or attribute in transient) and parameter.default is not inspect.Parameter.empty:
            continue
        if attribute in data:
            result[name] = data[attribute]
        elif parameter.default is inspect.Parameter.empty:
            if name in mapping:
                # Keep the historical missing-mapping exception catchable;
                # the defaulted mapping case above now correctly falls through.
                raise KeyError(attribute)
            raise DeserializationError(
                f'Missing attribute in given dict to match __init__ parameter: {name}.\n'
                f'If relevant, consider registering type "{full_type_name(cls)}" using '
                '"register_jsonic_type" and providing required "init_parameters_mapping".',
                current_context().path, code='missing_field', field=name
            )
    return result


def restore_attributes(instance, data, transient=(), private=True):
    frozen = dataclasses.is_dataclass(instance) and instance.__dataclass_params__.frozen
    for name, value in data.items():
        if name in transient or (not private and is_private_attribute(name)):
            continue
        if frozen:
            if not hasattr(instance, name) or getattr(instance, name) != value:
                raise DeserializationError(
                    'Stored field does not match the reconstructed frozen dataclass invariant',
                    current_context().child_path(name), code='immutable_field_mismatch', field=name
                )
        else:
            setattr(instance, name, value)


def reject_required_initvars(cls, serializing=False):
    # Dataclass Field metadata is the only distinction retained for string
    # annotations too; dataclasses.fields() deliberately omits InitVar entries.
    for name, field in cls.__dataclass_fields__.items():
        if field._field_type is not dataclasses._FIELD_INITVAR or not field.init:
            continue
        parameter = inspect.signature(cls.__init__).parameters.get(name)
        if (parameter is not None and parameter.default is inspect.Parameter.empty
                and parameter.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)):
            error = SerializationError if serializing else DeserializationError
            raise error(
                f'Required InitVar {name!r} is not persisted; use a custom codec to reconstruct it',
                current_context().path, code='unsupported_initvar', field=name
            )
