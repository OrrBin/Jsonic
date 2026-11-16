"""Inspect distribution boundaries and install wheel/sdist outside the checkout."""
import email
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile

folder = Path(sys.argv[1]).resolve()
wheel, = folder.glob('*.whl')
sdist, = folder.glob('*.tar.gz')
with zipfile.ZipFile(str(wheel)) as archive:
    names = archive.namelist()
    assert all(name.startswith('jsonic/') or '.dist-info/' in name for name in names), names
    metadata = email.message_from_bytes(archive.read(next(n for n in names if n.endswith('/METADATA'))))
    assert metadata['Version'] == '2.0.0.dev0'
    assert metadata['Requires-Python'] == '<3.14,>=3.8'
    assert 'pydantic' in metadata.get_all('Provides-Extra')
with tarfile.open(str(sdist)) as archive:
    names = archive.getnames()
    assert all('/.git/' not in name and '/.venv/' not in name for name in names)
    for required in ('pyproject.toml', 'LICENSE', 'MIGRATION.md', 'tests/fixtures/wire/v2.json'):
        assert any(name.endswith('/' + required) for name in names), required
# A separate environment receives only build prerequisites. Runtime installation
# has --no-deps, and wheel installation has no network access.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    env = root / 'env'
    venv.EnvBuilder(with_pip=True).create(str(env))
    python = env / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', 'setuptools>=68,<76', 'wheel>=0.41,<1'], check=True)
    for package in (wheel, sdist):
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps',
                        '--no-build-isolation', '--force-reinstall', str(package)], check=True, cwd=str(root))
        script = '''
import importlib.util,jsonic
from dataclasses import dataclass
from jsonic import serialize,deserialize
assert importlib.util.find_spec('pydantic') is None
@dataclass
class Person:
    age:int
assert deserialize({'age':7},expected_type=Person,validation='strict',safe=True)==Person(7)
literal={'_serialized_type':'literal','_is_tuple':True,'items':[1]}
assert deserialize(serialize(literal,wire_format='v2'),wire_format='v2',safe=True)==literal
print(jsonic.__file__)
'''
        result = subprocess.run([str(python), '-I', '-c', script], check=True, text=True,
                                capture_output=True, cwd=str(root), timeout=30)
        assert env.resolve() in Path(result.stdout.strip()).resolve().parents
        print(package.name, 'installed and exercised outside checkout')
