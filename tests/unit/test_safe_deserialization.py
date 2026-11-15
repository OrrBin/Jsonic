"""Harmless side-effect sentinels for the safe decoding boundary."""
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from jsonic import deserialize, serialize, register_jsonic_type, Serializable
from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name


@dataclass
class SafeRecord:
    value: int


@pytest.mark.parametrize('wrap', [
    lambda v: v,
    lambda v: {'child': [v]},
    lambda v: {'_serialized_type': 'tuple', '_is_tuple': True, 'items': [v]},
    lambda v: {'_serialized_type': 'set', '_is_set': True, 'items': [v]},
])
def test_unknown_nested_tags_never_import(wrap):
    payload = wrap({'_serialized_type': 'harmless_probe.Unregistered'})
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize(payload, safe=True)
        imports.assert_not_called()


def test_preflight_rejects_before_any_constructor():
    calls = []
    class Registered(Serializable):
        def __init__(self):
            calls.append('called')
    payload = [{'_serialized_type': full_type_name(Registered)},
               {'_serialized_type': 'harmless_probe.Unknown'}]
    with pytest.raises(DeserializationError):
        deserialize(payload, safe=True)
    assert calls == []


def test_registered_and_explicit_expected_type_without_imports():
    payload = serialize(SafeRecord(4))
    with patch('jsonic.serializable.importlib.import_module') as imports:
        assert deserialize(payload, expected_type=SafeRecord, safe=True) == SafeRecord(4)
        register_jsonic_type(SafeRecord)
        assert deserialize(json.dumps(payload), string_input=True, safe=True) == SafeRecord(4)
        imports.assert_not_called()


def test_expected_type_mismatch_does_not_import_in_legacy_mode():
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError):
            deserialize({'_serialized_type': 'harmless_probe.Unknown'}, expected_type=SafeRecord)
        imports.assert_not_called()


@pytest.mark.parametrize('payload', [
    {'_serialized_type': ['not', 'a', 'tag']},
    {'_serialized_type': 'tuple', '_is_tuple': 1, 'items': []},
    {'_is_tuple': True, 'items': []},
    {'_serialized_type': 'set', '_is_set': True, 'items': {}},
])
def test_malformed_tags_and_envelopes_rejected(payload):
    with pytest.raises(DeserializationError):
        deserialize(payload, safe=True)


def test_policy_resets_on_failure_and_isolated_between_threads():
    payload = serialize(SafeRecord(4))
    with ThreadPoolExecutor(max_workers=2) as pool:
        safe = pool.submit(deserialize, payload, safe=True)
        legacy = pool.submit(deserialize, payload)
        with pytest.raises(DeserializationError):
            safe.result()
        assert legacy.result() == SafeRecord(4)
    assert deserialize(payload) == SafeRecord(4)


def test_pydantic_preflight_rejects_nested_tag_before_validation():
    pydantic = pytest.importorskip('pydantic')
    class Model(pydantic.BaseModel):
        child: dict
    register_jsonic_type(Model)
    payload = {'_serialized_type': full_type_name(Model),
               'child': {'_serialized_type': 'harmless_probe.Unknown'}}
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError):
            deserialize(payload, safe=True)
        imports.assert_not_called()
