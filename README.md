# Jsonic

[![PyPI version](https://badge.fury.io/py/py-jsonic.svg)](https://badge.fury.io/py/py-jsonic)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-448%20passing-brightgreen.svg)](tests/)

**Jsonic** is a lightweight, Pythonic library for effortless JSON serialization and deserialization of Python objects. Built for modern Python with type hints, dataclasses, and developer experience in mind.

```python
from jsonic import serialize, deserialize
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    name: str
    email: str
    created_at: datetime

user = User("Alice", "alice@example.com", datetime.now())
json_data = serialize(user)  # Dict or JSON string
user_copy = deserialize(json_data, expected_type=User)  # Type-safe!
```

---

## ✨ Features

- 🎯 **Zero Configuration** - Works with dataclasses, type hints, and regular classes
- 🔒 **Type Safe** - Full type hint support with validation
- 🚀 **Modern Python** - Built for Python 3.8+ with dataclasses and type hints
- 📦 **Rich Types** - Supports tuples, sets, enums, datetime, `__slots__`, and more
- 🎨 **Flexible** - Custom serializers, transient fields, private attribute control
- 🔍 **Partial Serialization** - Include/exclude fields with nested dot notation
- 🤝 **Pydantic Integration** - Seamless support for Pydantic models and field aliases
- 🐛 **Great Errors** - Detailed error messages with exact path to the problem
- ⚡ **Fast** - Minimal overhead, optimized for performance
- 🧪 **Well Tested** - 448 tests with >95% coverage

---

## 📦 Installation

```bash
pip install py-jsonic
```

**Requirements:** Python 3.8+

---

## 🚀 Quick Start

### Basic Usage

```python
from jsonic import serialize, deserialize
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    in_stock: bool

# Serialize to dict
product = Product("Laptop", 999.99, True)
data = serialize(product)
# {'name': 'Laptop', 'price': 999.99, 'in_stock': True, '_serialized_type': 'Product'}

# Deserialize back to object
product_copy = deserialize(data, expected_type=Product)
assert product.name == product_copy.name
```

### With Nested Objects

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Address:
    street: str
    city: str

@dataclass
class User:
    name: str
    addresses: List[Address]

user = User("Bob", [Address("123 Main St", "NYC")])
data = serialize(user)
user_copy = deserialize(data, expected_type=User)
```

### JSON String Output

```python
json_string = serialize(user, string_output=True)
user_copy = deserialize(json_string, string_input=True, expected_type=User)
```

---

## 📚 Core Concepts

### Supported Types

Jsonic automatically handles:

- **Primitives**: `int`, `float`, `str`, `bool`, `None`
- **Collections**: `list`, `dict`, `tuple`, `set`
- **Standard Library**: `datetime`, `Enum`, `UUID`
- **Python Classes**: dataclasses, classes with type hints, `__slots__`
- **Custom Types**: Via `@jsonic_serializer` and `@jsonic_deserializer`

### Three Ways to Use Jsonic

#### 1. Dataclasses (Recommended)

```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class Person:
    name: str
    age: int

person = Person("Alice", 30)
data = serialize(person)
```

#### 2. Serializable Base Class

```python
from jsonic import Serializable
from datetime import datetime

class User(Serializable):
    def __init__(self, username: str, created_at: datetime):
        super().__init__()
        self.username = username
        self.created_at = created_at

user = User("alice", datetime.now())
data = serialize(user)
```

#### 3. Register External Classes

```python
from jsonic import register_jsonic_type

class ThirdPartyClass:
    def __init__(self, value: str):
        self.internal_value = value

# Register with parameter mapping
register_jsonic_type(
    ThirdPartyClass,
    init_parameters_mapping={'value': 'internal_value'}
)
```

---

## 🎯 Common Use Cases

### API Responses

```python
@dataclass
class APIResponse:
    status: str
    data: dict
    timestamp: datetime

response = APIResponse("success", {"user_id": 123}, datetime.now())
return serialize(response, string_output=True)
```

### Database Models

```python
@dataclass
class BlogPost:
    title: str
    content: str
    author: User
    tags: List[str]
    published_at: datetime

# Save to database
post_json = serialize(post, string_output=True)
db.save(post_json)

# Load from database
post_data = db.load()
post = deserialize(post_data, string_input=True, expected_type=BlogPost)
```

### Configuration Files

```python
@dataclass
class AppConfig:
    database_url: str
    api_keys: dict
    features: List[str]

# Load config
with open('config.json') as f:
    config = deserialize(json.load(f), expected_type=AppConfig)
```

### Microservices Communication

```python
@dataclass
class OrderEvent:
    order_id: str
    items: List[Product]
    total: float
    created_at: datetime

# Send event
event = OrderEvent("ORD-123", products, 299.99, datetime.now())
message_queue.publish(serialize(event, string_output=True))

# Receive event
data = message_queue.consume()
event = deserialize(data, string_input=True, expected_type=OrderEvent)
```

---

## 🔧 Advanced Features

### Partial Serialization

Control which fields to serialize with `include` and `exclude` parameters:

```python
@dataclass
class User:
    username: str
    email: str
    password_hash: str
    api_token: str

user = User("alice", "alice@example.com", "hash123", "token456")

# Exclude sensitive fields
safe_data = serialize(user, exclude={'password_hash', 'api_token'})
# Result: {'username': 'alice', 'email': 'alice@example.com', ...}

# Include only specific fields
public_data = serialize(user, include={'username', 'email'})
# Result: {'username': 'alice', 'email': 'alice@example.com', ...}
```

**Nested field filtering** with dot notation:

```python
@dataclass
class Credentials:
    username: str
    password: str

@dataclass
class Database:
    host: str
    credentials: Credentials

@dataclass
class Config:
    app_name: str
    database: Database

config = Config("MyApp", Database("localhost", Credentials("admin", "secret")))

# Exclude nested password field
safe_config = serialize(config, exclude={'database.credentials.password'})
# Password is excluded, but username remains

# Include only specific nested fields
public_config = serialize(config, include={'app_name', 'database.host'})
# Only app_name and database.host are included
```

**Filter fields in lists:**

```python
@dataclass
class Item:
    name: str
    price: float
    internal_cost: float

@dataclass
class Order:
    order_id: str
    items: List[Item]

order = Order("ORD-123", [Item("Widget", 10.0, 5.0)])

# Exclude internal_cost from all items
public_order = serialize(order, exclude={'items.internal_cost'})
```

### Transient Attributes

Exclude fields from serialization at the class level:

```python
class User(Serializable):
    transient_attributes = ['password_hash', '_cache']
    
    def __init__(self, username: str, password_hash: str):
        super().__init__()
        self.username = username
        self.password_hash = password_hash  # Won't be serialized
        self._cache = {}  # Won't be serialized
```

### Private Attributes

Control private attribute serialization:

```python
# Exclude private attributes (default)
data = serialize(obj, serialize_private_attributes=False)

# Include private attributes
data = serialize(obj, serialize_private_attributes=True)
```

### Custom Serializers

```python
from jsonic import jsonic_serializer, jsonic_deserializer
from decimal import Decimal

@jsonic_serializer(Decimal)
def serialize_decimal(obj: Decimal) -> dict:
    return {'value': str(obj), '_serialized_type': 'Decimal'}

@jsonic_deserializer('Decimal')
def deserialize_decimal(data: dict) -> Decimal:
    return Decimal(data['value'])
```

### Type Safety

```python
# Validates the deserialized type matches expected type
user = deserialize(data, expected_type=User)

# Raises error if type doesn't match
try:
    product = deserialize(user_data, expected_type=Product)
except TypeError as e:
    print(f"Type mismatch: {e}")
```

### Enums

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class Request:
    status: Status

request = Request(Status.APPROVED)
data = serialize(request)  # Handles enums automatically
```

### Tuples and Sets

```python
@dataclass
class Data:
    coordinates: tuple  # (x, y, z)
    unique_ids: set

data = Data((1.0, 2.0, 3.0), {1, 2, 3})
serialized = serialize(data)  # Preserves tuple and set types
restored = deserialize(serialized, expected_type=Data)
assert isinstance(restored.coordinates, tuple)
assert isinstance(restored.unique_ids, set)
```

### Pydantic Models

Jsonic seamlessly integrates with Pydantic models:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    email: str
    age: int = Field(ge=0, le=150)
    nickname: str = Field(alias="display_name")

# Serialize Pydantic models
user = User(name="Alice", email="alice@example.com", age=30, display_name="Ally")
data = serialize(user)  # Respects field aliases

# Deserialize to Pydantic models
user_copy = deserialize(data, expected_type=User)  # Full validation
```

**Pydantic features supported:**
- Auto-detection of Pydantic models
- Field aliases (`alias`, `validation_alias`, `serialization_alias`)
- Nested Pydantic models
- Pydantic validators run on deserialization

---

## 🐛 Error Handling

Jsonic provides detailed error messages with exact paths:

```python
@dataclass
class Address:
    street: str
    city: str

@dataclass  
class User:
    name: str
    address: Address

# Error shows exact location
try:
    data = {'name': 'Alice', 'address': {'street': 123}}  # Wrong type
    user = deserialize(data, expected_type=User)
except Exception as e:
    print(e)
    # DeserializationError: Type mismatch at path: obj.address.street
```

### Type Not Found Suggestions

```python
try:
    deserialize({'_serialized_type': 'Usr'})  # Typo
except TypeError as e:
    print(e)
    # Could not find type: Usr
    # Did you mean one of these?
    #   - User
    #   - UserProfile
```

---

## 📊 Comparison with Alternatives

| Feature | Jsonic | Pydantic | marshmallow | dataclasses-json |
|---------|--------|----------|-------------|------------------|
| Zero config for dataclasses | ✅ | ✅ | ❌ | ✅ |
| Type hints support | ✅ | ✅ | ⚠️ | ✅ |
| Pydantic integration | ✅ | N/A | ❌ | ❌ |
| Partial serialization | ✅ | ⚠️ | ⚠️ | ❌ |
| Nested field filtering | ✅ | ❌ | ❌ | ❌ |
| Validation | ⚠️ | ✅ | ✅ | ❌ |
| Tuples/Sets support | ✅ | ⚠️ | ❌ | ❌ |
| `__slots__` support | ✅ | ❌ | ❌ | ❌ |
| Custom serializers | ✅ | ✅ | ✅ | ⚠️ |
| Error messages with paths | ✅ | ✅ | ⚠️ | ❌ |
| Learning curve | Low | Medium | High | Low |
| Performance | Fast | Fast | Medium | Fast |

**When to use Jsonic:**
- You want simple, Pythonic serialization without schemas
- You're working with existing classes you can't modify
- You need `__slots__`, tuples, or sets support
- You want great error messages out of the box
- You need fine-grained control over serialization (include/exclude nested fields)
- You want to work with both dataclasses and Pydantic models

**When to use alternatives:**
- **Pydantic**: You need extensive validation and FastAPI integration (but Jsonic can serialize Pydantic models!)
- **marshmallow**: You need complex validation rules and transformations
- **dataclasses-json**: You only need basic dataclass serialization

---

## 🎓 Examples

See [EXAMPLES.md](EXAMPLES.md) for comprehensive examples including:
- Real-world API integration
- Database persistence patterns
- Microservices communication
- Configuration management
- Migration from other libraries

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Running tests
- Code style guidelines
- Pull request process

---

## 📝 Documentation

- **[Examples](EXAMPLES.md)** - Real-world usage examples
- **[API Reference](docs/)** - Detailed API documentation
- **[Roadmap](ROADMAP.md)** - Planned features and timeline
- **[Contributing](CONTRIBUTING.md)** - How to contribute

---

## 🐛 Known Limitations

Jsonic is designed for data classes and may not work with:

- **Classes with temporary constructor parameters** - Parameters not stored as attributes
- **Classes with positional-only parameters** - Can't reconstruct with keyword args
- **Classes with complex `*args`/`**kwargs`** - May not deserialize correctly
- **Classes with side effects in `__init__`** - May behave differently on deserialization

For these cases, consider using custom serializers or restructuring your classes.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Inspired by the Python community's need for simple, Pythonic serialization that "just works" with modern Python features.

---

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/jsonic/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/jsonic/discussions)
- **Email**: orrbenyamini@gmail.com

---

**Made with ❤️ for the Python community**
