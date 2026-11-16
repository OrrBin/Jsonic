"""Consume a prebuilt wheel; build/CI policy remains owned by #17."""
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

import pytest


def test_safe_persistence_from_installed_wheel_outside_checkout(tmp_path, pytestconfig):
    wheel = pytestconfig.getoption('--wheel-path')
    if wheel is None:
        pytest.skip('requires a prebuilt wheel via --wheel-path; no implicit downloads/builds')
    wheel = Path(wheel).resolve()
    assert wheel.is_file() and wheel.suffix == '.whl'
    environment = tmp_path / 'environment'
    venv.EnvBuilder(with_pip=True).create(str(environment))
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheel)],
                   check=True, text=True, capture_output=True, timeout=60)
    script = tmp_path / 'persist.py'
    script.write_text('''
import json, sys
from pathlib import Path
from jsonic import serialize, deserialize, register_jsonic_type
import jsonic
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
@dataclass(frozen=True)
class Record:
    value: int
    created: datetime
    identifier: UUID
    doubled: int = field(init=False)
    def __post_init__(self): object.__setattr__(self, 'doubled', self.value * 2)
register_jsonic_type(Record)
value = Record(7, datetime(2026, 11, 15), UUID(int=7))
if sys.argv[1] == 'write':
    print(serialize(value, string_output=True, uuid_format='string'))
else:
    restored = deserialize(sys.stdin.read(), string_input=True, safe=True)
    assert restored == value
    print(json.dumps({'library': jsonic.__file__, 'value': restored.value}))
''')
    written = subprocess.run([str(python), '-I', str(script), 'write'], cwd=str(tmp_path),
                             check=True, text=True, capture_output=True, timeout=15)
    read = subprocess.run([str(python), '-I', str(script), 'read'], input=written.stdout, cwd=str(tmp_path),
                          check=True, text=True, capture_output=True, timeout=15)
    result = json.loads(read.stdout)
    assert result['value'] == 7
    assert environment in Path(result['library']).resolve().parents
    assert Path(__file__).resolve().parents[2] not in Path(result['library']).resolve().parents
