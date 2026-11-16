"""Explicit field-state persistence keeps presentation output unchanged (#11)."""
from copy import deepcopy
from typing import List, Dict, Tuple, Set, Any
from uuid import UUID
from unittest.mock import patch

import pytest

pydantic = pytest.importorskip('pydantic')
from jsonic import serialize, deserialize, register_jsonic_type, jsonic_deserializer
from jsonic.context import current_context, TraversalContext
from jsonic.exceptions import DeserializationError
from jsonic.pydantic_support import PYDANTIC_FIELDS_PREFIX
from jsonic.util import full_type_name

V2 = hasattr(pydantic.BaseModel, 'model_fields')


class Child(pydantic.BaseModel):
    if V2:
        model_config = pydantic.ConfigDict(frozen=True)
        amount: int = pydantic.Field(validation_alias='inputAmount', serialization_alias='outputAmount')
    else:
        class Config:
            frozen = True
        amount: int = pydantic.Field(alias='inputAmount')
    secret: Any = 'default'


class Parent(pydantic.BaseModel):
    children: List[Child]
    mapping: Dict[str, Child]
    pair: Tuple[Child, Child]
    members: Set[Child]
    identifier: UUID


@pytest.mark.parametrize('text', [False, True])
@pytest.mark.parametrize('shape', ['root', 'list', 'tuple', 'dict'])
def test_nested_typed_models_and_collections_roundtrip(text, shape):
    register_jsonic_type(Child)
    register_jsonic_type(Parent)
    child = Child(inputAmount=7)
    value = Parent(children=[child], mapping={'a': child}, pair=(child, child), members={child}, identifier=UUID(int=7))
    wraps = {'root': (lambda v: v, lambda v: v), 'list': (lambda v: [v], lambda v: v[0]),
             'tuple': (lambda v: (v,), lambda v: v[0]), 'dict': (lambda v: {'model': v}, lambda v: v['model'])}
    wrap, unwrap = wraps[shape]
    payload = serialize(wrap(value), string_output=text, pydantic_mode='roundtrip', uuid_format='string')
    before = deepcopy(payload)
    restored = unwrap(deserialize(payload, string_input=text, safe=True))
    # Pydantic v1's own model equality dumps sets of models to unhashable
    # dictionaries. Compare independent field state rather than that dump.
    def state(model):
        child_state = lambda child: (child.amount, child.secret)
        return (list(map(child_state, model.children)),
                {k: child_state(v) for k, v in model.mapping.items()},
                tuple(map(child_state, model.pair)),
                set(map(child_state, model.members)), model.identifier)
    assert type(restored) is Parent
    assert state(restored) == state(value)
    assert type(restored.children[0]) is Child
    assert type(restored.mapping['a']) is Child
    assert type(restored.pair) is tuple
    assert all(type(child) is Child for child in restored.pair)
    assert type(restored.members) is set
    assert type(next(iter(restored.members))) is Child
    assert payload == before


def test_default_presentation_uses_existing_alias_and_type_id():
    value = Child(inputAmount=7)
    tag = full_type_name(Child)
    expected_key = 'outputAmount' if V2 else 'inputAmount'
    assert serialize(value) == {expected_key: 7, 'secret': 'default', '_serialized_type': tag}
    persisted = serialize(value, pydantic_mode='roundtrip')
    assert persisted == {'amount': 7, 'secret': 'default', '_serialized_type': PYDANTIC_FIELDS_PREFIX + tag}
    assert deserialize(persisted, expected_type=Child, safe=True) == value
    assert current_context() == TraversalContext()


def test_canonical_field_selection_preserves_format_and_skips_excluded_values():
    sentinel = object()
    value = Child(inputAmount=7, secret=sentinel)
    payload = serialize({'child': (value,)}, pydantic_mode='roundtrip', exclude={'child.secret'})
    wire = payload['child']['items'][0]
    assert set(wire) == {'amount', '_serialized_type'}
    assert wire['_serialized_type'].startswith(PYDANTIC_FIELDS_PREFIX)
    register_jsonic_type(Child)
    assert deserialize(payload, safe=True)['child'][0].secret == 'default'
    assert value.secret is sentinel


@pytest.mark.parametrize('kind', ['choices', 'path'])
def test_complex_validation_aliases_are_rejected_explicitly(kind):
    if not V2: pytest.skip('Pydantic v2 alias API')
    alias = pydantic.AliasChoices('wire', 'input') if kind == 'choices' else pydantic.AliasPath('source', 'value')
    class Model(pydantic.BaseModel):
        value: int = pydantic.Field(validation_alias=alias)
    value = Model(wire=7) if kind == 'choices' else Model(source={'value': 7})
    with pytest.raises(ValueError, match='string validation alias'):
        serialize(value, pydantic_mode='roundtrip')
    assert current_context() == TraversalContext()


def test_extra_stored_attributes_are_not_silently_lost():
    if V2:
        class Model(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(extra='allow')
            value: int
    else:
        class Model(pydantic.BaseModel):
            value: int
            class Config:
                extra = 'allow'
    value = Model(value=7, extraValue='keep')
    assert serialize(value)['extraValue'] == 'keep'
    with pytest.raises(ValueError, match='extra stored attributes'):
        serialize(value, pydantic_mode='roundtrip')


def test_same_input_alias_for_distinct_fields_is_rejected():
    class Model(pydantic.BaseModel):
        first: int = pydantic.Field(alias='same')
        second: int = pydantic.Field(alias='same')
    with pytest.raises(ValueError, match='unique validation aliases'):
        serialize(Model(same=7), pydantic_mode='roundtrip')


def test_presentation_alias_resembling_metadata_remains_user_data():
    class Model(pydantic.BaseModel):
        value: str = pydantic.Field(alias='_jsonic_pydantic_mode')
    value = Model(_jsonic_pydantic_mode='fields-v1')
    assert deserialize(serialize(value), expected_type=Model, safe=True) == value
    assert deserialize(serialize(value, pydantic_mode='roundtrip'), expected_type=Model, safe=True) == value


def test_roundtrip_mode_uses_field_state_instead_of_presentation_serializers():
    if not V2: pytest.skip('Pydantic v2 field_serializer API')
    calls = []
    class Model(pydantic.BaseModel):
        value: int
        @pydantic.field_serializer('value')
        def display(self, value):
            calls.append(value)
            return 'formatted'
    value = Model(value=7)
    assert serialize(value)['value'] == 'formatted'
    wire = serialize(value, pydantic_mode='roundtrip')
    assert wire['value'] == 7
    assert calls == [7]
    assert deserialize(wire, expected_type=Model, safe=True).value == 7


def test_unknown_canonical_fields_and_unauthorized_versions_are_rejected():
    payload = serialize(Child(inputAmount=7), pydantic_mode='roundtrip')
    with pytest.raises(ValueError, match='unknown canonical fields'):
        deserialize({**payload, 'unexpected': 1}, expected_type=Child, safe=True)
    future = {**payload, '_serialized_type': payload['_serialized_type'].replace('fields-v1:', 'fields-v2:')}
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize(future, expected_type=Child, safe=True)
        imports.assert_not_called()


def test_format_prefix_cannot_reconstruct_an_authorized_non_pydantic_class():
    calls = []
    class Plain:
        def __init__(self): calls.append('constructed')
    register_jsonic_type(Plain)
    payload = {'_serialized_type': PYDANTIC_FIELDS_PREFIX + full_type_name(Plain)}
    with patch('jsonic.serializable.importlib.import_module') as imports:
        with pytest.raises(DeserializationError, match='not registered'):
            deserialize(payload, safe=True)
        imports.assert_not_called()
    assert calls == []


def test_writer_refuses_collision_with_an_explicit_custom_codec_id():
    class Shadow:
        pass
    tag = PYDANTIC_FIELDS_PREFIX + full_type_name(Child)
    jsonic_deserializer(Shadow, type_id=tag)(lambda data: Shadow())
    with pytest.raises(ValueError, match='conflicts with a custom codec'):
        serialize(Child(inputAmount=7), pydantic_mode='roundtrip')


def test_safe_mode_still_requires_nested_type_registration():
    child = Child(inputAmount=7)
    wire = serialize([child], pydantic_mode='roundtrip')
    with pytest.raises(DeserializationError, match='not registered'):
        deserialize(wire, safe=True)
    register_jsonic_type(Child)
    assert deserialize(wire, safe=True) == [child]


def test_native_constraints_are_validated_when_reading_persisted_fields():
    class Model(pydantic.BaseModel):
        value: int = pydantic.Field(gt=0)
    value = Model(value=7)
    payload = serialize(value, pydantic_mode='roundtrip')
    invalid = {**payload, 'value': -1}
    before = deepcopy(invalid)
    with pytest.raises(pydantic.ValidationError):
        deserialize(invalid, expected_type=Model, safe=True)
    assert invalid == before
    assert value.value == 7


def test_root_model_is_explicitly_unsupported():
    if V2:
        Model = pydantic.RootModel[List[int]]
        value = Model([1, 2])
    else:
        class Model(pydantic.BaseModel):
            __root__: List[int]
        value = Model.parse_obj([1, 2])
    with pytest.raises(ValueError, match='does not support root models'):
        serialize(value, pydantic_mode='roundtrip')


def test_invalid_field_selectors_do_not_leak_format_options():
    with pytest.raises(AttributeError):
        serialize(7, include=[object()], pydantic_mode='roundtrip', uuid_format='string')
    assert current_context() == TraversalContext()


def test_field_state_mode_rejects_a_cyclic_model_before_recursive_dumping():
    class Model(pydantic.BaseModel):
        child: Any = None
    value = Model()
    value.child = value
    with pytest.raises(ValueError, match='Circular reference'):
        serialize(value, pydantic_mode='roundtrip')
    assert value.child is value
