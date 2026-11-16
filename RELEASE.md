# Build, support and release policy

## Development version and support

This checkout is `2.0.0.dev0`, an unpublished development version. The official
[PyPI metadata](https://pypi.org/pypi/py-jsonic/json) checked on 16 November 2026
reports latest `1.0.1` with `Requires-Python: >=3.6`. We do not reuse that release
number or claim the new API is already published. A major development line
accounts for stricter behavior and the explicitly narrowed interpreter range.

The declared range is Python **3.8 through 3.13**, matching the CI matrix.
Python 3.6/3.7 and newer unqualified interpreters are excluded explicitly.
Keeping 3.8 is a project compatibility choice, not a claim of upstream Python
security support. Pydantic is optional: absent, v1 >=1.10.13,<2 and v2 >=2,<3
are separate Linux jobs on every declared Python version. Windows has 3.8
without Pydantic and 3.13/v2; macOS 15 Intel has 3.13/v1 and v2. This does not claim every
OS/dependency Cartesian combination is tested. Older interpreters receive
compatible dependency versions through their own Requires-Python constraints.
Setuptools build requirements are bounded to versions supporting Python 3.8.

`pyproject.toml` is the sole metadata/developer dependency source. Install
`requirements-dev.txt` in a fresh environment. `requirements.txt` contains no
runtime dependencies. The `pydantic` extra is additive. Package discovery includes
only `jsonic` and its subpackages; tests/docs/scripts may ship in source archives
but are excluded from wheels.

## Reproduce CI

```sh
python -m pip install -r requirements-dev.txt
# Select pydantic v1/v2 explicitly, or leave absent for the absence job.
python -m build
python -m twine check dist/*
python scripts/check_packages.py dist
python scripts/run_ci_tests.py
python scripts/check_docs.py
```

Start with an empty `dist/`; scripts deliberately require one wheel and sdist.
The package checker inspects both archives, installs each outside the checkout
with no runtime dependencies, and exercises strict input and literal-dictionary
persistence. A separate temporary environment installs only explicit build
tools before the no-index sdist install; build-tool preparation requires network
access. The pytest wheel integration uses another fresh environment with
`--no-index --no-deps`. Historical source is pinned to repository commit
`6138b60a992d14cf18ad9f35c2b58ad2ee20b244`, not an unverified PyPI artifact.

CI uploads wheel/sdist, JUnit and branch-coverage JSON for every matrix job.
No static pass-count or coverage badge substitutes for those run results.
README and policy-document snippets plus `examples/*.py` are executed.
EXAMPLES.md contains application integration recipes requiring external apps,
services or caller-provided state; these are illustrative and are not claimed
as executed end-to-end integrations.

## Publication is separate

No workflow publishes to PyPI or creates a release. Before a stable release,
review MIGRATION.md against the final code, select/verify the final version
against PyPI, verify the matrix on the exact release commit, inspect artifacts,
and obtain explicit authorization to publish. A CI run passing on a branch is
not evidence that a package has been released. This policy addresses #17 and
the CI requirement remaining in testing umbrella #25.
