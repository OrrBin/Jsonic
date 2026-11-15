import json
from datetime import datetime
from enum import Enum
from types import new_class
from unittest.mock import patch

import pytest

from jsonic import deserialize, serialize, jsonic_serializer, jsonic_deserializer
from jsonic.exceptions import DeserializationError


class Color(Enum):
    RED = 1


@pytest.mark.parametrize('value', [None, True, 2, 2.5, 's', [1], {'x': 1}, (1,), {1},
                                  datetime(2026, 1, 1), complex(1, 2), Color.RED])
@pytest.mark.parametrize('as_text', [False, True])
def test_exact_expected_types_accept_and_reject(value, as_text):
    data = serialize(value)
    if as_text:
        data = json.dumps(data)
    assert deserialize(data, expected_type=type(value), string_input=as_text) == value
    with pytest.raises(DeserializationError):
        deserialize(data, expected_type=bytes, string_input=as_text)


def test_bool_does_not_satisfy_int_and_subclass_does_not_satisfy_base():
    with pytest.raises(DeserializationError):
        deserialize(True, expected_type=int)
    with pytest.raises(DeserializationError):
        deserialize([], expected_type=object)


def test_mismatch_never_invokes_decoder_or_imports():
    class Value:
        pass
    calls = []
    @jsonic_deserializer(Value)
    def decode(data):
        calls.append(True)
        return Value()
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError):
            deserialize({'_serialized_type': 'Value'}, expected_type=dict)
        imports.assert_not_called()
    assert calls == []


def test_bad_decoder_return_type_is_rejected():
    class Value:
        pass
    @jsonic_deserializer(Value)
    def decode(data):
        return 'wrong'
    with pytest.raises(DeserializationError):
        deserialize({'_serialized_type': 'Value'}, expected_type=Value)


def test_same_name_types_use_explicit_ids_and_legacy_aliases():
    first = new_class('SameName')
    first.__module__ = 'first_module'
    second = new_class('SameName')
    second.__module__ = 'second_module'
    for typ, tag in ((first, 'first:v1'), (second, 'second:v1')):
        jsonic_serializer(typ, type_id=tag)(lambda obj: {'value': 1})
        jsonic_deserializer(typ, type_id=tag)(lambda data, typ=typ: typ())
    for typ in (first, second):
        restored = deserialize(serialize(typ()), expected_type=typ, safe=True)
        assert type(restored) is typ
    # Qualified IDs are available even when explicit stable IDs are used.
    assert type(deserialize({'_serialized_type': 'first_module.SameName'}, safe=True)) is first


def test_ambiguous_short_registration_is_rejected_atomically():
    first, second = new_class('SameName'), new_class('SameName')
    first.__module__, second.__module__ = 'first_module', 'second_module'
    jsonic_deserializer(first)(lambda data: first())
    with pytest.raises(ValueError, match='Ambiguous'):
        jsonic_deserializer(second)(lambda data: second())
    assert type(deserialize({'_serialized_type': 'SameName'}, safe=True)) is first
    with pytest.raises(DeserializationError):
        deserialize({'_serialized_type': 'second_module.SameName'}, safe=True)


def test_explicit_legacy_alias():
    class Renamed:
        pass
    jsonic_deserializer(Renamed, type_id='app:renamed:v2', aliases=('OldName',))(lambda data: Renamed())
    assert type(deserialize({'_serialized_type': 'OldName'}, expected_type=Renamed, safe=True)) is Renamed


@pytest.mark.parametrize('encoder_first', [False, True])
def test_codec_identity_cannot_be_hijacked_across_registration_order(encoder_first):
    class First:
        pass
    class Second:
        pass
    if encoder_first:
        jsonic_serializer(First, type_id='unique:v1')(lambda value: {})
        register_conflict = jsonic_deserializer(Second, type_id='unique:v1')
    else:
        jsonic_deserializer(First, type_id='unique:v1')(lambda value: First())
        register_conflict = jsonic_serializer(Second, type_id='unique:v1')
    with pytest.raises(ValueError, match='Ambiguous'):
        register_conflict(lambda value: {})


@pytest.mark.parametrize('decorator', [jsonic_serializer, jsonic_deserializer])
@pytest.mark.parametrize('type_id', ['', 7])
def test_invalid_explicit_ids_rejected(decorator, type_id):
    class Value:
        pass
    with pytest.raises(ValueError):
        decorator(Value, type_id=type_id)(lambda value: {})
