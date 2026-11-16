# Collision-free persistence (wire v2)

Legacy output remains the default. It interprets `_serialized_type`, `_is_tuple`
and `_is_set` as metadata, so arbitrary literal dictionaries can lose their
identity/fields. Use the explicit v2 format for new persistence that needs
arbitrary JSON dictionaries:

```python
from jsonic import serialize, deserialize
value = {'_serialized_type': 'literal', '_is_tuple': True, 'items': [1]}
wire = serialize(value, wire_format='v2', string_output=True)
assert deserialize(wire, wire_format='v2', string_input=True, safe=True) == value
```

The outer envelope has exactly `_serialized_type: "jsonic:wire:v2"`, `version: 2`
and `payload`. Every node is a two-item array: `["value", primitive]`,
`["list", nodes]`, `["dict", pairs]` or `["object", pairs]`. A pair is a string
key and child node. Literal dictionaries always use `dict`, even if they
exactly imitate an envelope. Generated adapter metadata uses `object`.
Duplicate pairs, unknown kinds, incomplete/extra envelope fields and malformed
container envelopes are rejected before constructors run. Safe decoding still
preflights all real object tags; literal tag-looking keys authorize nothing.

Built-in adapters preserve this distinction recursively. Custom codecs that
serialize child objects should use `TraversalContext.serialize` so literal
children retain their marker. Handwritten raw codec output is the codec's wire
contract, not automatically identifiable user data. Readers receive decoded
literal dictionaries through normal child decoding; custom decoders must use
the context for recursive Jsonic values as documented in RESOLVERS.md.

Dictionary keys follow JSON normalization (non-string JSON-compatible keys
become strings; equivalent normalized keys collapse); graph identity and
nonfinite-number portability are not added. Selection still applies before
traversal. Existing legacy writer/reader behavior stays available deliberately
with `wire_format='legacy'` (the default). A v2 reader requires a v2 envelope;
it never guesses whether a plain dictionary is metadata. Old readers reject
v2's tag: new-reader/old-data compatibility requires explicitly using legacy
mode, and old-reader/new-v2-data compatibility is not promised. Migrate stored
data by decoding trusted old data in legacy mode and reserializing in v2;
legacy collisions already lost by prior decoding cannot be recovered.
