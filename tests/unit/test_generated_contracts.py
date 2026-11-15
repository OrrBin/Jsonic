"""Bounded generated trees plus explicit adapter/container option matrices (#27)."""
from copy import deepcopy

import pytest
from hypothesis import given, settings, strategies as st

from jsonic import deserialize, serialize
from tests.support.models import ADAPTERS, prepare_adapter


SCALARS = st.one_of(st.none(), st.booleans(), st.integers(min_value=-(2**80), max_value=2**80),
                    st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=24))
TREES = st.recursive(SCALARS, lambda child: st.one_of(
    st.lists(child, max_size=4), st.lists(child, max_size=4).map(tuple),
    st.dictionaries(st.text(alphabet='abcde', max_size=5), child, max_size=4),
    st.sets(SCALARS, max_size=4)), max_leaves=15)


def assert_same_tree(actual, expected):
    assert type(actual) is type(expected)
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            assert_same_tree(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            assert_same_tree(a, b)
    else:
        assert actual == expected


@pytest.mark.parametrize('text', [False, True])
@settings(max_examples=50, derandomize=True, deadline=None)
@given(tree=TREES)
def test_generated_supported_trees_preserve_values_and_container_types(tree, text):
    before = deepcopy(tree)
    payload = serialize(tree, string_output=text)
    wire_before = deepcopy(payload)
    restored = deserialize(payload, expected_type=type(tree), string_input=text, safe=True)
    assert_same_tree(restored, before)
    assert_same_tree(tree, before)
    assert payload == wire_before


WRAPPERS = {
    'root': (lambda v: v, lambda v: v),
    'list': (lambda v: [v], lambda v: v[0]),
    'dict': (lambda v: {'record': v}, lambda v: v['record']),
    'tuple': (lambda v: (v,), lambda v: v[0]),
    'set': (lambda v: {v}, lambda v: next(iter(v))),
}


@pytest.mark.parametrize('adapter', sorted(ADAPTERS))
@pytest.mark.parametrize('shape', sorted(WRAPPERS))
@pytest.mark.parametrize('text', [False, True])
@settings(max_examples=15, derandomize=True, deadline=None)
@given(value=SCALARS)
def test_generated_adapter_roundtrips(adapter, shape, text, value):
    cls = prepare_adapter(adapter)
    source = cls(value)
    wrap, unwrap = WRAPPERS[shape]
    root = wrap(source)
    payload = serialize(root, string_output=text)
    before = deepcopy(payload)
    result = deserialize(payload, string_input=text, expected_type=type(root))
    restored = unwrap(result)
    assert type(restored) is cls
    assert type(restored.value) is type(value)
    assert restored.value == value
    assert source.value == value
    assert source._private == 'initial'
    assert payload == before


@pytest.mark.parametrize('adapter', sorted(ADAPTERS))
def test_root_adapter_safe_decoding_authorized_by_expected_type(adapter):
    cls = prepare_adapter(adapter)
    assert deserialize(serialize(cls(7)), expected_type=cls, safe=True).value == 7


@pytest.mark.parametrize('adapter', ['generic', 'hinted', 'dataclass', 'slots', 'registered', 'resolver'])
@pytest.mark.parametrize('shape', sorted(WRAPPERS))
def test_selection_precedence_matches_simple_reference_rule(adapter, shape):
    cls = prepare_adapter(adapter)
    root = WRAPPERS[shape][0](cls('keep'))
    def record(wire):
        if shape == 'list': return wire[0]
        if shape == 'dict': return wire['record']
        if shape in ('set', 'tuple'): return wire['items'][0]
        return wire
    prefix = 'record.' if shape == 'dict' else ''
    payload = serialize(root, include={prefix + 'value', prefix + '_private'}, exclude={prefix + '_private'})
    selected = record(payload)
    assert {k: v for k, v in selected.items() if k != '_serialized_type'} == {'value': 'keep'}


@pytest.mark.parametrize('shape', ['root', 'list', 'dict',
    pytest.param('tuple', marks=pytest.mark.xfail(strict=True, raises=AssertionError, reason='F08/#10: tuple private option')),
    pytest.param('set', marks=pytest.mark.xfail(strict=True, raises=AssertionError, reason='F08/#10: set private option')),
])
def test_private_option_survives_supported_container_boundaries(shape):
    cls = prepare_adapter('registered')
    source = cls(1, _private='changed')
    wrap, unwrap = WRAPPERS[shape]
    payload = serialize(wrap(source), serialize_private_attributes=True)
    restored = unwrap(deserialize(payload, deserialize_private_attributes=True))
    assert restored._private == 'changed'
    assert source._private == 'changed'


@pytest.mark.xfail(strict=True, raises=AssertionError, reason='F11/#13: literal metadata dictionary is reinterpreted')
def test_reserved_key_regression_is_not_blessed_as_a_roundtrip():
    literal = {'_is_tuple': True, 'items': [1], 'label': 'keep'}
    assert deserialize(serialize(literal)) == literal


def test_repeated_references_do_not_imply_graph_identity_preservation():
    shared = {'value': [1]}
    restored = deserialize(serialize([shared, shared]), safe=True)
    assert restored == [shared, shared]
    assert restored[0] is not restored[1]


def test_excluded_cycle_does_not_break_independent_shared_values():
    cycle = {}
    cycle['self'] = cycle
    assert serialize({'ok': [1], 'cycle': cycle}, exclude={'cycle'}) == {'ok': [1]}
