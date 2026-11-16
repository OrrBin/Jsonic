"""Both historical signatures and the opt-in context protocol are executable."""
from dataclasses import FrozenInstanceError

import pytest

from jsonic import TraversalContext, Serializable, deserialize, serialize
from jsonic.context import current_context
from jsonic.exceptions import SerializationError, DeserializationError
from jsonic.type_resolver import TypeResolver, register_resolver


class Target:
    def __init__(self, value): self.value = value


class Resolver(TypeResolver):
    def can_resolve(self, cls): return cls is Target
    def priority(self): return 500
    def deserialize(self, data, cls): return cls(**data)


@pytest.mark.parametrize('style', ['public', 'legacy', 'context', 'legacy_context'])
def test_serialization_signatures_and_deserialization_context(style):
    calls = []
    class Adapter(Resolver):
        if style == 'public':
            def serialize(self, obj):
                calls.append(('serialize',))
                return {'value': obj.value}
        elif style == 'legacy':
            def serialize(self, obj, private):
                calls.append(('serialize', private))
                return {'value': obj.value}
        elif style == 'context':
            def serialize(self, obj, *, context):
                calls.append(('serialize', context.path, context.serialize_private_attributes))
                return {'value': context.serialize(obj.value, 'value')}
        else:
            def serialize(self, obj, private, *, context=None):
                calls.append(('serialize', private, context.path))
                return {'value': context.serialize(obj.value, 'value')}
        def deserialize(self, data, cls, *, context):
            assert type(data['value']) is int  # Dispatcher already decoded it.
            calls.append(('deserialize', context.path, context.deserialize_private_attributes))
            return cls(**data)
    register_resolver(Adapter())
    payload = serialize({'nested': Target(7)}, serialize_private_attributes=True)
    restored = deserialize(payload, deserialize_private_attributes=True)
    assert restored['nested'].value == 7
    assert len(calls) == 2
    assert calls[-1] == ('deserialize', 'nested', True)
    if style == 'context': assert calls[0] == ('serialize', 'nested', True)
    elif style == 'legacy_context': assert calls[0] == ('serialize', True, 'nested')
    elif style == 'legacy': assert calls[0] == ('serialize', True)
    else: assert calls[0] == ('serialize',)


def test_context_recursion_preserves_paths_private_flags_and_selection():
    class Child(Serializable):
        def __init__(self):
            self.value = 1
            self._secret = 'changed'
    class Adapter(Resolver):
        def serialize(self, obj, *, context):
            return {'value': context.serialize(obj.value, 'value')}
    register_resolver(Adapter())
    payload = serialize({'nested': Target((Child(),))}, serialize_private_attributes=True,
                        exclude={'nested.value._secret'})
    child = payload['nested']['value']['items'][0]
    assert child['value'] == 1
    assert '_secret' not in child
    with pytest.raises(SerializationError) as error:
        serialize({'nested': Target((object(),))})
    assert error.value.path == 'nested.value[0]'


@pytest.mark.parametrize('phase', ['serialize', 'deserialize'])
def test_callback_internal_typeerror_is_never_retried_as_signature_detection(phase):
    calls = []
    original = TypeError('user callback sentinel')
    class Adapter(Resolver):
        def serialize(self, obj, *, context=None):
            if phase == 'serialize':
                calls.append('serialize')
                raise original
            return {'value': obj.value}
        def deserialize(self, data, cls, *, context=None):
            calls.append('deserialize')
            raise original
    register_resolver(Adapter())
    if phase == 'serialize':
        with pytest.raises(SerializationError) as error:
            serialize({'nested': Target(7)})
    else:
        payload = serialize({'nested': Target(7)})
        with pytest.raises(DeserializationError) as error:
            deserialize(payload)
    assert calls == [phase]
    assert error.value.__cause__ is original
    assert error.value.path == 'nested'


def test_context_is_immutable_and_not_shared_after_callback_failure():
    context = TraversalContext(path='root', serialize_private_attributes=True)
    assert context.child_path('field') == 'root.field'
    assert context.child_path(2) == 'root[2]'
    with pytest.raises(FrozenInstanceError):
        context.path = 'changed'
    assert current_context() == TraversalContext()


def test_context_skips_excluded_child_before_traversal():
    class Adapter(Resolver):
        def serialize(self, obj, *, context):
            return {'value': context.serialize(obj.value, 'value')}
    register_resolver(Adapter())
    payload = serialize({'nested': Target(object())}, exclude={'nested.value'})
    assert set(payload['nested']) == {'_serialized_type'}


def test_unsupported_signature_is_rejected_before_user_code_runs():
    calls = []
    class Adapter(Resolver):
        def serialize(self, obj, private, required_third_argument):
            calls.append(obj)
            return {}
    register_resolver(Adapter())
    with pytest.raises(SerializationError, match='Unsupported resolver signature') as error:
        serialize(Target(7))
    assert calls == []
    assert type(error.value.__cause__) is TypeError


def test_opaque_callables_keep_the_historical_two_argument_call():
    calls = []
    class Encoder:
        __signature__ = 'opaque callable'
        def __call__(self, obj, private):
            calls.append(('encode', private))
            return {'value': obj.value}
    class Decoder:
        __signature__ = 'opaque callable'
        def __call__(self, data, cls):
            calls.append(('decode', dict(data)))
            return cls(**data)
    class Adapter(Resolver):
        serialize = Encoder()
        deserialize = Decoder()
    register_resolver(Adapter())
    payload = serialize(Target(7), serialize_private_attributes=True)
    assert deserialize(payload, expected_type=Target).value == 7
    assert calls == [('encode', True), ('decode', {'value': 7})]
