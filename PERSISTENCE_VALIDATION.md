# Constructor and Pydantic persistence validation

Validated 16 November 2026 against merged baseline
`af539e4cf12ff44126270b16cb45e062be251ddd`.

PRs #38, #39 and #40 were merged into master in order, their merged tree was
verified against the tested branch, and the merged suite passed. The two new
stacked branches below are separate, unmerged work:

| Issue | Branch | Base |
| --- | --- | --- |
| #12 / F10 | `feature/f10-constructor-and-uuid` | `master` |
| #11 / F09 | `feature/f09-pydantic-persistence` | F10 |

## Final combined results

The v2 suite collects **942 cases**, up from 874 (**68 new cases**). Five prior
expected-failure cases now have passing contracts: frozen non-init fields,
omitted Serializable defaults and UUID round trips reconstruct successfully;
required InitVar inputs are explicitly rejected; asymmetric Pydantic aliases
round-trip in the opted-in field-state format. Default presentation output
remains intentionally distinct from reversible persistence.

| Python | Pydantic | Passed | Skipped | Expected failures |
| --- | --- | ---: | ---: | ---: |
| 3.12.11 | 2.11.3, explicit wheel/history checks | 941 | 0 | 1 |
| 3.8.20 | 2.10.6 | 939 | 2 | 1 |
| 3.13.5 | 2.14.3 | 939 | 2 | 1 |
| 3.13.5 | 1.10.27 | 932 | 9 | 1 |
| 3.13.5 | absent | 857 | 39 | 1 |

There are no unexpected failures in the final candidate. Artifact inputs are
explicit: default runs skip the installed-wheel and historical-reader tests.
Version/dependency API skips are explained separately and are not integration
evidence. One existing v1-style validator warning remains in v2 jobs.

The only remaining strict expected failure is the literal dictionary/metadata
collision in #13. #14 field-validation semantics, #17 packaging/CI/release work,
and #1's optional ignore-cycles policy remain separate issues.

## Evidence and regressions

- Constructor matrices cover required/defaulted and mapped arguments,
  transient defaults, native missing-mapping KeyError compatibility, frozen
  recomputed invariants and source/payload preservation. Required InitVars
  fail before unusable persistence is emitted; defaulted/variadic constructor
  cases remain supported where reconstructable under legacy restoration.
- UUID cases cover all SafeUUID states, identifier extremes, unchanged legacy
  wire output, nested portable-string output, malformed payloads and application
  short-name codecs. Standard codecs use qualified IDs. A historical writer's
  UUID payload is read by the new safe decoder.
- Pydantic cases cover string aliases, nested typed models in lists/dicts/
  tuples/sets, text/value input, field selection, safe registration, namespace
  collisions and native validation constraints. Unsupported choices/paths,
  extra attributes, root models and ambiguous aliases fail explicitly.
- Fresh processes initialize model registrations independently. A real
  historical reader accepts the unchanged presentation format for an importable
  compatibility model and rejects the opted-in fields-v1 format for that same
  model. Historical writer cases cover ten legacy value families.
- The new wheel is installed without dependencies or network access into a
  fresh environment outside the checkout. Its separate writer/reader processes
  round-trip a frozen dataclass with a computed field, datetime and UUID string.
- The entire suite also passes shuffled order with seed 20261116: 939 passed,
  2 artifact skips, 1 expected failure. Documentation examples pass on both
  Pydantic v1 and v2. No recursion limits or existing depth assertions changed.

## Python 3.8 cycle failure found and fixed

An initial parallel run exited with SIGABRT without a Python traceback. The
macOS crash report showed recursive-call overflow (`_Py_CheckRecursiveCall`),
and progress localized it to the circular-reference cases. Diagnostic reruns
passed, but relying on eventual recursion-limit failure was unsafe.

Serialization now detects objects already on the live ancestor path before
reentering their adapters. Raw custom-codec mappings also have an encoder
cycle guard. Shared references in separate branches remain valid. Completed
frames are invalidated for copied task contexts and do not retain source
objects; independent threads have separate ancestor paths.

Tests prove a cyclic resolver is invoked once, cyclic models/containers are
rejected without mutation, completed task/independent thread contexts do not
produce false cycles, and 100 repeated cyclic dataclass attempts succeed in a
fresh process. The unchanged 100-level acyclic tuple case still passes. The
final Python 3.8 full suite passes with these guards; no skip or xfail was added
to hide the abort. This improves rejection, not #1's requested ignore option.

## Commands and compatibility

```sh
python -m pytest -q -o addopts=''
python -m pytest -q -o addopts='' --test-order-seed=20261116
python -m pytest -q -o addopts='' \
  --wheel-path=/absolute/path/to/new-wheel.whl \
  --legacy-jsonic-root=/absolute/path/to/historical/source
```

See PERSISTENCE.md and CHANGELOG.md for the exact contracts. New output formats
require explicit options and a compatible reader; default UUID/Pydantic output
is unchanged. Normal Pydantic validators still run, and arbitrary input-only
or non-idempotent transformations are not promised reversible. Earlier
required-InitVar rejection and error-contract changes need release/migration
review before publication. No package version change, publication or merge of
these two new branches is included. The platform matrix is macOS; other OSes
and untested Python versions are not established here.
