# Jsonic

[![Tests and packages](https://github.com/OrrBin/Jsonic/actions/workflows/tests.yml/badge.svg)](https://github.com/OrrBin/Jsonic/actions/workflows/tests.yml)
[![PyPI](https://badge.fury.io/py/py-jsonic.svg)](https://pypi.org/project/py-jsonic/)

Serialize Python objects to JSON-compatible trees or text, and reconstruct them
with explicit policies for trust, types and persistence. Supports dataclasses,
annotated classes, mixed dictionary/slot storage, tuples, sets, enums, UUID,
datetime, custom codecs and optional Pydantic models.

This checkout is **2.0.0rc1, unpublished release candidate**. PyPI's published 1.0.1 does not
include the new options below. See [migration notes](MIGRATION.md) before upgrading.
The supported interpreter range is **Python 3.8–3.13**. Pydantic is optional:
v1 (>=1.10.13) and v2 are covered independently. Versions outside that Python
range require further qualification and are excluded by package metadata.

## Install and develop

Install the published package with `python -m pip install py-jsonic`. To use
this checkout, run `python -m pip install .`; add `[pydantic]` for optional model
support. For development, use an isolated environment and
`python -m pip install -r requirements-dev.txt`. There are no mandatory runtime
dependencies. [RELEASE.md](RELEASE.md) describes package checks and support policy.

## Basic persistence

```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class Person:
    name: str
    age: int

person = Person('Alice', 30)
wire = serialize(person, string_output=True)
restored = deserialize(wire, string_input=True, expected_type=Person, safe=True)
assert restored == person
```

`expected_type` normally checks exact root identity. Dataclass annotations alone
**do not validate fields**. For plain typed input, explicitly enable strict
validation, which validates before constructing schema objects and does not
coerce values:

```python
from dataclasses import dataclass
from typing import List
from jsonic import deserialize
from jsonic.exceptions import DeserializationError

@dataclass
class Person:
    age: int

assert deserialize([{'age': 30}], expected_type=List[Person],
                   validation='strict', safe=True) == [Person(30)]
try:
    deserialize({'age': 'bad'}, expected_type=Person, validation='strict')
except DeserializationError as error:
    assert error.path == 'age' and error.code == 'type_mismatch'
else:
    raise AssertionError('invalid field accepted')
```

See [validation modes](VALIDATION_MODES.md) for unions, containers, defaults,
unknown fields and the supported annotation subset. Native Pydantic validation
is separate from this mode.

## Trust and externally supplied data

For API requests, uploaded configuration and message queues, use `safe=True`.
Register trusted classes with `register_jsonic_type(MyClass)` or subclass
`Serializable`. An explicit concrete root `expected_type` authorizes that class;
nested tagged classes still need registration. Unknown tags are rejected before
reconstruction, including under Pydantic models and tuple/set adapters.
Strict typed input instead selects classes from the caller's explicit schema;
see its policy details in VALIDATION_MODES.md.

Registered constructors and codecs are trusted application code. Safe decoding
is not a sandbox and does not impose resource limits. The legacy default permits
payload-directed dynamic imports and must be restricted to trusted stored data.

## Literal dictionaries and wire compatibility

Default legacy output can confuse literal metadata-looking dictionary keys
with object tags. Use the explicit v2 writer **and reader** for new data that
needs collision-free dictionaries:

```python
from jsonic import serialize, deserialize
value = {'_serialized_type': 'literal', '_is_tuple': True, 'items': [1]}
wire = serialize(value, wire_format='v2')
assert deserialize(wire, wire_format='v2', safe=True) == value
```

[Wire format and migration](WIRE_FORMAT.md) explains versioned node kinds,
shape validation, custom codec responsibilities and old-reader limitations.
Legacy mode remains available for existing data; v2 output requires a new reader.

## Selection and attributes

```python
from jsonic import serialize
value = [{'name': 'Alice', 'password': 'secret'}]
assert serialize(value, exclude={'password'}) == [{'name': 'Alice'}]
```

Selection applies to every member of root and nested collections. Exclusion
wins at every nesting level, and built-in extraction skips excluded values
before traversal. Dots are path separators with no literal-dot escape syntax.
Private object attributes are excluded by default; literal dictionary keys are
user data. `Serializable.transient_attributes` and `init_parameters_mapping`
control persistence for registered classes. Custom callbacks own their internal
attribute access and mutation. Jsonic protects its input mappings but passes
nested values to custom decoders with shallow-copy identity semantics.

## Custom codecs

```python
from decimal import Decimal
from jsonic import serialize, deserialize, jsonic_serializer, jsonic_deserializer

@jsonic_serializer(Decimal, type_id='example:decimal:v1')
def encode_decimal(value):
    return {'value': str(value)}

@jsonic_deserializer(Decimal, type_id='example:decimal:v1')
def decode_decimal(data):
    return Decimal(data['value'])

assert deserialize(serialize(Decimal('1.25')), expected_type=Decimal,
                   safe=True) == Decimal('1.25')
```

Registration takes a Python type, not a string. Stable IDs are opt-in;
explicit aliases let new readers accept historical IDs. Collision registrations
are rejected. [Resolver documentation](RESOLVERS.md) covers public signatures,
recursive traversal and structured errors.

## Pydantic and UUID persistence

```python
from pydantic import BaseModel, Field
from jsonic import serialize, deserialize

class Invoice(BaseModel):
    amount: int = Field(alias='inputAmount')

value = Invoice(inputAmount=7)
wire = serialize(value, pydantic_mode='roundtrip')
assert deserialize(wire, expected_type=Invoice, safe=True) == value
```

Pydantic presentation output remains the default and follows native serializers
and aliases; arbitrary presentation output need not be reversible. Opt-in
field-state persistence supports documented unique string aliases and runs
normal validators on reading. Use `uuid_format='string'` for portable UUID
output. [Persistence policies](PERSISTENCE.md) describes frozen invariants,
required InitVar rejection and both new formats' reader requirements.

## Verification and contribution

CI runs the Python/dependency matrix, builds and inspects wheel/sdist packages,
tests an installed wheel outside the checkout, checks historical reader/writer
compatibility and executes the examples below. It never publishes a release.
Coverage is measured and uploaded per job, without a static percentage promise.

- [Testing guide and historical coverage audit](TESTING.md)
- [Runnable example scripts](examples/) and [integration recipes](EXAMPLES.md)
- [Contributing](CONTRIBUTING.md), [roadmap](ROADMAP.md), [release notes](CHANGELOG.md)
- [Report an issue](https://github.com/OrrBin/Jsonic/issues)

MIT license; see [LICENSE](LICENSE).
