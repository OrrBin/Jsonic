# Root identity and strict typed input

The existing `deserialize(data, expected_type=Person)` checks the exact root
Python type. It does not enforce dataclass annotations or validate field values.
Annotations alone do not add runtime validation, and plain dictionaries are
not automatically turned into that class by the legacy mode.

Use the explicit typed-input mode when field validation is required:

```python
from dataclasses import dataclass
from typing import List
from jsonic import deserialize
from jsonic.exceptions import DeserializationError

@dataclass
class Person:
    age: int

people = deserialize([{'age': 30}], expected_type=List[Person],
                     validation='strict', safe=True)
assert people == [Person(30)]
try:
    deserialize([{'age': 'bad'}], expected_type=List[Person], validation='strict')
except DeserializationError as error:
    assert error.code == 'type_mismatch'
    assert error.path == '[0].age'
else:
    raise AssertionError('invalid field accepted')
```

## Supported contract

- Exact `str`, `bool`, `int`, `float`, `None` types, without coercion. In
  particular bool is not int and an integer is not silently converted to float.
- Parameterized lists, `Dict[str, T]`, sets and fixed/variable-length tuples.
  JSON arrays structure into tuples/sets; set duplicates follow set semantics.
  Existing exact legacy tuple/set envelopes are accepted for those schemas.
- `Optional`, `Union` (first successful alternative), and `Literal` with exact
  primitive identity. Module-resolvable forward references and recursive class
  schemas work through `get_type_hints`. Unresolvable local names fail clearly.
- Dataclasses and classes with annotated fields/constructor parameters,
  including registered/Serializable mappings. Required inputs are checked,
  omitted defaults/default factories remain constructor-owned, and typed
  non-constructor fields follow existing restoration/invariant rules.
- `Any` accepts JSON primitives/lists/string-key dictionaries as literal data;
  it does not dispatch type tags. Annotation metadata in `Dict[str, T]` is also
  ordinary dictionary data. Matching object tags are accepted only for a
  selected class schema; other tags are rejected without imports.

Unknown fields default to `unknown_fields='forbid'`; explicit `'ignore'` drops
unknown fields without decoding their contents. Private annotated fields are
part of the explicitly selected schema. Filtering options from ordinary object
decoding do not remove those schema fields. No extra-field preservation or
coercive mode is provided.

All provided values are validated before any schema constructor runs. Nested
objects are constructed once. Constructor defaults and user constructor/post-init
logic remain application responsibilities; their exceptions are preserved.
Frozen computed fields are checked without bypassing invariants. This mode
selects classes from caller-supplied schemas, never from input-directed imports
or custom codec/resolver hooks. `safe=True` propagates registry policy into
constructors' nested Jsonic calls, and an existing active safe policy cannot
be broadened. Schema constructors are trusted application code, not a sandbox.

Unsupported annotations (including bare collections, arbitrary generics,
TypedDict/protocol/Annotated schemas and Pydantic models), positional-only
constructors, required InitVars, and standard-library codec transformations
such as datetime/UUID inputs fail explicitly. Use native Pydantic validation
for its schemas, and normal Jsonic decoding for codec persistence. This is a
scoped structuring API, not universal Python typing validation.

Strict input works with plain JSON, matching legacy object payloads and
`wire_format='v2'`. `string_input=True` parses text first. Error metadata contains
paths and expected/actual types without embedding field values. Default
`validation=None` preserves previous root-only decoding, native Pydantic
validation and all existing wire contracts. This additive option addresses
issues #2/#14 without changing acceptance for existing callers.
