from copy import deepcopy
from uuid import UUID, SafeUUID

import pytest

from jsonic import deserialize, serialize


@pytest.mark.parametrize('number', [0, 1, 2**128 - 1])
@pytest.mark.parametrize('safety', list(SafeUUID))
def test_historical_uuid_wire_output_is_preserved_and_readable(number, safety):
    value = UUID(int=number, is_safe=safety)
    wire = {'int': number, 'is_safe': {'name': safety.name, 'value': safety.value,
                                     '_serialized_type': 'uuid.SafeUUID'}, '_serialized_type': 'uuid.UUID'}
    assert serialize(value) == wire
    before = deepcopy(wire)
    restored = deserialize(wire, expected_type=UUID, safe=True)
    assert restored == value
    assert restored.is_safe is safety
    assert wire == before


@pytest.mark.parametrize('wrap,unwrap', [(lambda v: v, lambda v: v),
    (lambda v: {'rows': [(v,)]}, lambda v: v['rows'][0][0])])
def test_opted_in_portable_string_uuid_codec_inherits_through_containers(wrap, unwrap):
    value = UUID(int=7)
    wire = serialize(wrap(value), uuid_format='string')
    assert unwrap(deserialize(wire, safe=True)) == value
    assert serialize(value, uuid_format='string') == {'uuid': str(value), '_serialized_type': 'uuid.UUID'}


@pytest.mark.parametrize('data', [
    {'int': -1}, {'int': 2**128}, {'int': True}, {'int': '7'}, {'uuid': 'invalid'},
    {'uuid': 7}, {'int': 7, 'extra': 1}, {'int': 7, 'is_safe': {'name': 'unknown', 'value': 1}},
])
def test_malformed_uuid_wire_data_is_rejected_without_mutation(data):
    payload = {'_serialized_type': 'uuid.UUID', **data}
    before = deepcopy(payload)
    with pytest.raises(ValueError): deserialize(payload, safe=True)
    assert payload == before


def test_invalid_field_selector_does_not_leak_uuid_format():
    from jsonic.context import current_context, TraversalContext
    with pytest.raises(AttributeError):
        serialize(7, include=[object()], uuid_format='string')
    assert current_context() == TraversalContext()


@pytest.mark.parametrize('name', ['UUID', 'SafeUUID'])
def test_standard_codecs_do_not_reserve_application_short_names(name):
    from jsonic import jsonic_serializer, jsonic_deserializer
    def initialize(self, value): self.value = value
    ApplicationType = type(name, (), {'__module__': __name__, '__init__': initialize})
    jsonic_serializer(ApplicationType)(lambda obj: {'value': obj.value})
    jsonic_deserializer(ApplicationType)(lambda data: ApplicationType(data['value']))
    assert deserialize(serialize(ApplicationType(7)), safe=True).value == 7
    native = UUID(int=7)
    assert type(deserialize(serialize(native), safe=True)) is UUID
