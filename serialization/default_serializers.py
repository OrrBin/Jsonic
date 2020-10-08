from datetime import datetime

from serialization import jsonic_serializer, jsonic_deserializer

"""This Module contains default serializer and deserializer for some types"""


@jsonic_serializer(serialized_type=datetime)
def serialize_datetime(datetime_obj):
    return {'datetime': datetime_obj.__str__()}


@jsonic_deserializer(deserialized_type_name=datetime)
def deserialize_datetime(serialized_datetime):
    return datetime.fromisoformat(serialized_datetime['datetime'])
