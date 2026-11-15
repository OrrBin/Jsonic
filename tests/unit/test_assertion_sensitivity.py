"""A small mutation pilot proves exact path assertions catch path loss."""
import os
from pathlib import Path


def test_exact_path_assertions_kill_path_loss_mutation(pytester, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv('PYTHONPATH', str(root) + os.pathsep + os.environ.get('PYTHONPATH', ''))
    pytester.makepyfile(test_paths=(root / 'tests/unit/test_error_context.py').read_text())
    pytester.makeconftest('''
import jsonic.serializable as implementation
from jsonic.exceptions import SerializationError
original = implementation._serialize_fields
def lose_path(*args, **kwargs):
    try:
        return original(*args, **kwargs)
    except SerializationError as error:
        error.path = ''
        raise
def pytest_configure(config):
    implementation._serialize_fields = lose_path
''')
    result = pytester.runpytest_subprocess('-q', '-k', 'serialization_preserves_exact_path', timeout=30)
    result.assert_outcomes(failed=4, deselected=4)
