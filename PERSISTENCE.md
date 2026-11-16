# Constructor and Pydantic persistence policies

## Constructor defaults and frozen dataclasses

Generic/Serializable and type-hinted reconstruction use the same missing-field
and default rules. Omitted optional arguments use Python defaults, including
mapped parameters and transient defaults. Missing unmapped required fields
raise DeserializationError with field/path metadata. A missing required mapped
attribute retains the historical KeyError. Positional-only constructors remain
unsupported by the keyword-binding path.

Frozen dataclasses are constructed normally. Their stored non-init fields must
equal the values recomputed/defaulted by construction; mismatches fail with
`code='immutable_field_mismatch'`. The decoder does not overwrite frozen state
with `object.__setattr__`. Mutable non-init fields retain legacy restoration.

A required InitVar is an input that a dataclass need not retain. Jsonic cannot
recover a discarded input from arbitrary derived fields. Such classes now fail
clearly at serialization and decoding with `code='unsupported_initvar'`; use an
explicit custom codec if the application retains enough information to recreate
the inputs. Defaulted InitVars can use their defaults. Frozen-field validation
still detects a stored result inconsistent with that reconstruction.

This earlier rejection changes previously successful one-way serialization of
required-InitVar shapes, whose round trips already failed. Assess migration and
release classification before publishing if clients relied on that behavior.

Cycles are rejected by object identity on the active ancestor path. A callback
should serialize its child fields or a separate value tree rather than reenter
the serializer on the same ancestor object in the same thread. Shared objects
in separate branches remain valid; the format does not preserve graph identity.

## UUID formats

The default UUID writer retains the legacy int/is_safe representation. The new
reader accepts it, including data produced by the historical implementation.
Safety enum metadata is decoded by explicit standard-library codecs rather
than input-directed module imports.
Standard codecs use qualified IDs, leaving application short names such as
UUID and SafeUUID available for their own codecs.

```python
from uuid import UUID
from jsonic import serialize, deserialize

value = UUID(int=7)
wire = serialize(value, uuid_format='string')
assert wire == {
    'uuid': '00000000-0000-0000-0000-000000000007',
    '_serialized_type': 'uuid.UUID',
}
assert deserialize(wire, expected_type=UUID, safe=True) == value
```

`uuid_format='string'` is opt-in and propagates through nested containers and
adapters. It preserves the identifier, omitting process-local is_safe metadata;
the read value uses SafeUUID.unknown. Existing readers are not promised to read
this opted-in representation. Other standard-library codecs are separate work.

## Pydantic presentation and field-state persistence

The default `pydantic_mode='presentation'` retains existing aliases and native
Pydantic dump/serializer behavior. Presentation output can be intentionally
lossy or use output aliases that validation does not accept. It is not promised
reversible for arbitrary models.

```python
from pydantic import BaseModel, Field
from jsonic import serialize, deserialize

class Invoice(BaseModel):
    amount: int = Field(alias='inputAmount')

value = Invoice(inputAmount=7)
wire = serialize(value, pydantic_mode='roundtrip')
assert wire['amount'] == 7
assert wire['_serialized_type'].startswith('jsonic:pydantic:fields-v1:')
assert deserialize(wire, expected_type=Invoice, safe=True) == value
```

The opt-in format stores canonical declared field names and a versioned type
tag. It reads raw fields, retaining nested model tags and Python container
types, and bypasses presentation serializers/computed output. On read, canonical
names map to supported validation aliases before ordinary Pydantic validation.
String input aliases may differ from string output aliases (Pydantic v2), so
asymmetric string aliases are reversible in this mode.

Supported model configurations have unique string validation aliases. Alias
choices/paths, root models, ambiguous aliases and extra stored attributes are
explicitly rejected. Presentation mode remains available for those APIs. New
format tags are rejected if they collide with a registered custom codec ID.
The format does not add a reserved field key to model data.

Selection uses canonical names in field-state mode, for example
`exclude={'children.secret'}`. Removing a required field can still make a
payload invalid to reconstruct, just as with ordinary partial serialization.
Private model attributes and computed output are not persisted declared fields.

Normal validators and constraints always run; non-idempotent or lossy custom
validation is not automatically invertible. Use a custom codec for such models
or for unsupported alias/extra/root configurations. The mode is a reversible
mapping for the stated subset, not a bypass of model invariants.
Input-only wrappers also need a custom codec if their parsed field value is not
accepted again as validation input. Pydantic v1's
own equality/dict dump may fail on sets of models even though field-state
persistence works; tests compare the actual field values and types directly.

Safe mode still requires authorization of every nested model. An explicit
root expected_type authorizes that root class; register nested classes with
register_jsonic_type as needed. The format does not authorize an arbitrary
type merely by prepending a format prefix.

## Compatibility

Both new output formats are opt-in and require a reader that understands them.
Existing UUID and Pydantic writer defaults are unchanged. Default/frozen repairs
are bug fixes; new options are additive functionality. Required-InitVar earlier
rejection and any error-contract changes need release/migration review. No
package version change or publication is part of these changes.
