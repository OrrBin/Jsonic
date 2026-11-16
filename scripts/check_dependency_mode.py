"""Fail rather than silently running the wrong optional-dependency job."""
import importlib.util
import sys

mode = sys.argv[1]
if mode == 'absent':
    assert importlib.util.find_spec('pydantic') is None
else:
    import pydantic
    assert pydantic.__version__.split('.')[0] == {'v1': '1', 'v2': '2'}[mode]
print('Dependency mode:', mode)
