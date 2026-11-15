from enum import Enum, Flag, IntFlag

import pytest

from jsonic import serialize, deserialize, register_jsonic_type
from jsonic.exceptions import DeserializationError
from jsonic.util import full_type_name


class Permissions(Flag):
    NONE = 0
    READ = 1
    WRITE = 2
    ALSO_READ = 1


class IntPermissions(IntFlag):
    NONE = 0
    READ = 1
    WRITE = 2


class Aliased(Enum):
    FIRST = 1
    SECOND = 1


@pytest.mark.parametrize('typ', [Permissions, IntPermissions])
@pytest.mark.parametrize('value', [0, 1, 2, 3])
@pytest.mark.parametrize('safe', [False, True])
def test_flags_roundtrip_without_format_change(typ, value, safe):
    register_jsonic_type(typ)
    original = typ(value)
    payload = serialize(original)
    assert payload == {'name': original.name, 'value': value, '_serialized_type': full_type_name(typ)}
    assert deserialize(payload, expected_type=typ, safe=safe) is original
    assert deserialize(serialize([original])) == [original]


def test_flag_alias_and_ordinary_enum_alias_behavior():
    assert deserialize(serialize(Permissions.ALSO_READ)) is Permissions.READ
    payload = serialize(Aliased.FIRST)
    payload['name'] = 'SECOND'
    assert deserialize(payload) is Aliased.FIRST


def test_unknown_bits_follow_python_flag_class_policy():
    payload = {'_serialized_type': full_type_name(Permissions), 'name': None, 'value': 8}
    with pytest.raises(DeserializationError) as error:
        deserialize(payload)
    assert isinstance(error.value.__cause__, ValueError)
    payload['_serialized_type'] = full_type_name(IntPermissions)
    assert deserialize(payload) == IntPermissions(8)


@pytest.mark.parametrize('value', ['invalid', {}, None])
def test_malformed_flags_have_consistent_errors(value):
    payload = {'_serialized_type': full_type_name(Permissions), 'name': 'READ', 'value': value}
    with pytest.raises(DeserializationError, match='Invalid enum payload'):
        deserialize(payload)


def test_missing_value_has_consistent_error():
    with pytest.raises(DeserializationError):
        deserialize({'_serialized_type': full_type_name(Permissions), 'name': 'READ'})
