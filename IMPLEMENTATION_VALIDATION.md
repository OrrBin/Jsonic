# Remaining-issue implementation validation

Work dated 16 November 2026, based on merged master `501ae1c`.

- #13: opt-in v2 node transport, explicit legacy reader, collision/property and
  malformed-shape tests, safe preflight and historical-reader rejection.
- #2/#14: explicit strict typed input, no coercion, documented supported subset,
  precise field paths, full validation before constructors and native invariants.
- #17/#25: pyproject metadata, development version 2.0.0.dev0, declared Python
  3.8–3.13, optional Pydantic, CI, clean wheel/sdist checks, runnable examples and
  migration/release documentation. No publication workflow is added.
- #1 (ignore circular references) is deliberately not implemented. Cycles are
  rejected, including malformed Python input supplied to the new modes.

The new APIs and format are opt-in. Legacy dictionary collisions are addressed
by choosing v2 on writer and reader, not by silently changing old wire defaults.
Strict typed input is a scoped schema contract; unsupported arbitrary typing,
Pydantic models and datetime/UUID transformations have documented separate paths.

## Final local verification

The final artifact-enabled Python 3.12.11 / Pydantic 2.11.3 run passes
**1,024 tests, zero skips, zero expected failures, zero unexpected failures**.
The merged baseline had 942 cases (941 passed, one expected failure): this
batch adds **82 collected cases** and converts the final expected failure into
a passing opt-in v2 contract. Legacy wire defaults are intentionally unchanged.

| Python | Pydantic | Passed | Skipped | Expected failures |
| --- | --- | ---: | ---: | ---: |
| 3.12.11 | 2.11.3, explicit artifact checks | 1,024 | 0 | 0 |
| 3.8.20 | 2.10.6 | 1,021 | 3 artifact-input skips | 0 |
| 3.13.5 | 2.14.3 | 1,021 | 3 artifact-input skips | 0 |
| 3.13.5 | 1.10.27 | 1,014 | 10 version/artifact skips | 0 |
| 3.13.5 | absent | 938 | 41 dependency/artifact skips | 0 |

The local matrix is macOS. Pydantic v2 has one existing deprecated-validator
warning. The package checker inspected and installed both wheel and sdist in a
clean environment outside the checkout, with no runtime dependencies; the final
runtime wheel is rebuilt for the full artifact-enabled pytest run.
15 documentation snippets/scripts execute with Pydantic; 11 execute without it.
Historical reader checks include a positive legacy control and negative v2
control. Parent v2 branch independently passed 964 tests with 3 artifact skips.
Shuffled order seed 20261116 passed before the last cross-version/path refinements.

Measured Python 3.12 line coverage is 1,162/1,206 (96.35%); branch coverage is
514/552 (93.12%). Coverage.py's combined metric is separately 95.34%. There are
no new exclusions, blanket xfails or skips to conceal errors. Unsupported schema
and malformed-input errors, literal data, caller preservation, constructor counts
and context cleanup have explicit regressions.

## CI findings and remote evidence

The first runner matrix exposed that ubuntu-latest moved to 26.04, whose
setup-python manifest lacks 3.8/3.9. CI pins Ubuntu 22.04, Windows 2022 and
macOS 15 Intel with current action versions. Intel avoids the observed queued
Arm64 pool; local macOS runs use Arm64. No paid larger runner is requested.

The wider matrix also exposed two previously untested contracts: Python
3.9/3.10 GenericAlias objects can pass isinstance(..., type), and Windows fixture
reads used the locale code page. The legacy concrete-type guard now checks
typing origin before safe authorization. UTF-8 fixture/document reads and
explicitly matched child-process encodings preserve Unicode across platforms.
Two additional strict-input regressions verify paths inherited by custom
callbacks and nested schema constructors. All were fixed, not skipped.

Remote run links and job conclusions are recorded in the PR description after
completion. A pending or failed remote job is not claimed as platform evidence.
See RELEASE.md to reproduce the workflow and MIGRATION.md for compatibility.
No merge or package publication is performed by these changes.
