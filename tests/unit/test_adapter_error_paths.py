"""Exact paths across resolver/custom/Pydantic/container boundaries (#15)."""
from dataclasses import dataclass
from typing import Any

import pytest

from jsonic import Serializable, deserialize, serialize, jsonic_deserializer
from jsonic.exceptions import DeserializationError, SerializationError
from jsonic.util import full_type_name


@dataclass
class DataclassChild:
    value: Any


class HintedChild:
    def __init__(self, value: Any): self.value = value


@pytest.mark.parametrize('cls', [DataclassChild, HintedChild])
@pytest.mark.parametrize('wrap,path', [
    (lambda v: {'child': v}, 'child.value'),
    (lambda v: {'rows': [(v,)]}, 'rows[0][0].value'),
    (lambda v: {v}, '[0].value'),
])
def test_resolver_serialization_preserves_parent_path(cls, wrap, path):
    if cls is DataclassChild and path == '[0].value':
        # Use a hashable dataclass shape so this actually reaches the set adapter.
        @dataclass(eq=False)
        class HashableChild:
            value: Any
        cls = HashableChild
    with pytest.raises(SerializationError) as error:
        serialize(wrap(cls(object())))
    assert error.value.path == path


@pytest.mark.parametrize('parent', ['registered', 'dataclass', 'hinted', 'pydantic'])
def test_missing_child_field_preserves_complete_decoder_path(parent):
    class Required(Serializable):
        def __init__(self, required): self.required = required
    if parent == 'registered':
        class Parent(Serializable):
            def __init__(self, child): self.child = child
    elif parent == 'dataclass':
        @dataclass
        class Parent:
            child: Any
    elif parent == 'hinted':
        class Parent:
            def __init__(self, child: Any): self.child = child
    else:
        pydantic = pytest.importorskip('pydantic')
        class Parent(pydantic.BaseModel):
            child: Any
    payload = {'_serialized_type': full_type_name(Parent), 'child':
               [{'_serialized_type': 'tuple', '_is_tuple': True,
                 'items': [{'_serialized_type': full_type_name(Required)}]}]}
    with pytest.raises(DeserializationError, match='Missing attribute.*required') as error:
        deserialize({'rows': [payload]})
    assert error.value.path == 'rows[0].child[0][0]'
    assert error.value.code == 'missing_field'
    assert error.value.field == 'required'


def test_custom_decoder_type_error_preserves_cause_and_boundary_path():
    class Broken:
        pass
    original = TypeError('decoder sentinel')
    @jsonic_deserializer(Broken)
    def decode(data): raise original
    with pytest.raises(DeserializationError) as error:
        deserialize({'rows': [{'_serialized_type': 'Broken'}]}, safe=True)
    assert error.value.path == 'rows[0]'
    assert error.value.__cause__ is original


def test_type_mismatch_metadata_has_types_without_input_values():
    secret = 'sensitive-sentinel'
    with pytest.raises(DeserializationError) as error:
        deserialize(secret, expected_type=int)
    assert error.value.code == 'type_mismatch'
    assert error.value.expected_type is int
    assert error.value.actual_type is str
    assert secret not in str(error.value)


def test_nontext_input_error_does_not_embed_payload_values():
    with pytest.raises(TypeError) as error:
        deserialize({'password': 'sensitive-sentinel'}, string_input=True)
    assert 'sensitive-sentinel' not in str(error.value)
