# Package testing guide and audit results

Implemented for tracking issue #25 and follow-ups #26–#31 on 15 November 2026.
Production code and the wire format are unchanged. Known product defects remain
owned by their original issues; adding tests does not claim to fix them.

## Running the tests

Install `requirements-dev.txt` and the chosen optional Pydantic version into an
isolated environment, then run:

```sh
python -m pytest -q -o addopts=''
python -m pytest -q -o addopts='' --test-order-seed=20261115
python -m pytest -q -o addopts='' --cov=jsonic --cov-branch --cov-report=term-missing
```

Hypothesis uses bounded, deterministic generation: at most 50 examples per
recursive-tree case and 15 per adapter round-trip case. Collected pytest case
counts do not include each generated example as a separate test. Failed
examples remain shrinkable and ordinary focused regression cases are kept
for known defects.

Two integration cases require explicit artifacts. Normal runs skip them with
reasons; they never build packages or download dependencies implicitly:

```sh
python -m pytest -q -o addopts='' tests/integration \
  --wheel-path=/absolute/path/to/package.whl \
  --legacy-jsonic-root=/absolute/path/to/historical/source
```

The wheel case installs with `--no-index --no-deps` into a fresh environment,
then reads and writes in separate isolated Python processes outside the
checkout. Prepare the wheel separately, for example using `python -m build
--wheel --no-isolation` with build, setuptools and wheel installed. Build/CI
configuration and release-support decisions remain owned by #17. The legacy
reader/writer case was executed with source from commit
`6138b60a992d14cf18ad9f35c2b58ad2ee20b244`.

## Verified results

The original audit collected 560 cases (558 passed, 2 skipped). The expanded
Pydantic v2 suite collects **837 cases**, a net increase of **277 cases**.
Existing assertions were also strengthened. The two unconditional enum skips
are now real tests using registered enum fixtures.

| Python | Pydantic | Passed | Skipped | Strict expected failures |
| --- | --- | ---: | ---: | ---: |
| 3.12.11 | 2.11.3, both artifact checks enabled | 826 | 0 | 11 |
| 3.8.20 | 2.10.6 | 824 | 2 | 11 |
| 3.13.5 | 2.14.3 | 824 | 2 | 11 |
| 3.13.5 | 1.10.27 | 821 | 6 | 10 |
| 3.13.5 | absent | 769 | 36 | 10 |

All runs have zero unexpected failures. Skips distinguish missing explicit
artifacts from dependency/version APIs. In particular, Pydantic v1 does not
support validation-alias choices/paths or v2 field serializers; absent-Pydantic
jobs do not constitute integration coverage. Collection of a module skipped
at import time yields different totals from collecting all its parameter cases.
The existing v1-style validator emits one deprecation warning on v2.

A full shuffled-order run with seed 20261115 also passed: 824 passed, 2 skipped,
11 expected failures. Separate child pytest runs verify fixture isolation in
both mutation/clean-check orders. A mutation pilot deliberately erases error
paths in a child process and confirms all four exact serialization-path tests
fail, without touching the repository's production code.

## Coverage evidence

On the same Python 3.12/Pydantic 2 environment as the original audit:

| Metric | Before | After |
| --- | ---: | ---: |
| Statements executed | 681/731 (93.16%) | 701/731 (95.90%) |
| Branches executed | 315/354 (88.98%) | 331/354 (93.50%) |

Combining separate v2, v1 and absent-Pydantic coverage jobs covers **711/731
statements (97.26%)** and **335/354 branches (94.63%)**. These union figures
are not a single-environment result. Coverage.py's combined line/branch
percentage is a third metric; it should not be confused with either column.
No new coverage exclusions were introduced.

Per-module union across v2/v1/absence jobs:

| Module | Line coverage | Branch coverage |
| --- | ---: | ---: |
| `jsonic/__init__.py` | 100.0% | — |
| `jsonic/decorators.py` | 100.0% | 100.0% |
| `jsonic/default_serializers.py` | 100.0% | — |
| `jsonic/exceptions.py` | 100.0% | 100.0% |
| `jsonic/pydantic_support.py` | 100.0% | 100.0% |
| `jsonic/resolvers/__init__.py` | 100.0% | — |
| `jsonic/resolvers/dataclass_resolver.py` | 100.0% | 100.0% |
| `jsonic/resolvers/typehinted_resolver.py` | 97.1% | 93.8% |
| `jsonic/serializable.py` | 96.7% | 93.3% |
| `jsonic/set_serializer.py` | 100.0% | — |
| `jsonic/tuple_serializer.py` | 100.0% | — |
| `jsonic/type_resolver.py` | 87.1% | 100.0% |
| `jsonic/util.py` | 100.0% | 100.0% |

## Coverage map and test ownership

| Work | Main tests | Behavioral scope |
| --- | --- | --- |
| #26 | `test_codec_boundaries.py`, `test_failure_paths.py` | Codec boundaries, invalid registration/aliases, wrapper calls, malformed input, concrete expected types, exception context, hint fallback/defaults, bounded diagnostics |
| #27 | `test_generated_contracts.py`, `tests/support/models.py` | Recursive primitive/container trees; generic, hinted, dataclass, slots, registered, custom-codec and external-resolver adapters; root/list/dict/tuple/set shapes; text/value input; selection precedence, private options, repeated references, normalization and cycles |
| #28 | `test_safe_policy_lifecycle.py` | Full-tree preflight, reentrant hooks/resolvers, explicit downgrade attempts, failure cleanup, authorization snapshots, thread barriers, independent and inherited asyncio task contexts |
| #29 | `test_constructor_contracts.py`, `test_external_resolver_contracts.py`, `test_pydantic_contract_matrix.py` | Default factories, keyword/positional-only constructors, mapped/transient arguments, invariants, alias choices/paths and collection selectors, priority/ties/fallback, external protocol and error shapes |
| #30 | `tests/integration/`, `tests/fixtures/wire/v1.json` | Fresh readers/writers, explicit independent registration, exact golden payloads, moved classes/stable IDs/legacy aliases, malformed fixtures, actual legacy reader and installed-wheel persistence |
| #31 | `test_error_context.py`, `test_fixture_isolation.py`, `test_assertion_sensitivity.py`, existing tests | Exact paths and exceptions, intended error-stage sentinels, actual set/tuple-key boundaries, precise numeric behavior, enum skip removal, resolver state cleanup and mutation sensitivity |

The shape/option matrix is deliberately constrained rather than an unbounded
Cartesian product. The generated adapter matrix exercises legacy decoding;
root adapters also exercise safe decoding with explicit expected-type
authorization. Generated primitive/container trees and dedicated lifecycle
tests cover nested safe mode. Custom callbacks own their recursive extraction;
the tests do not assume Jsonic can undo work inside them.

Golden payload provenance identifies the unchanged serializer implementation
and versioned fixture models, rather than claiming compatibility with untested
published distributions. Python 3.8's unnamed combined-flag payload and newer
Python's named combined-flag payload are both retained as historical variants.
New readers accept both by value. An actual historical writer also produces
nine primitive/container/object/codec payloads that the new safe reader reads.
Actual old readers reject newly opted-in
stable IDs; retaining an old-data decoder does not make old readers forward
compatible. Repeated-reference equality is tested separately from graph
identity, which is not promised.

## Known expected failures

Every expected failure is strict and constrained to the relevant exception
type. Unexpected passes fail the suite, prompting removal of obsolete markers.
Unexpected exception classes fail normally. No blanket xfail is applied to a
test module or generated suite.

| Product issue | Cases | Expected contract still unmet |
| --- | ---: | --- |
| #15 / F13 | 2 | Registered-parent decoding preserves complete parent paths |
| #10 / F08 | 2 | Tuple/set boundaries preserve the private-field option |
| #13 / F11 | 1 | Literal metadata-looking dictionary keeps its identity and fields |
| #12 / F10 | 4 | Frozen non-init fields, omitted Serializable defaults, UUID round trips and required InitVar reconstruction |
| #16 / F14 | 1 | Minimal resolver follows the declared one-payload-argument signature |
| #11 / F09 | 1 (v2 only) | Asymmetric validation/output aliases round-trip |

Some constructor/alias behavior needs a product contract decision. These tests
record desired persistence behavior and keep it visible rather than silently
asserting that the current defect is correct. Field validation (#14), resource
limits and graph preservation are not implied by the safe-decoding tests.

## Remaining coverage and release scope

The residual uncovered lines include four abstract resolver `pass` statements,
an impossible-with-an-ordinary-class missing-`__init__` guard, legacy encoder
fallbacks bypassed by preprocessing, and defensive decoder guards dominated by
public dispatch/preflight checks. Some diagnostics/fallback branches remain
reachable and are further opportunities; no claim of exhaustive coverage is
made. Do not corrupt private state merely to execute a dominated guard or add
meaningless tests for abstract `pass` statements.

The CI expansion, Python-version metadata reconciliation, automated wheel
builds, and documentation-example jobs belong to #17. These tests provide the
cases and artifact inputs for that work. The matrix above verifies macOS on
Python 3.8, 3.12 and 3.13; it does not establish Windows/Linux behavior or the
intervening/other Python versions. No package publication or merge is included.
