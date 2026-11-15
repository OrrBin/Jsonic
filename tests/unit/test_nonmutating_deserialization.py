from copy import deepcopy
from datetime import datetime
import threading

import pytest

from jsonic import deserialize, serialize, jsonic_deserializer


@pytest.mark.parametrize('valid', [False, True])
def test_datetime_payload_unchanged_after_success_and_failure(valid):
    data = serialize(datetime(2026, 1, 1)) if valid else {
        '_serialized_type': 'datetime', 'datetime': 'not-a-date'}
    payload = {'nested': [data]}
    before = deepcopy(payload)
    if valid:
        assert deserialize(payload)['nested'] == [datetime(2026, 1, 1)]
    else:
        with pytest.raises(ValueError):
            deserialize(payload)
    assert payload == before


@pytest.mark.parametrize('fails', [False, True])
def test_custom_decoder_cannot_mutate_outer_payload(fails):
    class Record:
        pass
    @jsonic_deserializer(Record)
    def decode(data):
        assert '_serialized_type' not in data
        data.pop('value')
        data['new'] = 2
        if fails:
            raise ValueError('sentinel')
        return Record()
    payload = {'_serialized_type': 'Record', 'value': 1}
    if fails:
        with pytest.raises(ValueError):
            deserialize(payload)
    else:
        assert isinstance(deserialize(payload), Record)
    assert payload == {'_serialized_type': 'Record', 'value': 1}


def test_concurrent_reader_always_sees_metadata():
    entered, release = threading.Event(), threading.Event()
    class Record:
        pass
    @jsonic_deserializer(Record)
    def decode(data):
        entered.set()
        assert release.wait(5)
        return Record()
    payload = {'_serialized_type': 'Record'}
    errors = []
    def run():
        try:
            deserialize(payload)
        except Exception as exc:
            errors.append(exc)
    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert entered.wait(5)
        assert payload == {'_serialized_type': 'Record'}
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert errors == []


def test_custom_hook_nested_identity_is_preserved():
    class Record:
        pass
    nested = {'value': 1}
    @jsonic_deserializer(Record)
    def decode(data):
        assert data['nested'] is nested
        return Record()
    deserialize({'_serialized_type': 'Record', 'nested': nested})
