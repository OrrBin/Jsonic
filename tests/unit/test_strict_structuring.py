from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Union, Literal, ClassVar

import pytest

from jsonic import deserialize, serialize, Serializable
from jsonic.exceptions import DeserializationError


@dataclass
class Child:
    age: int


@dataclass
class Parent:
    children: List[Child]
    label: Optional[str] = None
    mapping: Dict[str, Tuple[int, str]] = field(default_factory=dict)


def strict(value, typ, **options):
    return deserialize(value, expected_type=typ, validation='strict', **options)


@pytest.mark.parametrize('value,typ', [('1', int), (True, int), (1, float), (None, int), (1, str), (0, bool)])
def test_no_primitive_coercion(value, typ):
    with pytest.raises(DeserializationError) as error:
        strict(value, typ)
    assert error.value.code == 'type_mismatch'
    assert error.value.expected_type is typ and error.value.actual_type is type(value)


@pytest.mark.parametrize('value,typ', [(1, int), (True, bool), (1.5, float), ('a', str), (None, type(None))])
def test_exact_primitives(value, typ):
    assert strict(value, typ) == value


def test_nested_plain_json_defaults_forward_annotations():
    value = strict({'children': [{'age': 7}], 'mapping': {'x': [1, 'a']}}, Parent, safe=True)
    assert value == Parent([Child(7)], mapping={'x': (1, 'a')})
    assert type(value.children[0]) is Child and type(value.mapping['x']) is tuple
    assert strict({'children': []}, Parent).mapping is not strict({'children': []}, Parent).mapping


@pytest.mark.parametrize('value,code,path', [
    ({'children': [{'age': 'private-value'}]}, 'type_mismatch', 'children[0].age'),
    ({'children': [{}]}, 'missing_field', 'children[0].age'),
    ({'children': [], 'unexpected': 1}, 'unknown_field', 'unexpected'),
    ({'children': [], 'mapping': {'x': [1]}}, 'type_mismatch', 'mapping.x'),
])
def test_precise_paths_without_payload_values(value, code, path):
    with pytest.raises(DeserializationError) as error:
        strict(value, Parent)
    assert error.value.path == path and error.value.code == code
    assert 'private-value' not in str(error.value)


def test_unknown_ignore_never_dispatches_tags():
    assert strict({'children': [], 'unknown': {'_serialized_type': 'os.system'}}, Parent,
                  unknown_fields='ignore', safe=True) == Parent([])


def test_union_optional_literal_and_sets():
    assert strict([1, 2, 1], Set[int]) == {1, 2}
    assert strict([1, 'a'], Tuple[int, str]) == (1, 'a')
    assert strict([1, 2], Tuple[int, ...]) == (1, 2)
    assert strict(None, Optional[Child]) is None
    assert strict({'age': 4}, Union[str, Child]) == Child(4)
    assert strict(True, Literal[True]) is True
    with pytest.raises(DeserializationError):
        strict(1, Literal[True])


def test_validation_finishes_before_any_constructor():
    calls = []
    class Record:
        def __init__(self, age: int):
            calls.append(age)
            self.age = age
    with pytest.raises(DeserializationError):
        strict([{'age': 1}, {'age': 'bad'}], List[Record], safe=True)
    assert calls == []
    result = strict([{'age': 1}, {'age': 2}], List[Record], safe=True)
    assert [item.age for item in result] == [1, 2]
    assert calls == [1, 2]


def test_nested_constructor_invoked_once():
    calls = []
    class Record:
        def __init__(self, age: int):
            calls.append(age)
            self.age = age
    class Outer:
        def __init__(self, child):
            self.child = child
    Outer.__init__.__annotations__ = {'child': Record}
    assert strict({'child': {'age': 7}}, Outer).child.age == 7
    assert calls == [7]


def test_mapping_and_additional_typed_attributes():
    class Record(Serializable):
        init_parameters_mapping = {'identifier': 'id'}
        label: str
        def __init__(self, identifier: int):
            self.id = identifier
    result = strict({'id': 7, 'label': 'a'}, Record)
    assert result.id == 7 and result.label == 'a'


def test_frozen_invariants_and_matching_legacy_tags():
    @dataclass(frozen=True)
    class Frozen:
        age: int
        doubled: int = field(init=False)
        def __post_init__(self):
            object.__setattr__(self, 'doubled', 2*self.age)
    source = Frozen(3)
    assert strict(serialize(source), Frozen) == source
    bad = serialize(source)
    bad['doubled'] = 5
    with pytest.raises(DeserializationError) as error:
        strict(bad, Frozen)
    assert error.value.code == 'immutable_field_mismatch'


@pytest.mark.parametrize('fmt', ['legacy', 'v2'])
def test_tagged_objects_text_and_containers(fmt):
    source = Parent([Child(2)], mapping={'x': (1, 'a')})
    wire = serialize(source, wire_format=fmt, string_output=True)
    assert strict(wire, Parent, string_input=True, wire_format=fmt, safe=True) == source


def test_wrong_tag_rejected_without_import(monkeypatch):
    import jsonic.serializable as implementation
    def fail(*args):
        pytest.fail('input-directed import')
    monkeypatch.setattr(implementation.importlib, 'import_module', fail)
    with pytest.raises(DeserializationError) as error:
        strict({'_serialized_type': 'os.system', 'age': 1}, Child, safe=True)
    assert error.value.code == 'tag_mismatch'


def test_dict_any_treats_metadata_as_literal_data():
    data = {'_serialized_type': 'os.system', 'items': [1], '_is_tuple': True}
    assert strict(data, Dict[str, Any], safe=True) == data
    assert strict(serialize(data, wire_format='v2'), Dict[str, Any], wire_format='v2', safe=True) == data


@pytest.mark.parametrize('typ,value', [(List, []), (Dict[int, int], {}), (ClassVar[int], 1)])
def test_unsupported_annotations_are_explicit(typ, value):
    with pytest.raises(DeserializationError) as error:
        strict(value, typ)
    assert error.value.code == 'unsupported_annotation'


def test_unresolved_forward_reference():
    class Record:
        def __init__(self, child: 'MissingSchema'):
            pass
    with pytest.raises(DeserializationError) as error:
        strict({'child': {}}, Record)
    assert error.value.code == 'unsupported_annotation'


def test_legacy_behavior_is_preserved():
    assert deserialize(serialize(Child('bad')), expected_type=Child).age == 'bad'
    with pytest.raises(DeserializationError):
        deserialize({'age': 1}, expected_type=Child)


def test_safe_policy_reaches_constructors_and_cleans_up():
    calls = []
    class Record:
        def __init__(self, age: int):
            with pytest.raises(DeserializationError):
                deserialize({'_serialized_type': 'unregistered.Unknown'}, safe=False)
            calls.append(age)
    strict({'age': 1}, Record, safe=True)
    assert calls == [1]
    from jsonic.serializable import _safe_types
    assert _safe_types.get() is None

@dataclass
class Node:
    value: int
    child: Optional['Node'] = None


def test_resolved_recursive_forward_reference():
    assert strict({'value': 1, 'child': {'value': 2}}, Node) == Node(1, Node(2))


@pytest.mark.parametrize('options', [
    {'validation': 'coerce', 'expected_type': Child},
    {'validation': 'strict'},
    {'validation': 'strict', 'expected_type': Child, 'unknown_fields': 'allow'},
    {'unknown_fields': 'ignore'},
])
def test_invalid_options_fail_clearly(options):
    with pytest.raises(ValueError):
        deserialize({'age': 1}, **options)


@pytest.mark.parametrize('value,typ,code', [
    ({}, List[int], 'type_mismatch'), ([], Dict[str, int], 'type_mismatch'),
    ({1: 2}, Dict[str, int], 'type_mismatch'), (object(), Any, 'type_mismatch'),
    ([], Union[int, str], 'type_mismatch'), ([{}], Set[Dict[str, Any]], 'unhashable_element'),
    ({1, 2}, Tuple[int, int], 'type_mismatch'),
])
def test_invalid_structured_shapes(value, typ, code):
    with pytest.raises(DeserializationError) as error:
        strict(value, typ)
    assert error.value.code == code


def test_positional_only_constructor_rejected():
    class Positional:
        def __init__(self, age: int, /):
            self.age = age
    with pytest.raises(DeserializationError) as error:
        strict({'age': 1}, Positional)
    assert error.value.code == 'unsupported_annotation'


def test_transient_defaults_and_variadic_signature():
    class Record(Serializable):
        transient_attributes = ['cache']
        def __init__(self, age: int, *args, cache: int = 7, **kwargs):
            self.age, self.cache = age, cache
    result = strict({'age': 1, 'cache': 9}, Record)
    assert (result.age, result.cache) == (1, 7)


def test_required_transient_is_explicitly_rejected():
    class Record(Serializable):
        transient_attributes = ['age']
        def __init__(self, age: int):
            self.age = age
    with pytest.raises(DeserializationError) as error:
        strict({'age': 1}, Record)
    assert error.value.code == 'missing_field'


def test_pydantic_schema_rejected_in_strict_mode():
    pydantic = pytest.importorskip('pydantic')
    class Model(pydantic.BaseModel):
        age: int
    with pytest.raises(DeserializationError) as error:
        strict({'age': 1}, Model)
    assert error.value.code == 'unsupported_annotation'


def test_unannotated_class_rejected():
    class Empty:
        pass
    with pytest.raises(DeserializationError) as error:
        strict({}, Empty)
    assert error.value.code == 'unsupported_annotation'


def test_active_safe_policy_cannot_be_broadened_by_schema():
    from jsonic.serializable import _safe_types
    token = _safe_types.set({})
    try:
        with pytest.raises(DeserializationError) as error:
            strict({'age': 1}, Child, safe=False)
        assert error.value.code == 'unsafe_type'
    finally:
        _safe_types.reset(token)


def test_constructor_failure_restores_policy():
    class Broken:
        def __init__(self, age: int):
            raise RuntimeError('constructor failure')
    with pytest.raises(RuntimeError, match='constructor failure'):
        strict({'age': 1}, Broken, safe=True)
    from jsonic.serializable import _safe_types
    assert _safe_types.get() is None


def test_cyclic_python_input_rejected_before_schema_recursion():
    value = {'value': 1}
    value['child'] = value
    with pytest.raises(DeserializationError) as error:
        strict(value, Node)
    assert error.value.code == 'circular_reference'
