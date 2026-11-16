"""Wire v2 registration and compatibility are tested in separate processes."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from jsonic import serialize, deserialize

ROOT = Path(__file__).resolve().parents[2]


def test_v2_independent_processes(tmp_path):
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    script = '''
import json,sys
from dataclasses import dataclass
from jsonic import serialize,deserialize,register_jsonic_type
@dataclass
class Record:
    data:dict
register_jsonic_type(Record)
if sys.argv[1]=='write':
    print(serialize(Record({'_serialized_type':'os.system','_is_tuple':True,'items':[1]}),wire_format='v2',string_output=True))
else:
    value=deserialize(sys.stdin.read(),string_input=True,wire_format='v2',safe=True)
    assert type(value) is Record
    print(json.dumps(value.data))
'''
    def run(action, data=None):
        return subprocess.run([sys.executable, '-c', script, action], input=data,
            text=True, capture_output=True, check=True, timeout=15, cwd=str(tmp_path), env=env)
    written = run('write')
    assert json.loads(run('read', written.stdout).stdout) == {
        '_serialized_type': 'os.system', '_is_tuple': True, 'items': [1]}


def test_v2_golden_and_actual_old_reader(tmp_path, pytestconfig):
    fixture = json.loads((ROOT / 'tests/fixtures/wire/v2.json').read_text())
    value = {'_serialized_type': 'literal', '_is_tuple': True, 'items': [1]}
    assert serialize(value, wire_format='v2') == fixture['payload']
    assert deserialize(fixture['payload'], wire_format='v2', safe=True) == value
    legacy = pytestconfig.getoption('--legacy-jsonic-root')
    if legacy is None:
        pytest.skip('requires explicit historical source tree')
    script = 'import json,sys,jsonic; print(jsonic.__file__,flush=True); jsonic.deserialize(json.load(sys.stdin))'
    env = {**os.environ, 'PYTHONPATH': str(Path(legacy).resolve())}
    old = subprocess.run([sys.executable, '-c', script], input=json.dumps(fixture['payload']),
        text=True, capture_output=True, timeout=15, cwd=str(tmp_path), env=env)
    assert str(Path(legacy).resolve() / 'jsonic/__init__.py') in old.stdout
    assert old.returncode != 0 and 'Could not find type: jsonic:wire:v2' in old.stderr
    old_default = subprocess.run([sys.executable, '-c', script], input=json.dumps(serialize([1, 2])),
        text=True, capture_output=True, timeout=15, cwd=str(tmp_path), env=env)
    assert old_default.returncode == 0, old_default.stderr
