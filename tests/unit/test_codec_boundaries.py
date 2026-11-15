"""Wire boundaries of the existing datetime/complex codecs (#26)."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math

import pytest

from jsonic import deserialize, serialize


@pytest.mark.parametrize('value', [
    datetime.min, datetime.max, datetime(2026, 11, 15, 23, 59, 59, 123456),
    datetime(2026, 11, 15, tzinfo=timezone.utc),
    datetime(2026, 11, 15, tzinfo=timezone(timedelta(hours=5, minutes=45))),
    datetime(2026, 11, 15, tzinfo=timezone(-timedelta(hours=3, minutes=30))),
    complex(0, 0), complex(-0.0, -0.0), complex(-3, 4), complex(1e90, -1e-90),
])
@pytest.mark.parametrize('text', [False, True])
def test_standard_codec_boundaries(value, text):
    payload = serialize(value, string_output=text)
    before = deepcopy(payload)
    restored = deserialize(payload, string_input=text, expected_type=type(value), safe=True)
    assert type(restored) is type(value)
    assert restored == value
    assert payload == before
    if isinstance(value, complex):
        assert math.copysign(1, restored.real) == math.copysign(1, value.real)
        assert math.copysign(1, restored.imag) == math.copysign(1, value.imag)
    else:
        assert restored.utcoffset() == value.utcoffset()


@pytest.mark.parametrize('payload,error', [
    ({'_serialized_type': 'datetime', 'datetime': '2026-13-01'}, ValueError),
    ({'_serialized_type': 'datetime', 'datetime': 'not-a-date'}, ValueError),
    ({'_serialized_type': 'datetime', 'datetime': None}, TypeError),
    ({'_serialized_type': 'datetime'}, KeyError),
    ({'_serialized_type': 'complex', 'value': 'invalid'}, ValueError),
    ({'_serialized_type': 'complex', 'value': 'complex(x,2)'}, ValueError),
    ({'_serialized_type': 'complex', 'value': 'complex(1,x)'}, ValueError),
    ({'_serialized_type': 'complex'}, KeyError),
])
def test_malformed_codec_payload_preserves_input(payload, error):
    before = deepcopy(payload)
    with pytest.raises(error):
        deserialize(payload, safe=True)
    assert payload == before


@pytest.mark.parametrize('value', [float('inf'), float('-inf'), float('nan')])
def test_nonfinite_numbers_follow_current_python_json_extension(value):
    # This records the existing permissive JSON extension, not portable JSON.
    restored = deserialize(serialize(value, string_output=True), string_input=True)
    assert type(restored) is float
    if math.isnan(value):
        assert math.isnan(restored)
    else:
        assert restored == value
