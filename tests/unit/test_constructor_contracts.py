"""Named constructor cases; unresolved product defects stay linked to #12."""
from copy import deepcopy
from dataclasses import dataclass, field, FrozenInstanceError
from uuid import UUID

import pytest

from jsonic import Serializable, deserialize, serialize
from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name


def test_dataclass_default_factory_omission_creates_independent_values():
    @dataclass
    class Record:
        items: list = field(default_factory=list)
    payload = {'_serialized_type': full_type_name(Record)}
    first = deserialize(payload, expected_type=Record, safe=True)
    second = deserialize(payload, expected_type=Record, safe=True)
    first.items.append(1)
    assert second.items == []
    assert payload == {'_serialized_type': full_type_name(Record)}


def test_keyword_only_constructor_and_post_init_invariant():
    @dataclass(init=False)
    class Record:
        value: int
        doubled: int = field(init=False)
        def __init__(self, *, value):
            if value < 0:
                raise ValueError('value must be nonnegative')
            self.value, self.doubled = value, value * 2
    payload = serialize(Record(value=4))
    assert deserialize(payload, expected_type=Record, safe=True) == Record(value=4)
    invalid = {**payload, 'value': -1}
    before = deepcopy(invalid)
    with pytest.raises(ValueError, match='nonnegative'):
        deserialize(invalid, expected_type=Record, safe=True)
    assert invalid == before


def test_positional_only_constructors_are_currently_rejected_without_execution():
    calls = []
    class Record:
        def __init__(self, value: int, /):
            calls.append(value)
            self.value = value
    payload = {'_serialized_type': full_type_name(Record), 'value': 4}
    with pytest.raises(TypeError, match='positional.only'):
        deserialize(payload, expected_type=Record, safe=True)
    assert calls == []
    assert payload['value'] == 4


def test_mapped_constructor_and_transient_default():
    class Record(Serializable):
        init_parameters_mapping = {'identifier': 'id'}
        transient_attributes = ['cache']
        def __init__(self, identifier, cache='default cache'):
            self.id, self.cache = identifier, cache
    value = Record(7, cache=object())
    payload = serialize(value)
    assert 'cache' not in payload
    restored = deserialize(payload, safe=True)
    assert restored.id == 7
    assert restored.cache == 'default cache'


def test_frozen_noninit_field_roundtrip_preserves_invariants():
    @dataclass(frozen=True)
    class Record:
        value: int
        doubled: int = field(init=False)
        def __post_init__(self):
            object.__setattr__(self, 'doubled', self.value * 2)
    value = Record(4)
    assert deserialize(serialize(value), expected_type=Record, safe=True) == value


def test_defaulted_serializable_parameter_can_be_omitted():
    class Record(Serializable):
        def __init__(self, value=7): self.value = value
    assert deserialize({'_serialized_type': full_type_name(Record)}, safe=True).value == 7


def test_uuid_advertised_roundtrip():
    value = UUID('12345678-1234-5678-1234-567812345678')
    assert deserialize(serialize(value), expected_type=UUID) == value


def test_required_initvar_has_an_explicit_reconstruction_contract():
    from dataclasses import InitVar
    @dataclass
    class Record:
        seed: InitVar[int]
        value: int = field(init=False)
        def __post_init__(self, seed): self.value = seed * 2
    from jsonic.exceptions import SerializationError
    original = Record(4)
    with pytest.raises(SerializationError, match='Required InitVar.*seed') as error:
        serialize(original)
    assert error.value.code == 'unsupported_initvar'
    assert error.value.field == 'seed'
    assert original.value == 8
