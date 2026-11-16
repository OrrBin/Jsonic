import os
from pathlib import Path
import subprocess
import sys


def test_repeated_dataclass_cycle_rejection_in_a_fresh_process(tmp_path):
    root = Path(__file__).resolve().parents[2]
    script = '''
from dataclasses import dataclass
import sys
from jsonic import serialize
@dataclass
class Node:
    child:object=None
node=Node(); node.child=node
limit=sys.getrecursionlimit()
for _ in range(100):
    try: serialize(node)
    except ValueError as error: assert 'Circular reference' in str(error)
    else: raise AssertionError('cycle was accepted')
assert node.child is node and sys.getrecursionlimit()==limit
print('ok')
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True,
                            cwd=str(tmp_path), timeout=15,
                            env={**os.environ, 'PYTHONPATH': str(root), 'PYTHONFAULTHANDLER': '1'})
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'ok'
