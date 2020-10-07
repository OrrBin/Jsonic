from datetime import datetime

from serialization import serializer, deserializer

"""This Module contains default serializer and deserializer for some types"""


@serializer(serialized_type=datetime)
def serialize_datetime(datetime_obj):
    return {'datetime': datetime_obj.__str__()}


@deserializer(deserialized_type_name=datetime)
def deserialize_datetime(serialized_datetime):
    return datetime.fromisoformat(serialized_datetime['datetime'])
