"""Exercise the real autouse fixture in fresh pytest processes and both orders."""
import os
from pathlib import Path

import pytest


@pytest.mark.parametrize('order', [('mutate', 'clean'), ('clean', 'mutate')])
def test_registries_are_restored_between_tests(pytester, monkeypatch, order):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv('PYTHONPATH', str(root) + os.pathsep + os.environ.get('PYTHONPATH', ''))
    fixture = (root / 'tests/conftest.py').read_text().replace("pytest_plugins = ('pytester',)", '')
    pytester.makeconftest(fixture)
    pytester.makepyfile(test_isolation='''
from jsonic import Serializable
from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer
from jsonic.type_resolver import _registry
MAPS = (Serializable.jsonic_types, _JsonicSerializer.serializers,
        _JsonicSerializer.type_ids, _JsonicSerializer.types,
        _JsonicDeserializer.deserializers, _JsonicDeserializer.types)
def test_mutate():
    for mapping in MAPS:
        mapping['test_sentinel'] = object()
    _registry._resolvers.clear()
def test_clean():
    for mapping in (Serializable.jsonic_types, _JsonicSerializer.serializers,
                    _JsonicSerializer.type_ids, _JsonicSerializer.types,
                    _JsonicDeserializer.deserializers, _JsonicDeserializer.types):
        assert 'test_sentinel' not in mapping
    assert [type(r).__name__ for r in _registry._resolvers] == ['DataclassResolver', 'TypeHintedResolver']
''')
    result = pytester.runpytest_subprocess(*['test_isolation.py::test_' + name for name in order], '-q', timeout=30)
    result.assert_outcomes(passed=2)
