# Jsonic Roadmap

## Implemented in the 2.0 line

See README.md for implemented contracts, RELEASE.md for Python/dependency
support and CI, and MIGRATION.md for upgrade behavior. The 2.0.0rc1 candidate
is published on PyPI; 2.0.0 preparation retains its runtime behavior. Strict typed input, v2 dictionary transport,
Pydantic field-state persistence and traversal repairs are implemented.

## Deferred

- Optional ignoring of circular references (#1); rejection is the current policy.
- Broader annotation/codec support outside the documented strict subset.
- Graph identity, resource budgets, async APIs and JSON Schema generation.

These are proposals without committed dates or performance/competitor claims.
Tests and coverage are measured per CI run; see TESTING.md for historical audits.
