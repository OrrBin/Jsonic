"""Presentation/validation and selector boundaries for supported Pydantic majors."""
from copy import deepcopy
from typing import Any

import pytest

pydantic = pytest.importorskip('pydantic')
from jsonic import deserialize, serialize


class Child(pydantic.BaseModel):
    identifier: int = pydantic.Field(alias='wireId')
    secret: str = pydantic.Field(alias='wireSecret')


class Parent(pydantic.BaseModel):
    items: Any


@pytest.mark.parametrize('value', [None, 42, 'Model', object(), str])
def test_optional_model_detection_rejects_non_models(value):
    from jsonic.pydantic_support import is_pydantic_class, is_pydantic_model
    assert is_pydantic_class(value) is False
    assert is_pydantic_model(value) is False


@pytest.mark.parametrize('shape', ['model', 'list', 'tuple', 'dict'])
@pytest.mark.parametrize('selection', ['include', 'exclude'])
def test_nested_wire_aliases_and_selectors(shape, selection):
    child = Child(wireId=7, wireSecret='hide')
    wrapped = {'model': child, 'list': [child], 'tuple': (child,), 'dict': {'a': child}}[shape]
    source = Parent(items=wrapped)
    prefix = 'items.a.' if shape == 'dict' else 'items.'
    kwargs = {'include': {prefix + 'wireId'}} if selection == 'include' else {'exclude': {prefix + 'wireSecret'}}
    payload = serialize(source, **kwargs)
    value = payload['items']
    if shape == 'list': value = value[0]
    elif shape == 'tuple': value = value['items'][0]
    elif shape == 'dict': value = value['a']
    assert value == {'wireId': 7}
    assert child.secret == 'hide'


@pytest.mark.parametrize('items', [set(), {1, 2}, {}, [], [1, 'x', None], 7])
def test_empty_heterogeneous_and_scalar_selector_fallbacks(items):
    source = Parent(items=items)
    payload = serialize(source, exclude={'items.missing'})
    restored = deserialize(payload, expected_type=Parent, safe=True)
    assert restored.items == items
    assert source.items == items
    assert set(serialize(source, include={'notAField'})) == {'_serialized_type'}


def test_symmetric_alias_roundtrip_and_payload_immutability():
    value = Child(wireId=7, wireSecret='keep')
    payload = serialize(value)
    before = deepcopy(payload)
    assert deserialize(payload, expected_type=Child, safe=True) == value
    assert payload == before


@pytest.mark.parametrize('kind', ['choices', 'path'])
def test_explicitly_reversible_validation_alias_choices(kind):
    if not hasattr(pydantic, 'AliasChoices'):
        pytest.skip('validation_alias choices/paths are a Pydantic v2 API')
    alternative = 'input' if kind == 'choices' else pydantic.AliasPath('source', 'value')
    class Aliased(pydantic.BaseModel):
        value: int = pydantic.Field(validation_alias=pydantic.AliasChoices('wire', alternative), serialization_alias='wire')
    inputs = {'input': 7} if kind == 'choices' else {'source': {'value': 7}}
    original = Aliased(**inputs)
    assert serialize(original)['wire'] == 7
    assert deserialize(serialize(original), expected_type=Aliased, safe=True) == original


@pytest.mark.xfail(strict=True, raises=pydantic.ValidationError, reason='F09/#11: asymmetric validation/serialization aliases do not roundtrip')
def test_asymmetric_aliases_are_not_mistaken_for_a_reversible_codec():
    if not hasattr(pydantic, 'AliasChoices'):
        pytest.skip('asymmetric aliases are a Pydantic v2 API')
    class Aliased(pydantic.BaseModel):
        value: int = pydantic.Field(validation_alias='input', serialization_alias='output')
    original = Aliased(input=7)
    assert deserialize(serialize(original), expected_type=Aliased, safe=True) == original
