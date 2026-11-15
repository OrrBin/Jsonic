"""Call-local authorization and failure cleanup, using harmless sentinels (#28)."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from unittest.mock import patch

import pytest

from jsonic import Serializable, deserialize, jsonic_deserializer, register_jsonic_type
from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name
from tests.support.models import GenericRecord, ResolverRecord
from jsonic.type_resolver import TypeResolver, register_resolver


def assert_independent_legacy_and_safe_calls():
    payload = {'_serialized_type': full_type_name(GenericRecord), 'value': 7}
    assert deserialize(payload).value == 7
    with pytest.raises(DeserializationError, match='not registered'):
        deserialize(payload, safe=True)


@pytest.mark.parametrize('failure', ['parse', 'tag', 'constructor', 'hook'])
def test_safe_policy_is_reset_after_each_failure_stage(failure):
    class Constructor(Serializable):
        def __init__(self):
            raise RuntimeError('constructor sentinel')
    class Hook:
        pass
    @jsonic_deserializer(Hook)
    def decode(data):
        raise RuntimeError('hook sentinel')
    if failure == 'parse':
        with pytest.raises(json.JSONDecodeError):
            deserialize('{', safe=True, string_input=True)
    elif failure == 'tag':
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize({'_serialized_type': 'never.registered'}, safe=True)
    else:
        tag = full_type_name(Constructor) if failure == 'constructor' else 'Hook'
        with pytest.raises(RuntimeError, match=failure + ' sentinel'):
            deserialize({'_serialized_type': tag}, safe=True)
    assert_independent_legacy_and_safe_calls()


@pytest.mark.parametrize('kind', ['codec', 'resolver'])
@pytest.mark.parametrize('text', [False, True])
def test_reentrant_decoder_cannot_downgrade_safe_policy(kind, text):
    calls = []
    forbidden = {'_serialized_type': full_type_name(GenericRecord), 'value': 7}
    def nested():
        calls.append('nested')
        return deserialize(json.dumps(forbidden) if text else forbidden,
                           string_input=text, safe=False)
    if kind == 'codec':
        class Reentrant:
            pass
        @jsonic_deserializer(Reentrant)
        def decode(data):
            return nested()
        payload = {'_serialized_type': 'Reentrant'}
    else:
        class ReentrantResolver(TypeResolver):
            def can_resolve(self, cls): return cls is ResolverRecord
            def serialize(self, obj, private=False): return {}
            def deserialize(self, data, cls): return nested()
            def priority(self): return 500
        register_resolver(ReentrantResolver())
        payload = {'_serialized_type': full_type_name(ResolverRecord)}
    kwargs = {'expected_type': ResolverRecord} if kind == 'resolver' else {}
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize(payload, safe=True, **kwargs)
        imports.assert_not_called()
    assert calls == ['nested']
    assert_independent_legacy_and_safe_calls()


@pytest.mark.parametrize('shape', ['list', 'dict', 'tuple', 'set', 'registered', 'pydantic'])
def test_preflight_blocks_all_earlier_hooks_under_every_adapter(shape):
    calls = []
    class Sentinel:
        pass
    @jsonic_deserializer(Sentinel)
    def decode(data):
        calls.append('hook')
        return Sentinel()
    values = [{'_serialized_type': 'Sentinel'}, {'_serialized_type': 'never.registered'}]
    if shape == 'list': payload = values
    elif shape == 'dict': payload = {'values': values}
    elif shape in ('tuple', 'set'):
        payload = {'_serialized_type': shape, '_is_' + shape: True, 'items': values}
    elif shape == 'registered':
        class Parent(Serializable):
            def __init__(self, values):
                calls.append('parent')
        payload = {'_serialized_type': full_type_name(Parent), 'values': values}
    else:
        pydantic = pytest.importorskip('pydantic')
        class Parent(pydantic.BaseModel):
            values: list
        register_jsonic_type(Parent)
        payload = {'_serialized_type': full_type_name(Parent), 'values': values}
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize(payload, safe=True)
        imports.assert_not_called()
    assert calls == []


def test_registration_during_a_call_does_not_expand_its_authorization_snapshot():
    calls = []
    class NewType:
        def __init__(self): calls.append('new constructed')
    class Trigger:
        pass
    @jsonic_deserializer(Trigger)
    def decode(data):
        register_jsonic_type(NewType)
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize({'_serialized_type': full_type_name(NewType)}, safe=False)
        return Trigger()
    assert isinstance(deserialize({'_serialized_type': 'Trigger'}, safe=True), Trigger)
    assert calls == []
    assert isinstance(deserialize({'_serialized_type': full_type_name(NewType)}, safe=True), NewType)
    assert calls == ['new constructed']


def test_alias_registration_in_another_thread_waits_for_next_safe_call():
    entered, release = threading.Event(), threading.Event()
    class NewType:
        pass
    class Trigger:
        pass
    @jsonic_deserializer(Trigger)
    def decode(data):
        entered.set()
        assert release.wait(5)
        return deserialize({'_serialized_type': 'new:alias'}, safe=False)
    with ThreadPoolExecutor(max_workers=1) as pool:
        worker = pool.submit(deserialize, {'_serialized_type': 'Trigger'}, safe=True)
        try:
            assert entered.wait(5)
            jsonic_deserializer(NewType, type_id='new:alias')(lambda data: NewType())
        finally:
            release.set()
        with pytest.raises(DeserializationError, match='not registered'):
            worker.result(timeout=5)
    assert isinstance(deserialize({'_serialized_type': 'new:alias'}, safe=True), NewType)
    assert_independent_legacy_and_safe_calls()


def test_async_task_inheritance_is_separate_from_independent_task_contexts():
    async def scenario():
        inherited = []
        async def child():
            await asyncio.sleep(0)
            with pytest.raises(DeserializationError, match='not registered'):
                deserialize({'_serialized_type': full_type_name(GenericRecord), 'value': 7}, safe=False)
        class Trigger:
            pass
        @jsonic_deserializer(Trigger)
        def decode(data):
            inherited.append(asyncio.create_task(child()))
            return Trigger()
        async def safe_task():
            await asyncio.sleep(0)
            deserialize({'_serialized_type': 'Trigger'}, safe=True)
            await asyncio.wait_for(inherited[0], timeout=5)
        async def independent_task():
            await asyncio.sleep(0)
            assert_independent_legacy_and_safe_calls()
        await asyncio.gather(safe_task(), independent_task())
        assert_independent_legacy_and_safe_calls()
    asyncio.run(scenario())
