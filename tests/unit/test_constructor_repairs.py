"""Defaults, frozen invariants and explicit unsupported constructor inputs (#12)."""
from copy import deepcopy
from dataclasses import dataclass, field, InitVar

import pytest

from jsonic import Serializable, deserialize, serialize, register_jsonic_type
from jsonic.exceptions import DeserializationError, SerializationError
from jsonic.util import full_type_name


@pytest.mark.parametrize('kind', ['registered', 'hinted', 'generic'])
def test_constructor_defaults_and_required_fields_share_rules(kind):
    base = Serializable if kind == 'registered' else object
    class Record(base):
        def __init__(self, required, value=7):
            self.required, self.value = required, value
    if kind == 'hinted': Record.__init__.__annotations__ = {'required': int}
    payload = {'_serialized_type': full_type_name(Record), 'required': 1}
    assert deserialize(payload, expected_type=Record, safe=True).value == 7
    with pytest.raises(DeserializationError, match='Missing attribute.*required') as error:
        deserialize({'_serialized_type': full_type_name(Record)}, expected_type=Record, safe=True)
    assert error.value.field == 'required'


def test_missing_mapped_default_and_mapped_transient_default_are_used():
    class Record(Serializable):
        init_parameters_mapping = {'identifier': 'id', 'cached': 'cache'}
        transient_attributes = ['cache']
        def __init__(self, identifier=7, cached='default'):
            self.id, self.cache = identifier, cached
    value = deserialize({'_serialized_type': full_type_name(Record)}, safe=True)
    assert (value.id, value.cache) == (7, 'default')


def test_missing_required_mapped_attribute_keeps_keyerror_compatibility():
    class Record(Serializable):
        init_parameters_mapping = {'identifier': 'id'}
        def __init__(self, identifier): self.id = identifier
    payload = {'_serialized_type': full_type_name(Record)}
    before = deepcopy(payload)
    with pytest.raises(KeyError, match='id'):
        deserialize(payload, safe=True)
    assert payload == before


@pytest.mark.parametrize('registered', [False, True])
def test_frozen_noninit_fields_are_validated_and_never_overwritten(registered):
    @dataclass(frozen=True)
    class Record:
        value: int
        doubled: int = field(init=False)
        def __post_init__(self): object.__setattr__(self, 'doubled', self.value * 2)
    if registered: register_jsonic_type(Record)
    payload = serialize(Record(4))
    assert deserialize(payload, expected_type=Record, safe=True) == Record(4)
    payload['doubled'] = 99
    before = deepcopy(payload)
    with pytest.raises(DeserializationError, match='frozen dataclass invariant') as error:
        deserialize(payload, expected_type=Record, safe=True)
    assert error.value.code == 'immutable_field_mismatch'
    assert error.value.path == 'doubled'
    assert payload == before


@pytest.mark.parametrize('registered', [False, True])
def test_required_initvar_is_rejected_before_emitting_unreconstructable_data(registered):
    @dataclass
    class Record:
        seed: InitVar[int]
        value: int = field(init=False)
        def __post_init__(self, seed): self.value = seed * 2
    if registered: register_jsonic_type(Record)
    value = Record(4)
    with pytest.raises(SerializationError, match='Required InitVar.*seed'):
        serialize(value)
    with pytest.raises(DeserializationError, match='Required InitVar.*seed'):
        deserialize({'_serialized_type': full_type_name(Record), 'value': 8}, expected_type=Record, safe=True)
    assert value.value == 8


def test_defaulted_initvar_and_mutable_noninit_legacy_behavior():
    @dataclass
    class Record:
        seed: InitVar[int] = 4
        value: int = field(init=False)
        def __post_init__(self, seed): self.value = seed * 2
    value = Record()
    value.value = 9
    assert deserialize(serialize(value), expected_type=Record, safe=True).value == 9


def test_variadic_custom_constructor_is_not_a_required_initvar_input():
    @dataclass(init=False)
    class Record:
        seed: InitVar[int]
        value: int = field(init=False)
        def __init__(self, *seed): self.value = seed[0] if seed else 7
    value = Record(8)
    assert deserialize(serialize(value), expected_type=Record, safe=True).value == 8
