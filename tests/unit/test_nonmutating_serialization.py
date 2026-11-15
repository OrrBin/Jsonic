import threading

import pytest

from jsonic import Serializable, serialize, jsonic_serializer
from jsonic.exceptions import SerializationError


@pytest.mark.parametrize('registered', [False, True])
@pytest.mark.parametrize('fails', [False, True])
def test_source_state_unchanged(registered, fails):
    base = Serializable if registered else object
    class Record(base):
        transient_attributes = ['cache']
        def __init__(self):
            self._secret = 'secret'
            self.cache = 5
            self._serialized_type = 'user-owned'
            self.child = object() if fails else {'ok': 1}
    record = Record()
    before = dict(vars(record))
    if fails:
        with pytest.raises(SerializationError):
            serialize(record)
    else:
        result = serialize(record)
        assert result['_serialized_type'] != 'user-owned'
    assert vars(record) == before
    assert all(vars(record)[key] is value for key, value in before.items())


def test_concurrent_reader_never_observes_missing_attributes():
    entered, release = threading.Event(), threading.Event()
    class Slow:
        pass
    @jsonic_serializer(Slow)
    def slow(value):
        entered.set()
        assert release.wait(5)
        return {'ok': True}
    class Record(Serializable):
        transient_attributes = ['cache']
        def __init__(self):
            self._secret = 1
            self.cache = 2
            self.child = Slow()
    record = Record()
    before = dict(vars(record))
    failures = []
    def run():
        try:
            serialize(record)
        except Exception as exc:
            failures.append(exc)
    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert entered.wait(5)
        assert vars(record) == before
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert failures == []
    assert vars(record) == before


def test_custom_serializer_returning_source_mapping_is_not_tagged():
    class Record:
        def __init__(self):
            self.value = 1
    @jsonic_serializer(Record)
    def encode(value):
        return vars(value)
    record = Record()
    assert serialize(record)['_serialized_type'] == 'Record'
    assert vars(record) == {'value': 1}


def test_custom_hook_failure_leaves_parent_fields_present():
    class Bad:
        pass
    @jsonic_serializer(Bad)
    def fail(value):
        raise RuntimeError('sentinel failure')
    class Parent(Serializable):
        def __init__(self):
            self._secret = 1
            self.child = Bad()
    parent = Parent()
    before = dict(vars(parent))
    with pytest.raises(SerializationError, match='sentinel failure'):
        serialize(parent)
    assert vars(parent) == before
