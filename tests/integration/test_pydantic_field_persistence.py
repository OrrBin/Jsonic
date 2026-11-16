"""Independent processes initialize their own model registrations for fields-v1."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_pydantic_fields_format_survives_fresh_processes(tmp_path):
    pytest.importorskip('pydantic')
    root = Path(__file__).resolve().parents[2]
    script = tmp_path / 'persist_models.py'
    script.write_text('''
import json,sys
from typing import List
from uuid import UUID
import pydantic
from jsonic import serialize,deserialize,register_jsonic_type
class Child(pydantic.BaseModel):
    if hasattr(pydantic.BaseModel,'model_fields'):
        value:int=pydantic.Field(validation_alias='input',serialization_alias='output')
    else:
        value:int=pydantic.Field(alias='input')
class Parent(pydantic.BaseModel):
    children:List[Child]
    identifier:UUID
register_jsonic_type(Child)
value=Parent(children=[Child(input=7)],identifier=UUID(int=7))
if sys.argv[1]=='write':
    print(serialize(value,string_output=True,pydantic_mode='roundtrip',uuid_format='string'))
else:
    restored=deserialize(sys.stdin.read(),string_input=True,expected_type=Parent,safe=True)
    assert type(restored.children[0]) is Child
    assert restored.children[0].value==7 and restored.identifier==UUID(int=7)
    print(json.dumps({'value':restored.children[0].value,'uuid':str(restored.identifier)}))
''')
    environment = {**os.environ, 'PYTHONPATH': str(root)}
    written = subprocess.run([sys.executable, str(script), 'write'], capture_output=True,
                             text=True, check=True, timeout=15, cwd=str(tmp_path), env=environment)
    read = subprocess.run([sys.executable, str(script), 'read'], input=written.stdout,
                          capture_output=True, text=True, check=True, timeout=15, cwd=str(tmp_path), env=environment)
    assert json.loads(read.stdout) == {'value': 7, 'uuid': '00000000-0000-0000-0000-000000000007'}
