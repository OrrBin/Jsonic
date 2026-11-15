import pytest

from jsonic import Serializable, serialize, deserialize, register_jsonic_type
from jsonic.serializable import _get_all_slots


class SlotBase:
    __slots__ = ('base', '__secret')
    def set_base(self):
        self.base = 17
        self.__secret = 'hidden'


class Mixed(SlotBase):
    __slots__ = ('slot', '__dict__', '__weakref__')
    def __init__(self, slot=1):
        self.set_base()
        self.slot = slot
        self.dynamic = 2


class HintedMixed(Mixed):
    __slots__ = 'extra'
    def __init__(self, slot: int = 1):
        super().__init__(slot)
        self.extra = 5


class RegisteredMixed(Serializable):
    __slots__ = ('slot',)
    transient_attributes = ['cache']
    def __init__(self, slot=1):
        self.slot = slot
        self.dynamic = 2
        self.cache = 3


@pytest.mark.parametrize('typ', [Mixed, HintedMixed, RegisteredMixed])
@pytest.mark.parametrize('explicit_registration', [False, True])
def test_mixed_layout_roundtrip(typ, explicit_registration):
    if explicit_registration:
        register_jsonic_type(typ, transient_attributes=getattr(typ, 'transient_attributes', None))
    original = typ(99)
    original.dynamic = 37
    payload = serialize(original)
    assert payload['slot'] == 99
    assert payload['dynamic'] == 37
    assert 'cache' not in payload
    assert '__dict__' not in payload and '__weakref__' not in payload
    restored = deserialize(payload)
    assert restored.slot == 99
    assert restored.dynamic == 37
    if isinstance(original, SlotBase):
        assert restored.base == 17
    if typ is HintedMixed:
        assert restored.extra == 5


def test_private_inherited_slots_and_filters():
    original = HintedMixed(99)
    original._SlotBase__secret = 'changed'
    assert '_SlotBase__secret' not in serialize(original)
    data = serialize(original, serialize_private_attributes=True)
    assert data['_SlotBase__secret'] == 'changed'
    restored = deserialize(data, deserialize_private_attributes=True)
    assert restored._SlotBase__secret == 'changed'
    assert 'slot' not in serialize(original, exclude={'slot'})


def test_uninitialized_slots_are_skipped_and_storage_names_deduplicated():
    class Base:
        __slots__ = ('x',)
    class Child(Base):
        __slots__ = ('x', 'unset')
    original = Child()
    original.x = 4
    assert _get_all_slots(Child) == ['x', 'unset']
    payload = serialize(original)
    assert payload['x'] == 4
    assert 'unset' not in payload


def test_transient_slot_uses_same_policy_as_dynamic_fields():
    class Record(Serializable):
        __slots__ = ('slot',)
        transient_attributes = ['slot', 'dynamic']
        def __init__(self):
            self.slot = object()
            self.dynamic = object()
            self.ok = 1
    result = serialize(Record())
    assert result['ok'] == 1
    assert 'slot' not in result and 'dynamic' not in result


def test_all_underscore_class_name_does_not_mangle_slots():
    class ___:
        __slots__ = ('__value',)
        def __init__(self):
            self.__value = 4
    assert serialize(___(), serialize_private_attributes=True)['__value'] == 4
