import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / 'tests/fixtures/wire/v1.json').read_text())['cases']


def worker(tmp_path, action, name, payload=None, safe=False, register=True, library_root=ROOT):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(library_root) + os.pathsep + str(ROOT)
    command = [sys.executable, '-m', 'tests.support.persistence_worker', action, name]
    if register: command.append('--register')
    if safe: command.append('--safe')
    process = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                             text=True, capture_output=True, cwd=str(tmp_path), env=env, timeout=15)
    assert process.stdout, process.stderr
    return process.returncode, json.loads(process.stdout)


@pytest.mark.parametrize('name', sorted(GOLDEN))
@pytest.mark.parametrize('safe', [False, True])
def test_fresh_writer_and_reader_with_golden_payloads(tmp_path, name, safe):
    code, written = worker(tmp_path, 'write', name)
    assert code == 0, written
    assert written['payload'] == GOLDEN[name]
    code, read = worker(tmp_path, 'read', name, payload=GOLDEN[name], safe=safe)
    assert code == 0, read
    assert Path(read['library']).resolve() == ROOT / 'jsonic/__init__.py'
    if name in ('stable', 'alias', 'moved'):
        assert read['value'] == {'type': 'RenamedValue', 'value': 7}
    elif name == 'record':
        assert read['value'] == {'type': 'Record', 'value': 7}
    elif name == 'flags':
        assert read['value']['value'] == 1
        assert read['value']['type'] == 'Permission'
    else:
        # A separately initialized reader can also describe its own source value.
        from tests.support.persistence_worker import describe, value_for
        assert read['value'] == describe(value_for(name))


@pytest.mark.parametrize('safe', [False, True])
@pytest.mark.parametrize('variant', ['combined_flags_python38', 'combined_flags_python312'])
def test_combined_flag_wire_variants_from_different_python_versions(tmp_path, safe, variant):
    variants = json.loads((ROOT / 'tests/fixtures/wire/v1.json').read_text())['historical_variants']
    code, read = worker(tmp_path, 'read', 'combined_flags', payload=variants[variant], safe=safe)
    assert code == 0, read
    assert read['value']['value'] == 3
    assert read['value']['type'] == 'Permission'


def test_reader_does_not_inherit_writer_registration(tmp_path):
    assert worker(tmp_path, 'write', 'record')[0] == 0
    code, result = worker(tmp_path, 'read', 'record', payload=GOLDEN['record'], safe=True, register=False)
    assert code == 2
    assert result['error'] == 'DeserializationError'
    assert 'not registered' in result['message']
    code, result = worker(tmp_path, 'read', 'record', payload=GOLDEN['record'], register=False)
    assert code == 0  # Explicitly trusted legacy import resolution, separate from safe mode.
    assert result['value']['value'] == 7


@pytest.mark.parametrize('tag', ['never.registered', 'os.system'])
def test_malformed_fixtures_cannot_select_unregistered_types(tmp_path, tag):
    code, result = worker(tmp_path, 'read', 'record', payload={'_serialized_type': tag}, safe=True)
    assert code == 2
    assert result['error'] == 'DeserializationError'
    assert 'not registered' in result['message']


def test_actual_historical_reader_writer_compatibility(tmp_path, pytestconfig):
    legacy = pytestconfig.getoption('--legacy-jsonic-root')
    if legacy is None:
        pytest.skip('requires an explicit historical source tree via --legacy-jsonic-root')
    legacy = Path(legacy).resolve()
    assert (legacy / 'jsonic/__init__.py').is_file()
    # The legacy public API has no safe keyword and no stable-ID decoder registration.
    script = "import json,sys,jsonic; from jsonic import deserialize; print(jsonic.__file__,flush=True); deserialize(json.load(sys.stdin))"
    env = {**os.environ, 'PYTHONPATH': str(legacy)}
    process = subprocess.run([sys.executable, '-c', script], input=json.dumps(GOLDEN['stable']),
                             text=True, capture_output=True, cwd=str(tmp_path), env=env, timeout=15)
    assert process.returncode != 0
    assert str(legacy / 'jsonic/__init__.py') in process.stdout
    assert 'Could not find type: testing:persist:v1' in process.stderr
    for name in ('primitives', 'tuple', 'set', 'datetime', 'complex', 'record', 'color', 'flags', 'combined_flags'):
        code, written = worker(tmp_path, 'write', name, library_root=legacy)
        assert code == 0, (name, written)
        assert Path(written['library']).resolve() == legacy / 'jsonic/__init__.py'
        code, read = worker(tmp_path, 'read', name, payload=written['payload'], safe=True)
        assert code == 0, (name, read)
        from tests.support.persistence_worker import describe, value_for
        assert read['value'] == describe(value_for(name)), name
