"""Third-party-style resolver contracts, with isolated global registration (#29)."""
import pytest

from jsonic import deserialize, serialize
from jsonic.exceptions import SerializationError
from jsonic.type_resolver import TypeResolver, register_resolver, get_resolver_for_type


class Target:
    def __init__(self, value: int): self.value = value


class ExternalResolver(TypeResolver):
    def __init__(self, name='external', rank=200, accepts=True):
        self.name, self.rank, self.accepts = name, rank, accepts
        self.calls = []
    def can_resolve(self, cls): return self.accepts and cls is Target
    def priority(self): return self.rank
    def serialize(self, obj, private=False):
        self.calls.append(('serialize', private))
        return {'value': obj.value}
    def deserialize(self, data, cls):
        self.calls.append(('deserialize', dict(data)))
        return cls(**data)


@pytest.mark.parametrize('ranks,winner', [((200, 300), 'second'), ((300, 200), 'first'), ((200, 200), 'first')])
def test_priority_and_stable_tie_order(ranks, winner):
    first, second = ExternalResolver('first', ranks[0]), ExternalResolver('second', ranks[1])
    register_resolver(first)
    register_resolver(second)
    assert get_resolver_for_type(Target).name == winner
    payload = serialize(Target(4), serialize_private_attributes=True)
    restored = deserialize(payload, expected_type=Target, safe=True)
    assert restored.value == 4
    chosen, other = (first, second) if winner == 'first' else (second, first)
    assert chosen.calls == [('serialize', True), ('deserialize', {'value': 4})]
    assert other.calls == []


def test_nonmatching_resolver_falls_back_to_builtin():
    resolver = ExternalResolver(accepts=False)
    register_resolver(resolver)
    assert deserialize(serialize(Target(4)), expected_type=Target).value == 4
    assert resolver.calls == []


@pytest.mark.parametrize('returned,error', [(None, TypeError), (7, TypeError), (['bad'], ValueError)])
def test_malformed_resolver_return_shape_has_a_clear_failure(returned, error):
    class Bad(ExternalResolver):
        def serialize(self, obj, private=False): return returned
    register_resolver(Bad())
    # Conversion currently exposes dict()'s errors; normalization belongs to #16.
    with pytest.raises(error):
        serialize(Target(4))


def test_resolver_exception_preserves_path_and_source_state():
    class Bad(ExternalResolver):
        def serialize(self, obj, private=False): raise RuntimeError('resolver sentinel')
    register_resolver(Bad())
    source = Target(4)
    with pytest.raises(SerializationError, match='resolver sentinel') as error:
        serialize({'nested': source})
    assert error.value.path == 'nested'
    assert vars(source) == {'value': 4}


def test_minimal_public_protocol_resolver():
    class PublicResolver(ExternalResolver):
        def serialize(self, obj): return {'value': obj.value}
    register_resolver(PublicResolver())
    assert serialize(Target(4))['value'] == 4
