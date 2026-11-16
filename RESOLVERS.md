# Resolver compatibility and traversal context

A resolver selects a Python class, returns an object-field mapping during
serialization, and constructs the class from a decoded mapping during
deserialization. Higher priority wins; equal priorities retain registration
order. Serializable/registered types and custom codecs keep their existing
priority over resolver selection.

Both historical serializer signatures remain supported:

```python
def serialize(self, obj): ...
def serialize(self, obj, serialize_private_attributes): ...
```

New implementations can opt into an immutable context by declaring `context`:

```python
from jsonic import TraversalContext, serialize, deserialize
from jsonic.type_resolver import TypeResolver, register_resolver

class Box:
    def __init__(self, value):
        self.value = value

class BoxResolver(TypeResolver):
    def can_resolve(self, cls):
        return cls is Box

    def priority(self):
        return 100

    def serialize(self, obj, *, context: TraversalContext):
        return {'value': context.serialize(obj.value, 'value')}

    def deserialize(self, data, cls, *, context: TraversalContext):
        # Children have already been decoded; do not decode them again.
        return cls(data['value'])

register_resolver(BoxResolver())
wire = serialize(Box([(1, 2)]))
restored = deserialize(wire, expected_type=Box, safe=True)
assert restored.value == [(1, 2)]
```

`context.path` identifies the current parent. `child_path('field')` appends a
field and `child_path(0)` appends a collection index. Child helpers preserve
private-field options, current selection and the active authorization policy.
For an excluded field, `context.serialize` avoids traversal and returns a None
placeholder; dispatcher output filtering removes that field. The callback
still owns attribute access performed before invoking the helper.

Context is scoped to an active call. Its child methods rely on the active
call's selection and safety policy; it is not a standalone codec to retain
and reuse after the callback. Public `serialize()` inside a resolver begins
a new selection root; use the context child helper for inherited traversal.

Legacy `(obj, private_flag, *, context=None)` serializers also work. Decoder
signatures remain `(data, cls)` with optional keyword-only `context`. Methods
with inspectable signatures receive protocol adaptation. Opaque/C-backed
callables retain their historical two-argument invocation. The dispatcher
never retries a callback that raises TypeError internally.
Return a mapping suitable for the existing wire format and an instance of
the selected class; arbitrary transforms are not automatically reversible.

Jsonic SerializationError/DeserializationError retain their TypeError and
AttributeError catch compatibility. They expose `path`, `code`, `field`,
`expected_type` and `actual_type` where available, and wrappers chain original
causes. Specialized exception subclasses, native ValueError (including
Pydantic ValidationError), KeyError and application RuntimeError keep their
existing classes. Their native details are not rewritten. Error text supplied
by user callbacks may contain values the callback chooses to include.
