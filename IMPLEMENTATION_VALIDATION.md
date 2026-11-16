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

## Verification

The final artifact-enabled Python 3.12.11 / Pydantic 2.11.3 run passes
**1,019 tests, zero skips, zero expected failures, zero unexpected failures**.
The merged baseline had 942 cases (941 passed, one expected failure): this
batch adds 77 collected cases and converts the final expected failure into a
passing opt-in v2 contract. Legacy wire defaults are intentionally unchanged.

| Python | Pydantic | Passed | Skipped | Expected failures |
| --- | --- | ---: | ---: | ---: |
| 3.12.11 | 2.11.3, explicit artifact checks | 1,019 | 0 | 0 |
| 3.8.20 | 2.10.6 | 1,016 | 3 artifact-input skips | 0 |
| 3.13.5 | 2.14.3 | 1,016 | 3 artifact-input skips | 0 |
| 3.13.5 | 1.10.27 | 1,009 | 10 version/artifact skips | 0 |
| 3.13.5 | absent | 933 | 41 dependency/artifact skips | 0 |

The local matrix is macOS. Pydantic v2 has one existing deprecated-validator
warning. The package checker inspected and installed both final wheel and
sdist in a clean environment outside the checkout, with no runtime dependencies.
15 documentation snippets/scripts execute with Pydantic; 11 execute without it.
Historical reader checks include a positive legacy control and negative v2
control. Coverage is measured, not asserted from test counts.

The first GitHub run exposed an infrastructure issue: ubuntu-latest moved to
26.04, whose setup-python manifest lacks 3.8/3.9. CI now pins Ubuntu 22.04,
Windows 2022 and macOS 15, with current action versions. Remote run results
are recorded separately after the corrected workflow completes. No local
result is presented as Windows/Linux evidence.
