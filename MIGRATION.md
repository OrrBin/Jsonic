# Migration from published 1.0.1 to 2.0.0rc1

This is an unpublished major release candidate. No package has been uploaded.

## Observable changes requiring review

- Python support is explicitly 3.8–3.13 instead of published metadata's >=3.6.
  Python 3.6/3.7 were not viable without missing compatibility support; newer
  untested versions are intentionally unqualified. Do not upgrade unsupported
  interpreters without first updating your environment or qualifying support.
- `expected_type` now consistently enforces exact root identity, including
  bool/int, subclasses and codec return types. Previously tolerated mismatches
  are rejected. This does not automatically validate annotations on fields.
- Invalid/ambiguous codec registrations fail instead of overwriting another
  type. Use matching encoder/decoder stable IDs and explicit historical aliases.
- Nested selection consistently uses exclusion precedence. Root collections
  apply field selection to their members, and excluded values/hooks are no
  longer traversed. Update exact output or callback-count assumptions.
- Source objects no longer receive injected metadata or temporarily lose
  private/transient attributes. Custom hooks must still avoid mutating shared
  nested inputs; outer decoder mappings are shallow copies.
- Mixed dictionary/slot objects now retain previously omitted slot values.
  Nested private options and paths propagate through tuple/set adapters.
- Error paths are complete and errors expose structured metadata. Native
  specialized exceptions retain documented compatibility; malformed enum
  payloads are normalized. Avoid depending on old message strings or truncated
  paths; use exception classes, code and path where contracted.
- Omitted constructor defaults are honored. Frozen computed values must match
  constructor-produced invariants. Required InitVars fail earlier because their
  inputs cannot generally be recovered; persist them explicitly in a custom
  codec if needed. Deterministic cycle rejection does not ignore references.

## Additive options and stored data

Defaults retain legacy wire output and legacy import-based decoding. For
externally supplied data, explicitly opt into `safe=True`, register every
trusted tagged class and treat constructors/codecs as trusted application code.
No resource limit or sandbox is implied.

- `validation='strict'` with an expected schema accepts plain typed input using
  the documented non-coercing subset, validates before constructing, and rejects
  unknown fields unless explicitly ignored. Existing root-only decoding remains
  unchanged. See VALIDATION_MODES.md for unsupported schemas and Pydantic policy.
- `wire_format='v2'` must be selected on both writer and reader. It escapes
  literal dictionaries through explicit node kinds; it does not guess versions.
  Read existing trusted payloads deliberately in legacy mode, then write v2.
  Old readers reject v2. Previously lost collision data cannot be recovered.
- `uuid_format='string'`, `pydantic_mode='roundtrip'` and stable codec IDs are
  opt-in new output contracts requiring compatible readers. Legacy UUID output
  and Pydantic presentation output remain defaults. Normal Pydantic validators
  run; arbitrary user serializers/transformations are not universal inverses.

Before switching writers, inventory downstream readers, update/test them and
keep representative old payload fixtures. See WIRE_FORMAT.md, PERSISTENCE.md,
RESOLVERS.md and validation reports for exact limits. Package tests and these
migration notes do not constitute a publication or data-migration operation.
