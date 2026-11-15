"""Reachable failure branches and atomic codec registration (#26)."""
from copy import deepcopy
import json
from unittest.mock import patch

import pytest

from jsonic import Serializable, deserialize, serialize, jsonic_serializer, jsonic_deserializer, register_jsonic_type
from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer
from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name


def registry_snapshot():
    return [dict(mapping) for mapping in (
        _JsonicSerializer.serializers, _JsonicSerializer.type_ids, _JsonicSerializer.types,
        _JsonicDeserializer.deserializers, _JsonicDeserializer.types)]


@pytest.mark.parametrize('decorator', [jsonic_serializer, jsonic_deserializer])
@pytest.mark.parametrize('invalid', [None, 'Example', 1, object()])
def test_decorators_require_types_without_mutating_registry(decorator, invalid):
    before = registry_snapshot()
    with pytest.raises(TypeError, match='requires a Python type'):
        decorator(invalid)(lambda value: {})
    assert registry_snapshot() == before


@pytest.mark.parametrize('aliases', [('',), (17,), ('valid', '')])
def test_invalid_alias_registration_is_atomic(aliases):
    class Record:
        pass
    before = registry_snapshot()
    with pytest.raises(ValueError, match='nonempty strings'):
        jsonic_deserializer(Record, aliases=aliases)(lambda value: Record())
    assert registry_snapshot() == before


def test_decorated_wrappers_remain_callable():
    class Record:
        def __init__(self, value):
            self.value = value
    @jsonic_serializer(Record)
    def encode(record):
        return {'value': record.value}
    @jsonic_deserializer(Record)
    def decode(data):
        return Record(data['value'])
    assert encode(Record(7)) == {'value': 7}
    assert decode({'value': 9}).value == 9


@pytest.mark.parametrize('tag', [7, [], {}])
def test_nonstring_tag_rejected_before_import_or_dispatch(tag):
    payload = {'_serialized_type': tag}
    before = deepcopy(payload)
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='Type tag must be a string'):
            deserialize(payload, expected_type=dict)
        imports.assert_not_called()
    assert payload == before


@pytest.mark.parametrize('expected', ['dict', 42, list[int] if hasattr(list, '__class_getitem__') else 'List[int]'])
def test_expected_type_requires_a_concrete_python_type(expected):
    with pytest.raises(TypeError, match='concrete Python type'):
        deserialize({}, expected_type=expected)


@pytest.mark.parametrize('payload', [{}, [], None, 3])
def test_safe_string_input_requires_text(payload):
    with pytest.raises(TypeError, match='string_input requires str'):
        deserialize(payload, safe=True, string_input=True)
    assert deserialize([1], safe=True) == [1]


def test_json_parse_error_is_not_replaced_by_dispatch_error():
    with pytest.raises(json.JSONDecodeError):
        deserialize('{', safe=True, string_input=True)


def test_nested_custom_type_error_has_wrapper_path_and_original_context():
    class Broken:
        pass
    original = AttributeError('decoder sentinel')
    @jsonic_deserializer(Broken)
    def decode(data):
        raise original
    payload = {'rows': [{'_serialized_type': 'Broken'}]}
    with pytest.raises(DeserializationError, match='decoder sentinel') as error:
        deserialize(payload, safe=True)
    assert error.value.path == 'rows[0]'
    assert error.value.__context__ is original


def test_unresolvable_type_hints_fall_back_without_losing_data():
    class Forward:
        def __init__(self, value: 'NotAnImportedType'):
            self.value = value
    value = Forward(7)
    payload = serialize(value)
    assert payload['value'] == 7
    assert deserialize(payload, expected_type=Forward).value == 7


def test_typehinted_defaults_are_used_when_omitted():
    class Defaulted:
        def __init__(self, value: int = 7):
            self.value = value
    payload = {'_serialized_type': full_type_name(Defaulted)}
    assert deserialize(payload, expected_type=Defaulted).value == 7


def test_unknown_type_with_empty_registry_has_no_misleading_suggestions(monkeypatch):
    monkeypatch.setattr(Serializable, 'jsonic_types', {})
    with pytest.raises(TypeError, match='Could not find type: never_imported.Unknown') as error:
        deserialize({'_serialized_type': 'never_imported.Unknown'})
    assert 'Registered types' not in str(error.value)
    assert 'Did you mean' not in str(error.value)


def test_unrelated_registry_suggestions_are_bounded(monkeypatch):
    monkeypatch.setattr(Serializable, 'jsonic_types', {})
    names = []
    for i in range(8):
        cls = type('RecordNumber' + str(i), (), {'__module__': 'example_models'})
        register_jsonic_type(cls)
        names.append(full_type_name(cls))
    with pytest.raises(TypeError) as error:
        deserialize({'_serialized_type': 'missing_package.ZzzUnrelated'})
    message = str(error.value)
    assert all(name in message for name in names[:5])
    assert all(name not in message for name in names[5:])
    assert 'and 3 more' in message


def test_legacy_enum_payload_without_member_name_can_reconstruct_by_value():
    from enum import Enum
    class Number(Enum):
        ONE = 1
    payload = {'_serialized_type': full_type_name(Number), 'name': None, 'value': 1}
    assert deserialize(payload, expected_type=Number, safe=True) is Number.ONE
