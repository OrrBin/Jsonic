"""Reject cycles before exhausting Python's stack; retain acyclic sharing."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import dataclass
from typing import Any

import pytest

from jsonic import serialize, jsonic_serializer
from jsonic.context import current_context, TraversalContext
from jsonic.type_resolver import TypeResolver, register_resolver


@pytest.mark.parametrize('shape', ['list', 'dict', 'tuple_list', 'dataclass'])
def test_cyclic_values_are_rejected_without_source_mutation(shape):
    if shape == 'list':
        value = []; value.append(value)
    elif shape == 'dict':
        value = {}; value['child'] = value
    elif shape == 'tuple_list':
        value = []; value.append((value,))
    else:
        @dataclass
        class Node:
            child: Any = None
        value = Node(); value.child = value
    with pytest.raises(ValueError, match='Circular reference'):
        serialize(value)
    assert current_context() == TraversalContext()
    if shape == 'dict': assert value['child'] is value
    elif shape == 'dataclass': assert value.child is value
    elif shape == 'list': assert value[0] is value
    else: assert value[0][0] is value


def test_resolver_is_not_recursively_reentered_for_a_cycle():
    calls = []
    class Node:
        def __init__(self): self.child = self
    class Adapter(TypeResolver):
        def can_resolve(self, cls): return cls is Node
        def priority(self): return 500
        def serialize(self, value, *, context):
            calls.append('called')
            return {'child': context.serialize(value.child, 'child')}
        def deserialize(self, data, cls): return cls()
    register_resolver(Adapter())
    with pytest.raises(ValueError, match='Circular reference'):
        serialize(Node())
    assert calls == ['called']


def test_cycles_in_raw_custom_codec_output_are_rejected():
    class Model: pass
    raw = {}; raw['child'] = raw
    jsonic_serializer(Model)(lambda value: raw)
    with pytest.raises(ValueError, match='Circular reference'):
        serialize(Model())
    assert raw['child'] is raw


def test_shared_raw_codec_mapping_is_not_treated_as_a_cycle():
    class Model: pass
    shared = {'value': 7}
    jsonic_serializer(Model)(lambda value: {'a': shared, 'b': shared})
    result = serialize(Model())
    assert result['a'] == result['b'] == {'value': 7}
    assert result['a'] is not result['b']


def test_completed_frames_in_copied_task_contexts_are_inactive():
    async def scenario():
        tasks, calls = [], []
        class Model: pass
        value = Model()
        async def later():
            await asyncio.sleep(0)
            return serialize(value)
        @jsonic_serializer(Model)
        def encode(obj):
            calls.append('called')
            if len(calls) == 1: tasks.append(asyncio.create_task(later()))
            return {'value': 7}
        assert serialize(value)['value'] == 7
        assert (await asyncio.wait_for(tasks[0], timeout=5))['value'] == 7
        assert len(calls) == 2
    asyncio.run(scenario())


def test_copied_context_in_another_thread_has_an_independent_ancestor_path():
    class Model: pass
    calls = []
    with ThreadPoolExecutor(max_workers=1) as pool:
        @jsonic_serializer(Model)
        def encode(value):
            calls.append('called')
            if len(calls) == 1:
                result = pool.submit(copy_context().run, serialize, value).result(timeout=5)
                assert result['value'] == 7
            return {'value': 7}
        assert serialize(Model())['value'] == 7
    assert len(calls) == 2
