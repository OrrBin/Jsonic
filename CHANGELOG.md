# Unreleased

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
