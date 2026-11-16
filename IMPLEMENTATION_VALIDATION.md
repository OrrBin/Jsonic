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

The first complete candidate passed 997 artifact-enabled cases with no skips,
expected failures or unexpected failures. An additional 22 malformed-input and
policy/error cases were added before the final run; final results are recorded
below after verification. Prior baseline: 941 passed, 1 strict expected failure.

Local matrix covers macOS Python 3.8/3.12/3.13 and Pydantic v1/v2/absent.
The package checker successfully inspected and installed both wheel and sdist
in a clean environment outside the checkout, with no runtime dependencies.
15 documentation snippets/scripts execute with Pydantic; 11 execute without it.
Historical reader checks include a positive legacy control and negative v2
control. No static coverage threshold or cross-platform result is inferred
from those local runs. The committed GitHub workflow supplies the additional
Python versions and selected Windows/macOS jobs; remote results are separate.
