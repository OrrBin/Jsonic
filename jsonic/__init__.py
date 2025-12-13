from .serializable import Serializable, register_jsonic_type, serialize, deserialize
from .decorators import jsonic_serializer, jsonic_deserializer
from .default_serializers import *

# Register type resolvers
from .type_resolver import register_resolver
from .resolvers import DataclassResolver, TypeHintedResolver

register_resolver(DataclassResolver())
register_resolver(TypeHintedResolver())

# Register tuple and set serializers
from . import tuple_serializer
from . import set_serializer
