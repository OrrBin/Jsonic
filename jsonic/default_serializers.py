from datetime import datetime
from uuid import UUID, SafeUUID

from jsonic import jsonic_serializer, jsonic_deserializer

"""This Module contains default serializer and deserializer for some types"""


@jsonic_serializer(serialized_type=datetime)
def serialize_datetime(datetime_obj):
    return {'datetime': datetime_obj.__str__()}


@jsonic_deserializer(deserialized_type_name=datetime)
def deserialize_datetime(serialized_datetime):
    return datetime.fromisoformat(serialized_datetime['datetime'])


@jsonic_serializer(serialized_type=complex)
def serialize_complex(num: complex):
    return {'value': f'complex({num.real},{num.imag})'}


@jsonic_deserializer(deserialized_type_name=complex)
def deserialize_complex(obj: dict):
    num_str = obj['value']
    comma_index = num_str.index(',')
    return complex(real=float(num_str[8:comma_index]), imag=float(num_str[comma_index + 1:-1]))


@jsonic_deserializer(SafeUUID, type_id='uuid.SafeUUID')
def deserialize_uuid_safety(data):
    if isinstance(data, SafeUUID):
        return data
    if not isinstance(data, dict) or data.get('_serialized_type', 'uuid.SafeUUID') not in ('uuid.SafeUUID', 'SafeUUID'):
        raise ValueError('Invalid UUID safety metadata')
    try:
        value = SafeUUID[data['name']]
    except (KeyError, TypeError):
        raise ValueError('Invalid UUID safety metadata') from None
    if 'value' in data and data['value'] != value.value:
        raise ValueError('Inconsistent UUID safety metadata')
    return value


@jsonic_deserializer(UUID, type_id='uuid.UUID')
def deserialize_uuid(data):
    """Read explicit portable strings and the historical slots representation."""
    if set(data) == {'uuid'} and type(data['uuid']) is str:
        return UUID(data['uuid'])
    if 'int' in data and set(data) <= {'int', 'is_safe'}:
        if type(data['int']) is not int:
            raise ValueError('UUID int must be an integer')
        safety = deserialize_uuid_safety(data['is_safe']) if 'is_safe' in data else SafeUUID.unknown
        return UUID(int=data['int'], is_safe=safety)
    raise ValueError('Invalid UUID payload; expected uuid string or legacy int fields')
