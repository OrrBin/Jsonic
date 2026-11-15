"""Small importable models: local stack lookup must not make tests pass."""
from dataclasses import dataclass
from typing import Any

from jsonic import Serializable, jsonic_serializer, jsonic_deserializer, serialize
from jsonic.type_resolver import TypeResolver, register_resolver


class GenericRecord:
    def __init__(self, value, _private='initial'):
        self.value = value
        self._private = _private


class HintedRecord:
    def __init__(self, value: Any, _private='initial'):
        self.value = value
        self._private = _private


@dataclass(eq=False)
class DataclassRecord:
    value: Any
    _private: str = 'initial'


class SlottedRecord:
    __slots__ = ('value', '_private')
    def __init__(self, value, _private='initial'):
        self.value = value
        self._private = _private


class RegisteredRecord(Serializable):
    transient_attributes = ['cache']
    def __init__(self, value, _private='initial'):
        self.value = value
        self._private = _private
        self.cache = object()


class CustomRecord(GenericRecord):
    pass


class ResolverRecord(GenericRecord):
    pass


def install_custom_codec():
    @jsonic_serializer(CustomRecord, type_id='testing:custom:v1')
    def encode(value):
        return {'value': serialize(value.value)}
    @jsonic_deserializer(CustomRecord, type_id='testing:custom:v1', aliases=('OldCustomRecord',))
    def decode(data):
        from jsonic import deserialize
        return CustomRecord(deserialize(data['value']))


class RecordResolver(TypeResolver):
    def can_resolve(self, cls):
        return cls is ResolverRecord
    def serialize(self, obj, private=False):
        result = {'value': serialize(obj.value)}
        if private:
            result['_private'] = obj._private
        return result
    def deserialize(self, data, cls):
        return cls(**data)
    def priority(self):
        return 200


def install_resolver():
    register_resolver(RecordResolver())


ADAPTERS = {
    'generic': GenericRecord, 'hinted': HintedRecord, 'dataclass': DataclassRecord,
    'slots': SlottedRecord, 'registered': RegisteredRecord,
    'codec': CustomRecord, 'resolver': ResolverRecord,
}


def prepare_adapter(name):
    if name == 'codec':
        install_custom_codec()
    elif name == 'resolver':
        install_resolver()
    return ADAPTERS[name]
