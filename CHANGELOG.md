# 2.0.0rc1 — release candidate (unpublished)

Prepared 16 November 2026. This candidate packages the merged remediation and
testing work for review; it has not been uploaded to PyPI or TestPyPI.

- Breaking changes include Python 3.8–3.13 support boundaries, exact root type
  checks, codec collision rejection, consistent filtering, restored slot fields,
  stricter immutable/constructor behavior and revised diagnostics.
- Additive options include registry-only safe decoding, strict typed input,
  collision-free v2 transport, stable codec IDs, UUID strings and Pydantic
  field-state persistence. Legacy wire defaults remain available.
- Build qualification includes wheel/sdist clean installs, historical payloads,
  executed documentation and the Python/Pydantic/platform CI matrix.
- Review MIGRATION.md before upgrading from published 1.0.1. Circular-reference
  ignoring (#1) remains deferred; cycles are rejected.


## F09 — explicit Pydantic field-state persistence (#11)

`serialize(..., pydantic_mode='roundtrip')` writes canonical field names and a
versioned Pydantic type tag. Readers translate supported string input aliases
before normal Pydantic validation; nested models retain their own tags and
container types. The default presentation mode still uses existing output
aliases and native dump serializers. Persistence mode reads declared raw fields
and skips presentation serializers/computed output. It supports unique string
validation aliases; alias choices/paths, root models and extra stored attributes
are explicitly rejected rather than guessed. Normal validators still run and
arbitrary/non-idempotent user transformations are not promised reversible.

The new mode is opt-in and is a new format requiring an updated reader. Existing
wire output is unchanged. Selection uses canonical names in persistence mode;
safe decoding still requires authorization of every nested model. No package
release or default-format switch is included.

## F10 — constructor defaults, frozen fields and UUIDs (#12)

Generic/Serializable and type-hinted reconstruction share missing/defaulted
argument rules, including mapped and transient defaults. Frozen dataclasses
recompute non-init fields during construction and validate stored values;
they are never overwritten by bypassing immutability. Mutable non-init fields
retain legacy restoration. Required InitVar inputs are explicitly unsupported:
serialization/decoding fail clearly and a custom codec is required to persist
them. This rejects an unsupported shape earlier, rather than emitting data
that cannot reconstruct its constructor inputs.

UUID decoding accepts historical int/is_safe payloads without changing default
writer output. `serialize(..., uuid_format='string')` opts into a portable UUID
string representation; it preserves identifier value and omits process-local
is_safe metadata. The format option propagates through nested traversal. New
UUID output is opt-in for minor-release compatibility; no release is published.

Cycle rejection checks live ancestor frames before recursive object traversal
and guards raw custom-codec mappings during JSON conversion. This avoids the
recursion-limit-dependent rejection that caused a Python 3.8 abort during
validation. Shared references remain valid, completed task contexts do not keep
stale ancestors active, and independent threads have separate ancestor paths.
The default still rejects cycles; #1's optional ignore policy is separate work.

## F14 — executable resolver protocol (#16)

The dispatcher supports the documented one-payload serializer and the legacy
two-argument private-field serializer. Resolvers may opt into a keyword-only
TraversalContext on serialization/deserialization. Signature binding happens
before invocation; a TypeError raised inside user code is never retried.
TraversalContext is exported from jsonic and supplies immutable options/path
plus serialize/deserialize child helpers. Decoder data is already recursively
decoded; callbacks should not decode it a second time. Priority/tie behavior
and default wire representations are unchanged. Opaque/non-inspectable callables
retain historical two-argument invocation. Callbacks return the documented
mapping/instance shapes.

## F13 — complete adapter error paths (#15)

Dataclass/type-hinted extraction, registered/resolver reconstruction, Pydantic
child traversal and tuple/set adapters retain complete parent paths. Normalized
TypeError/AttributeError failures chain their original cause. Jsonic errors add
code, expected_type, actual_type and field metadata without removing existing
exception inheritance. Input values are not included in root type/input errors.
Specialized TypeError/AttributeError subclasses, native ValueError subclasses
(including Pydantic ValidationError), KeyError and
application RuntimeError remain catch-compatible; their own messages/locations
are not rewritten. User callback error text is preserved and may contain values
chosen by that callback. The wire format is unchanged.

## F08 — tuple/set traversal context (#10)

Built-in tuple/set adapters preserve private-field options and parent paths in
both directions using a call-local traversal context. Selection and safe-mode
authorization continue to flow through recursive callbacks. Omitting the
private decoding option in a nested callback inherits its caller's option;
an explicit False still excludes private fields. Root defaults and wire tags
are unchanged. Context is reset on success and failure and isolated by task/thread.

## F07 — mixed dictionary/slot layouts (#9)

Registered types, generic objects and type-hinted resolvers share an attribute
enumerator combining dynamic attributes with initialized slots throughout the
MRO. It excludes infrastructure, deduplicates storage names, and handles
name-mangled private slots. Private, transient and selection rules apply to
both layouts. Payloads now contain previously lost slot fields; exact-output
consumers should account for those additional fields.

## F06 — combined enum flags (#8)

`Flag` and `IntFlag` reconstruct from their stored numeric value, preserving
combined and zero values. Ordinary enums continue to use named members.
Unknown bits follow the enum class's own boundary policy. Malformed enum data
raises `DeserializationError` with the original cause. The wire format is unchanged.

## F05 — preserve decoding input (#7)

Custom decoders receive a separate outer dictionary without the type tag.
Success, failure and concurrent readers no longer observe removed metadata.
This is a shallow copy: nested values retain their identity and custom hooks
must treat them as read-only if caller input must remain unchanged. Built-in
decoders do not mutate nested input. Wire format and callback shape stay stable.

## F04 — expected types and codec identity (#6)

Root `expected_type` now uses exact Python type identity on every decode path,
including primitives, tuples, sets, enums and custom codecs. `bool` does not
satisfy `int`; subclass acceptance, unions and field validation are not implied.
Type mismatches are rejected before imports or callbacks when identifiable
from the payload; decoder return types are also checked. Previously tolerated
mismatches now raise `DeserializationError`.

Custom decorators accept an optional stable `type_id`; deserializers also
accept explicit `aliases`. Encoder/decoder pairs must use the same ID.
Existing writers retain their short tags, while readers also accept qualified
IDs. Ambiguous decoder tags are rejected instead of overwriting a different
type. Use explicit unique IDs for same-name classes. These additions do not
change the default output format; old readers cannot read newly opted-in IDs.

## F03 — traversal-time field selection (#5)

Field selection now runs before reading/traversing built-in object fields.
Root lists, tuples and sets apply selectors to each member, including nested
collections. Excluded unsupported values, cycles and child hooks are skipped.
Pydantic receives native include/exclude rules before dumping fields.

Exclusion wins at every nesting level, preserving existing top-level behavior
and correcting the previous include-wins documentation. This changes nested
overlaps that previously ignored exclusions; review redaction output when
upgrading. Dots denote path separators; there is no escaping for literal keys
containing dots. Custom codecs still control their own extraction and recursion;
their output is filtered, but Jsonic cannot prevent work inside user callbacks.

## F02 — non-mutating serialization (#4)

Serialization reads a separate attribute mapping and writes metadata only to
the output. Private/transient fields remain present during traversal and after
errors. Custom serializer and resolver result mappings are copied before tags
are added. The wire format is unchanged. Applications must not rely on the
previous undocumented injection of `_serialized_type` onto source instances.

## F01 — controlled decoding (#3)

`deserialize(..., safe=True)` preflights all nested tags before imports,
constructors or decoding hooks run. Register trusted classes with
`register_jsonic_type`; an explicit root `expected_type` also authorizes that
class for the call. Registered custom decoders are trusted application code.
The policy is call-local and follows recursive calls through legacy adapters.

The legacy default still dynamically imports classes and is only suitable for
trusted stored data. Safe mode is additive; changing the default is reserved
for a major release. No wire format changes are made.

## F11 — collision-free dictionaries (#13)

Add explicit `wire_format='v2'` on serialization and decoding. Versioned node
kinds distinguish literal dictionaries from adapter metadata, including literal
dictionaries that imitate the v2 envelope itself. Complete shapes and duplicate
keys are validated before reconstruction. Default legacy wire contracts remain
unchanged. V2 requires a new reader; see WIRE_FORMAT.md for migration and custom
codec responsibilities. This is additive opt-in functionality, not a default
wire-format replacement.

## F12 — explicit strict structuring (#2, #14)

Add `validation='strict'` to deserialize with an explicit expected schema.
Validate a scoped subset of primitive/container/union/literal and annotated-class
inputs without coercion before constructing any schema objects. Unknown fields
are rejected unless explicitly ignored; matching class tags are schema-bound,
not imported. Defaults, frozen invariants, forward references, safe nested calls
and error paths have dedicated cases. Unsupported schemas fail explicitly.
Default root-only type checking remains unchanged. See VALIDATION_MODES.md.

## F15 — package and release qualification (#17, #25)

Move metadata to pyproject.toml and mark this checkout 2.0.0.dev0, unreleased.
Declare Python 3.8–3.13, package-only wheels, optional Pydantic and one developer
dependency path. Add version/dependency CI plus Windows/macOS boundary coverage,
wheel/sdist inspection and clean installations, explicit historical/wheel tests,
measured branch-coverage artifacts and executed documentation/examples. Remove
unsupported static counts, competitor/performance rankings and placeholder links.
See RELEASE.md and MIGRATION.md for publication separation and breaking-change
review. No package is published and no stable version is selected automatically.
