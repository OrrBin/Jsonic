# Priority fixes: F01–F07

Validated on 15 November 2026 against baseline commit
`6138b60a992d14cf18ad9f35c2b58ad2ee20b244`.

## Branch order

These are stacked feature branches. Each adds one finding's implementation,
regression tests and compatibility notes to its predecessor. `master` is unchanged.

| Finding | Issue | Branch | Base |
| --- | --- | --- | --- |
| F01 | #3 | `feature/f01-safe-deserialization` | `master` |
| F02 | #4 | `feature/f02-nonmutating-serialization` | F01 |
| F03 | #5 | `feature/f03-traversal-filtering` | F02 |
| F04 | #6 | `feature/f04-type-checks-and-codec-ids` | F03 |
| F05 | #7 | `feature/f05-nonmutating-deserialization` | F04 |
| F06 | #8 | `feature/f06-flag-roundtrips` | F05 |
| F07 | #9 | `feature/f07-mixed-slot-attributes` | F06 |

Review and land in order. After a predecessor lands, retarget the next pull
request to `master` before merging it.

## Results at the combined branch

| Python | Pydantic | pytest | Result |
| --- | --- | --- | --- |
| 3.8.20 | 2.10.6 | 8.3.5 | 558 passed, 2 skipped |
| 3.12.11 | 2.11.3 | 8.3.2 | 558 passed, 2 skipped |
| 3.13.5 | 2.14.3 | 9.2.0 | 558 passed, 2 skipped |
| 3.13.5 | 1.10.27 | 9.2.0 | 557 passed, 3 skipped |
| 3.13.5 | absent | 9.2.0 | 526 passed, 34 skipped |

The two baseline skips concern local enum classes. Pydantic v1 additionally
skips the v2-only field-serializer test. With Pydantic absent, integration tests
skip explicitly; those skips are not integration coverage. Pydantic v2 emits
one existing deprecation warning for a v1-style validator in the original tests.

The original suite on Python 3.13/Pydantic 2 had 447 passed, 1 failed, 2 skipped.
The existing combined-flag failure is repaired by F06. Earlier branches were
checked with that single known failure deselected; after F06, full-suite runs
have no deselections. There are 110 additional collected regression cases.

Measured line coverage on Python 3.12/Pydantic 2.11.3 is **93% overall** and
**95% for `jsonic/serializable.py`**. Coverage is evidence of execution, not a
claim of exhaustive safety or correctness. Python 3.9–3.11 and newer versions,
other operating systems, and published distributions were not tested here.

## Checks and regression scope

Run the complete suite with pytest, Hypothesis and the chosen optional
Pydantic version installed:

```sh
python -m pytest -q -o addopts=''
python -m pytest -q -o addopts='' --cov=jsonic --cov-report=term-missing
```

New tests exercise safe nested dispatch before imports/constructors, malformed
tags, concurrent policy isolation, source state after successful/failed
serialization, event-controlled concurrent readers, shallow decoder input
isolation, root collection redaction, excluded cycles/hooks/unsupported values,
generated nested dictionary collections, Pydantic filtering before field
serializers, exact root expected types, codec aliases/collisions/registration
order, combined/zero/unknown enum flags, and mixed/inherited/private slots.

All three example modules execute successfully on Python 3.12/Pydantic 2.11.3:
`examples.nested_filtering_example`, `examples.pydantic_example`, and
`examples.pydantic_aliases_example`. A separate-process persistence probe also
successfully writes then safely reads a registered dataclass with nested datetime.
`git diff --check master` passes.

## Compatibility decisions

- F01 is the additive safe-mode path allowed by the issue: callers must use
  `safe=True`. Legacy default decoding still dynamically imports types and is
  only suitable for trusted data. Making safe decoding the default remains
  major-release work. Registered hooks and constructors are trusted code.
- F03 consistently gives exclusion precedence, including nested conflicts;
  this repairs an inconsistent existing behavior but changes some output.
  Review release classification before publishing. Custom callbacks own their
  extraction; output filtering cannot undo work done inside a callback.
- F04 preserves legacy writer tags by default. Stable IDs are opt-in and
  encoder/decoder pairs must agree. Root type checks are exact, including
  bool/int distinctions; this is not field validation or typed structuring.
- F05 protects the outer decoder mapping with a shallow copy. Nested values
  are shared with user hooks; those hooks must treat them as read-only.
- F07 emits slot fields that previously disappeared. Exact-output consumers
  must account for the restored fields.

See `CHANGELOG.md` for per-finding details. F08–F15 remain outside this batch.
No package release, merge, or issue closure is part of this work.
