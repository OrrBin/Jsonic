"""Exact public error paths; known adapter path loss belongs to #15."""
import pytest
from jsonic import Serializable, deserialize, serialize
from jsonic.exceptions import DeserializationError, SerializationError
from jsonic.util import full_type_name

class Bad:
    def __init__(self):
        self.bad = object()

@pytest.mark.parametrize('wrap,path', [
    (lambda v: {'nested': v}, 'nested.bad'),
    (lambda v: {'level2': {'level3': v}}, 'level2.level3.bad'),
    (lambda v: [1, 2, v, 4], '[2].bad'),
    (lambda v: {'bad': v}, 'bad.bad'),
])
def test_serialization_preserves_exact_path(wrap, path):
    with pytest.raises(SerializationError) as error:
        serialize(wrap(Bad()))
    assert error.value.path == path
    assert str(error.value).endswith('at path: ' + path)

@pytest.mark.parametrize('field', ['inner', 'nested'])
@pytest.mark.xfail(strict=True, raises=AssertionError, reason='F13/#15: registered-parent decoder drops parent path')
def test_registered_parent_missing_field_preserves_exact_path(field):
    calls = []
    class Child(Serializable):
        def __init__(self, required):
            calls.append('child constructed')
            self.required = required
    class Parent(Serializable):
        def __init__(self, **kwargs):
            calls.append('parent constructed')
    payload = {'_serialized_type': full_type_name(Parent),
               field: {'_serialized_type': full_type_name(Child)}}
    with pytest.raises(DeserializationError, match='Missing attribute.*required') as error:
        deserialize(payload, safe=True)
    assert calls == []
    assert error.value.path == field

def test_missing_list_member_field_reaches_constructor_binding():
    calls = []
    class Item(Serializable):
        def __init__(self, required):
            calls.append(required)
            self.required = required
    tag = full_type_name(Item)
    payload = [{'_serialized_type': tag, 'required': 1}, {'_serialized_type': tag}]
    with pytest.raises(DeserializationError, match='Missing attribute.*required') as error:
        deserialize(payload, safe=True)
    assert calls == [1]
    assert error.value.path == '[1]'

def test_tuple_dictionary_keys_are_explicitly_rejected():
    with pytest.raises(TypeError, match='keys must be'):
        serialize({(1, 2): {3, 4}})
