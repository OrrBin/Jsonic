from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List

import pytest
from hypothesis import given, strategies as st

from jsonic import Serializable, serialize, jsonic_serializer


@pytest.mark.parametrize('container', [list, tuple])
def test_root_collection_redacts_and_skips_unsupported(container):
    data = container([{'name': 'u', 'password': object()}])
    result = serialize(data, exclude={'password'})
    items = result if container is list else result['items']
    assert items == [{'name': 'u'}]


def test_excluded_cycles_and_hooks_are_not_visited():
    class Bad:
        pass
    @jsonic_serializer(Bad)
    def fail(value):
        raise AssertionError('excluded hook executed')
    cycle = {}
    cycle['self'] = cycle
    assert serialize({'ok': 1, 'bad': Bad(), 'cycle': cycle},
                     exclude={'bad', 'cycle'}) == {'ok': 1}


@pytest.mark.parametrize('shape', ['dataclass', 'registered', 'hinted', 'generic', 'slots'])
def test_excluded_object_fields_are_not_traversed(shape):
    if shape == 'dataclass':
        @dataclass
        class Record:
            ok: int
            bad: object
        obj = Record(1, object())
    else:
        base = Serializable if shape == 'registered' else object
        class Record(base):
            if shape == 'slots':
                __slots__ = ('ok', 'bad')
            def __init__(self):
                self.ok = 1
                self.bad = object()
        if shape == 'hinted':
            Record.__init__.__annotations__ = {'return': None, 'unused': int}
        obj = Record()
    assert serialize(obj, exclude={'bad'})['ok'] == 1
    assert 'bad' not in serialize(obj, exclude={'bad'})


def test_exclusion_wins_at_every_scope():
    assert serialize({'x': object()}, include={'x'}, exclude={'x'}) == {}
    assert serialize({'nested': [{'x': object(), 'y': 2}]},
                     include={'nested.x', 'nested.y'}, exclude={'nested.x'}) == {'nested': [{'y': 2}]}


@given(st.lists(st.dictionaries(st.sampled_from(['name', 'password']), st.integers()), max_size=15))
def test_redaction_across_nested_collections(records):
    result = serialize({'rows': [records]}, exclude={'rows.password'})
    assert all('password' not in row for row in result['rows'][0])


def test_dictionary_private_keys_and_nested_private_option_preserved():
    class Private(Serializable):
        def __init__(self):
            self._secret = 1
    result = serialize({'_user_key': Private()}, serialize_private_attributes=True)
    assert result['_user_key']['_secret'] == 1


def test_selection_does_not_leak_between_calls_or_threads():
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(serialize, {'x': 1, 'y': 2}, include={'x'})
        b = pool.submit(serialize, {'x': 1, 'y': 2}, exclude={'x'})
        assert a.result() == {'x': 1}
        assert b.result() == {'y': 2}
    assert serialize({'x': 1, 'y': 2}) == {'x': 1, 'y': 2}


def test_pydantic_excludes_before_field_serializer_runs():
    pydantic = pytest.importorskip('pydantic')
    if not hasattr(pydantic, 'field_serializer'):
        pytest.skip('Pydantic v2 field serializer')
    class Child(pydantic.BaseModel):
        secret: str
        name: str
        @pydantic.field_serializer('secret')
        def secret_serializer(self, value):
            raise AssertionError('excluded serializer ran')
    class Parent(pydantic.BaseModel):
        children: List[Child]
    value = Parent(children=[Child(secret='hidden', name='ok')])
    assert serialize(value, exclude={'children.secret'})['children'] == [{'name': 'ok'}]


def test_root_set_redacts_before_traversing_members():
    class Record:
        def __init__(self):
            self.name = 'ok'
            self.password = object()
    result = serialize({Record()}, exclude={'password'})
    assert result['_is_set'] is True
    assert result['items'][0]['name'] == 'ok'
    assert 'password' not in result['items'][0]


def test_custom_output_is_not_reinterpreted_when_no_filter_is_requested():
    class Record:
        pass
    @jsonic_serializer(Record)
    def encode(value):
        return {'_is_tuple': True}
    assert serialize(Record())['_is_tuple'] is True


def test_external_resolver_output_is_filtered(monkeypatch):
    from jsonic.type_resolver import TypeResolver, register_resolver, _registry
    monkeypatch.setattr(_registry, '_resolvers', list(_registry._resolvers))
    class Record:
        pass
    class Resolver(TypeResolver):
        def can_resolve(self, cls):
            return cls is Record
        def serialize(self, obj, private):
            return {'name': 'ok', 'password': object()}
        def deserialize(self, data, cls):
            return cls()
        def priority(self):
            return 200
    register_resolver(Resolver())
    result = serialize(Record(), exclude={'password'})
    assert result['name'] == 'ok'
    assert 'password' not in result
