"""Option/path propagation through nested built-in adapters (#10)."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from unittest.mock import patch

import pytest

from jsonic import Serializable, deserialize, serialize
from jsonic.context import current_context, TraversalContext
from jsonic.exceptions import SerializationError, DeserializationError
from jsonic.util import full_type_name


class Private(Serializable):
    def __init__(self, value=1):
        self.value = value
        self._secret = 'default'


@pytest.mark.parametrize('private', [False, True])
@pytest.mark.parametrize('wrap,unwrap', [
    (lambda v: (v,), lambda v: v[0]),
    (lambda v: {v}, lambda v: next(iter(v))),
    (lambda v: {'rows': [(v,)]}, lambda v: v['rows'][0][0]),
    (lambda v: ({v},), lambda v: next(iter(v[0]))),
])
def test_nested_private_options_in_both_directions(private, wrap, unwrap):
    source = Private()
    source._secret = 'changed'
    payload = serialize(wrap(source), serialize_private_attributes=private)
    before = deepcopy(payload)
    restored = unwrap(deserialize(payload, deserialize_private_attributes=private, safe=True))
    assert restored._secret == ('changed' if private else 'default')
    assert source._secret == 'changed'
    assert payload == before


@pytest.mark.parametrize('kind', ['tuple', 'set'])
def test_adapter_error_path_keeps_parent_and_index(kind):
    value = (object(),) if kind == 'tuple' else {object()}
    with pytest.raises(SerializationError) as error:
        serialize({'rows': [value]})
    assert error.value.path == 'rows[0][0]'


def test_decode_private_option_not_confused_with_constructor_default():
    payload = {'_serialized_type': 'tuple', '_is_tuple': True, 'items': [
        {'_serialized_type': full_type_name(Private), 'value': 1, '_secret': 'wire value'}]}
    assert deserialize(payload, deserialize_private_attributes=True)[0]._secret == 'wire value'
    assert deserialize(payload, deserialize_private_attributes=False)[0]._secret == 'default'


def test_context_resets_after_failures_and_between_threads():
    def run(private):
        with pytest.raises(SerializationError):
            serialize((object(),), serialize_private_attributes=private)
        with pytest.raises(DeserializationError):
            deserialize({'_serialized_type': 'unregistered'}, safe=True, deserialize_private_attributes=private)
        assert current_context() == TraversalContext()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, private) for private in (False, True)]
        for future in futures: future.result(timeout=5)
    assert current_context() == TraversalContext()


def test_safe_nested_rejection_still_precedes_imports():
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError):
            deserialize({'_serialized_type': 'tuple', '_is_tuple': True,
                         'items': [{'_serialized_type': 'unregistered'}]}, safe=True)
        imports.assert_not_called()
