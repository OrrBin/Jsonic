import copy
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import pytest
from hypothesis import given, settings, strategies as st

from jsonic import serialize, deserialize, register_jsonic_type
from jsonic.exceptions import DeserializationError
from jsonic.wire import TAG

json_values = st.recursive(st.none() | st.booleans() | st.integers() | st.text(),
    lambda child: st.lists(child, max_size=4) | st.dictionaries(
        st.sampled_from(['_serialized_type', '_is_tuple', '_is_set', 'items', 'payload', 'version', '$jsonic', 'x']),
        child, max_size=5), max_leaves=20)


@settings(max_examples=80, derandomize=True, deadline=None)
@given(json_values)
def test_arbitrary_json_dictionary_identity(value):
    original = copy.deepcopy(value)
    wire = serialize(value, wire_format='v2', string_output=True)
    assert deserialize(wire, string_input=True, wire_format='v2', safe=True) == value
    assert value == original


@pytest.mark.parametrize('literal', [
    {'_serialized_type': 'os.system', '_is_tuple': True, 'items': [1], 'label': 'keep'},
    {'_serialized_type': TAG, 'version': 2, 'payload': ['value', 7]},
    {'_is_set': True, 'items': [], 'nested': {'_serialized_type': ['not', 'a tag']}},
])
def test_literals_inside_objects_containers_and_codecs(literal):
    @dataclass
    class Record:
        data: dict
        identifier: UUID
    register_jsonic_type(Record)
    source = (Record(literal, UUID(int=7)), [literal], datetime(2026, 1, 1), {1, 2})
    wire = serialize(source, wire_format='v2', uuid_format='string')
    result = deserialize(wire, wire_format='v2', safe=True)
    assert type(result) is tuple and type(result[0]) is Record
    assert result == source


@pytest.mark.parametrize('payload', [
    {}, {'_serialized_type': TAG, 'version': True, 'payload': ['value', 1]},
    {'_serialized_type': TAG, 'version': 2, 'payload': ['value', {}]},
    {'_serialized_type': TAG, 'version': 2, 'payload': ['dict', [['x', ['value', 1]], ['x', ['value', 2]]]]},
    {'_serialized_type': TAG, 'version': 2, 'payload': ['object', [['_serialized_type', ['value', 'tuple']], ['items', ['list', []]]]]},
    {'_serialized_type': TAG, 'version': 2, 'payload': ['mystery', []]},
])
def test_malformed_envelopes_are_rejected_without_mutation(payload):
    before = copy.deepcopy(payload)
    with pytest.raises(DeserializationError) as error:
        deserialize(payload, wire_format='v2', safe=True)
    assert error.value.code == 'invalid_envelope'
    assert payload == before


def test_safe_preflight_rejects_real_tags_but_not_literal_tags():
    @dataclass
    class Unknown:
        value: int
    wire = serialize([{'_serialized_type': 'literal'}, Unknown(2)], wire_format='v2')
    with pytest.raises(DeserializationError, match='not registered'):
        deserialize(wire, wire_format='v2', safe=True)


def test_v2_requires_explicit_reader_and_legacy_is_unchanged():
    assert serialize((1,)) == {'items': [1], '_is_tuple': True, '_serialized_type': 'tuple'}
    assert deserialize(serialize((1,))) == (1,)
    with pytest.raises(DeserializationError):
        deserialize(serialize({'x': 1}, wire_format='v2'), safe=True)
    with pytest.raises(DeserializationError, match='envelope'):
        deserialize({'x': 1}, wire_format='v2')


def test_selection_and_expected_literal_dict_type():
    source = {'_serialized_type': 'literal', 'child': {'_is_tuple': True, 'password': 'secret'}}
    wire = serialize(source, wire_format='v2', exclude={'child.password'})
    assert deserialize(wire, wire_format='v2', expected_type=dict, safe=True) == {
        '_serialized_type': 'literal', 'child': {'_is_tuple': True}}
    assert deserialize(serialize(1), expected_type=int) == 1  # no context leakage


def test_custom_codec_context_selection_preserves_literal_identity():
    from jsonic import jsonic_serializer, jsonic_deserializer
    from jsonic.context import current_context
    class Box:
        def __init__(self, data):
            self.data = data
    @jsonic_serializer(Box)
    def write(value):
        return {'data': current_context().serialize(value.data, 'data')}
    @jsonic_deserializer(Box)
    def read(data):
        return Box(current_context().deserialize(data['data'], 'data'))
    source = Box({'_serialized_type': 'literal', '_is_tuple': True, 'secret': 'x'})
    result = deserialize(serialize(source, wire_format='v2', exclude={'data.secret'}),
                         wire_format='v2', safe=True)
    assert result.data == {'_serialized_type': 'literal', '_is_tuple': True}


def test_malformed_sibling_prevents_earlier_constructor():
    calls = []
    @dataclass
    class Record:
        value: int
        def __post_init__(self):
            calls.append(self.value)
    register_jsonic_type(Record)
    wire = serialize([Record(1), 2], wire_format='v2')
    calls.clear()
    wire['payload'][1][1] = ['value', {'not': 'primitive'}]
    with pytest.raises(DeserializationError):
        deserialize(wire, wire_format='v2', safe=True)
    assert calls == []


def test_json_key_normalization():
    value = {True: 'boolean', None: 'null', 2: 'integer'}
    assert deserialize(serialize(value, wire_format='v2'), wire_format='v2', safe=True) == {
        'true': 'boolean', 'null': 'null', '2': 'integer'}


@pytest.mark.parametrize('node', [None, [], [1, 2], ['dict', {}], ['object', []],
    ['object', [['_serialized_type', ['value', 'example.Tag']], ['_is_tuple', ['value', True]]]]])
def test_invalid_node_shapes(node):
    with pytest.raises(DeserializationError) as error:
        deserialize({'_serialized_type': TAG, 'version': 2, 'payload': node}, wire_format='v2')
    assert error.value.code == 'invalid_envelope'


def test_cyclic_python_envelope_rejected_without_recursion():
    node = ['list', []]
    node[1].append(node)
    with pytest.raises(DeserializationError) as error:
        deserialize({'_serialized_type': TAG, 'version': 2, 'payload': node}, wire_format='v2')
    assert error.value.code == 'circular_reference'
