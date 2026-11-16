"""Execute maintained self-contained snippets and example scripts in fresh processes."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
has_pydantic = importlib.util.find_spec('pydantic') is not None
count = 0
for document in ('README.md', 'WIRE_FORMAT.md', 'VALIDATION_MODES.md', 'PERSISTENCE.md', 'RESOLVERS.md'):
    for index, code in enumerate(re.findall(r'```python\n(.*?)```', (root / document).read_text(), re.S), 1):
        if 'from pydantic' in code and not has_pydantic:
            print('Optional Pydantic snippet omitted:', document, index)
            continue
        result = subprocess.run([sys.executable, '-c', code], cwd=str(root),
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(f'{document} block {index}:\n{result.stdout}\n{result.stderr}')
        count += 1
for example in sorted((root / 'examples').glob('*.py')):
    if example.name.startswith('pydantic') and not has_pydantic:
        continue
    result = subprocess.run([sys.executable, str(example)], cwd=str(root),
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f'{example.name}:\n{result.stdout}\n{result.stderr}')
    if 'ERROR: Should have raised' in result.stdout:
        raise AssertionError(example.name + ': expected rejection did not happen')
    count += 1
print('Executed documentation snippets/scripts:', count)
