from datetime import datetime

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
