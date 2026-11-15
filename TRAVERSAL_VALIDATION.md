# Traversal and resolver fixes: validation

Validated 16 November 2026 against merged baseline
`d7534377dd9a174961a5557ffa390681be4f98e2`.

All 13 preceding PRs (#18–#24 and #32–#37) were verified merged before this
batch. These three stacked branches are new work and are not merged:

| Issue | Branch | Base |
| --- | --- | --- |
| #10 / F08 | `feature/f08-traversal-context` | `master` |
| #15 / F13 | `feature/f13-error-context` | F08 |
| #16 / F14 | `feature/f14-resolver-protocol` | F13 |

Review/land in order, retargeting each successor to master after its predecessor
lands. Existing wire fixtures are unchanged.

## Results

The v2 suite now collects **874 cases**, up from 837: **37 new cases**.
Five previous expected failures are ordinary passing tests: tuple/set private
options (2), registered-parent error paths (2), and the documented minimal
resolver signature (1).

| Python | Pydantic | Passed | Skipped | Expected failures |
| --- | --- | ---: | ---: | ---: |
| 3.12.11 | 2.11.3, explicit wheel/history checks | 868 | 0 | 6 |
| 3.8.20 | 2.10.6 | 866 | 2 | 6 |
| 3.13.5 | 2.14.3 | 866 | 2 | 6 |
| 3.13.5 | 1.10.27 | 863 | 6 | 5 |
| 3.13.5 | absent | 810 | 37 | 5 |

There are no unexpected failures. The default artifact skips and dependency
API skips are explicit; absent-dependency skips are not integration evidence.
The existing Pydantic v1-style validator warning remains in v2 jobs. macOS was
tested; Windows/Linux and other Python versions are not established by this run.

The final shuffled-order run uses seed 20261116. The resolver documentation
example and all three existing example modules execute successfully. The newly
built wheel is used for isolated installed-package persistence; an actual
historical writer/reader tree is used for compatibility checks. Both are
explicit test inputs rather than implicit downloads/builds.

```sh
python -m pytest -q -o addopts=''
python -m pytest -q -o addopts='' --test-order-seed=20261116
python -m pytest -q -o addopts='' \
  --wheel-path=/absolute/path/to/new-wheel.whl \
  --legacy-jsonic-root=/absolute/path/to/historical/source
```

## Regression scope

- Nested tuple/set/list/dictionary traversal preserves both private flags,
  full paths and active safe authorization. Context state resets after failed
  calls and remains independent between threads/tasks.
- Dataclass/type-hinted extraction, registered objects, custom decoders and
  Pydantic child traversal preserve parent paths. Jsonic errors provide code,
  field and expected/actual type metadata where relevant; normalized errors
  chain their original causes without adding input values to root input/type
  diagnostics.
- Public one-payload serializers, legacy private-flag serializers, new
  context-aware methods, and opaque legacy callables all remain callable.
  Signature matching occurs before execution. Callback-body TypeError is
  invoked once, then propagated with its original cause.
- Context-based child serialization advances selection before traversal,
  skipping excluded unsupported values. The context is immutable and scoped
  to active calls. See RESOLVERS.md for the extension contract.
- An initial Python 3.8 run found excess call frames at 100 nested tuples.
  Error normalization was inlined at the boundary; the existing 100-level
  test now passes without changing recursion limits or weakening assertions.

## Compatibility and remaining work

Root defaults, codec IDs and serialized envelopes are unchanged. An omitted
private decoding option in a nested callback inherits the active traversal;
explicit False still excludes private fields. Error wrappers preserve existing
specialized exception subclasses and ValueError/KeyError/RuntimeError behavior
as described in CHANGELOG.md and RESOLVERS.md; this does not promise to rewrite
native Pydantic validation locations or arbitrary user callback messages.

Six strict expected failures remain: #12 constructor/UUID/InitVar behavior (4),
#11 asymmetric Pydantic aliases (1, v2 only), and #13 literal dictionary/metadata
collisions (1). Their product fixes are outside this batch. #14 field-validation
semantics and #17 packaging/CI/release claims also remain separate work.

TESTING.md records the earlier testing audit; its 837-case/11-expected-failure
tables are historical. This report is the current traversal-fix result. No
package version change, publication, or merge is included.
