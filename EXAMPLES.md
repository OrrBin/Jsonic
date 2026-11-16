# Jsonic Examples

Application integration recipes for common patterns. These snippets often require
caller-provided variables, external services or optional libraries; they are
illustrative, not end-to-end tested integrations. For executed examples and the
current API contracts, see README.md, examples/, VALIDATION_MODES.md and
WIRE_FORMAT.md. Annotations alone do not validate fields in normal decoding.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Pydantic Integration](#pydantic-integration)
- [Partial Serialization](#partial-serialization)
- [API Integration](#api-integration)
- [Database Persistence](#database-persistence)
- [Microservices](#microservices)
- [Configuration Management](#configuration-management)
- [Advanced Patterns](#advanced-patterns)
- [Migration Guides](#migration-guides)

---

## Basic Examples

### Simple Dataclass

```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class Person:
    name: str
    age: int
    email: str

# Create and serialize
person = Person("Alice", 30, "alice@example.com")
data = serialize(person)

# Deserialize
person_copy = deserialize(data, expected_type=Person)
assert person.name == person_copy.name
```

### Nested Objects

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Address:
    street: str
    city: str
    zip_code: str

@dataclass
class Company:
    name: str
    address: Address
    employees: List[str]

company = Company(
    "Tech Corp",
    Address("123 Main St", "San Francisco", "94105"),
    ["Alice", "Bob", "Charlie"]
)

# Serialize
data = serialize(company, string_output=True)

# Deserialize
company_copy = deserialize(data, string_input=True, expected_type=Company)
```

### Collections

```python
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

@dataclass
class DataContainer:
    items: List[str]
    metadata: Dict[str, int]
    unique_ids: Set[int]
    coordinates: Tuple[float, float, float]

container = DataContainer(
    items=["a", "b", "c"],
    metadata={"count": 3, "version": 1},
    unique_ids={1, 2, 3},
    coordinates=(1.0, 2.0, 3.0)
)

data = serialize(container)
restored = deserialize(data, expected_type=DataContainer)

# Types are preserved
assert isinstance(restored.unique_ids, set)
assert isinstance(restored.coordinates, tuple)
```

---

## Pydantic Integration

### Basic Pydantic Model

```python
from pydantic import BaseModel, Field
from jsonic import serialize, deserialize

class User(BaseModel):
    name: str
    email: str
    age: int = Field(ge=0, le=150)

# Serialize Pydantic model
user = User(name="Alice", email="alice@example.com", age=30)
data = serialize(user)

# Deserialize to Pydantic model (with validation)
user_copy = deserialize(data, expected_type=User)
```

### Field Aliases

```python
from pydantic import BaseModel, Field
from jsonic import serialize, deserialize

class APIUser(BaseModel):
    user_id: str = Field(alias="userId")
    full_name: str = Field(alias="fullName")
    email_address: str = Field(alias="emailAddress")

# Serialize with aliases
user = APIUser(userId="123", fullName="Alice Smith", emailAddress="alice@example.com")
data = serialize(user)
# Result: {'userId': '123', 'fullName': 'Alice Smith', 'emailAddress': 'alice@example.com', ...}

# Deserialize respects aliases
user_copy = deserialize(data, expected_type=APIUser)
```

### Nested Pydantic Models

```python
from pydantic import BaseModel
from typing import List
from jsonic import serialize, deserialize

class Address(BaseModel):
    street: str
    city: str
    country: str

class Company(BaseModel):
    name: str
    address: Address

class Employee(BaseModel):
    name: str
    email: str
    company: Company
    skills: List[str]

# Create nested structure
employee = Employee(
    name="Bob",
    email="bob@example.com",
    company=Company(
        name="Tech Corp",
        address=Address(
            street="123 Main St",
            city="San Francisco",
            country="USA"
        )
    ),
    skills=["Python", "JavaScript"]
)

# Serialize and deserialize
data = serialize(employee)
employee_copy = deserialize(data, expected_type=Employee)
```

### Pydantic Validators

```python
from pydantic import BaseModel, validator, Field
from jsonic import serialize, deserialize

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    discount: float = Field(ge=0, le=1)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('discount')
    def discount_valid(cls, v, values):
        if 'price' in values and v >= values['price']:
            raise ValueError('Discount cannot exceed price')
        return v

# Validators run during deserialization
data = {
    'name': '  Laptop  ',
    'price': 999.99,
    'discount': 0.1,
    '_serialized_type': 'Product'
}

product = deserialize(data, expected_type=Product)
assert product.name == "Laptop"  # Trimmed by validator
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from jsonic import serialize, deserialize

app = FastAPI()

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: str

# In-memory storage (serialized)
users_db = {}

@app.post("/users", response_model=UserResponse)
def create_user(user: CreateUserRequest):
    # Pydantic validates automatically
    user_id = str(len(users_db) + 1)
    
    # Store serialized version
    user_data = serialize(user)
    user_data['id'] = user_id
    user_data['created_at'] = '2025-12-21T10:00:00'
    users_db[user_id] = user_data
    
    # Return as Pydantic model
    return deserialize(user_data, expected_type=UserResponse)

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return deserialize(users_db[user_id], expected_type=UserResponse)
```

### Mixing Dataclasses and Pydantic

```python
from dataclasses import dataclass
from pydantic import BaseModel
from typing import List
from jsonic import serialize, deserialize

# Dataclass for internal use
@dataclass
class InternalMetadata:
    created_by: str
    version: int

# Pydantic for API
class APIProduct(BaseModel):
    name: str
    price: float

# Combined model
@dataclass
class Product:
    api_data: APIProduct
    metadata: InternalMetadata

# Works seamlessly
product = Product(
    api_data=APIProduct(name="Widget", price=19.99),
    metadata=InternalMetadata(created_by="admin", version=1)
)

data = serialize(product)
product_copy = deserialize(data, expected_type=Product)
```

### Pydantic Config Options

```python
from pydantic import BaseModel, ConfigDict
from jsonic import serialize, deserialize

class StrictUser(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        validate_assignment=True
    )
    
    name: str
    email: str

# Pydantic config is respected
user = StrictUser(name="  Alice  ", email="alice@example.com")
assert user.name == "Alice"  # Whitespace stripped

data = serialize(user)
user_copy = deserialize(data, expected_type=StrictUser)
```

### Optional Fields and Defaults

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from jsonic import serialize, deserialize

class UserProfile(BaseModel):
    username: str
    bio: Optional[str] = None
    age: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True

# Minimal data
user = UserProfile(username="alice")
data = serialize(user)

# Deserialize with defaults
user_copy = deserialize(data, expected_type=UserProfile)
assert user_copy.tags == []
assert user_copy.is_active == True
```

---

## Partial Serialization

### Exclude Sensitive Fields

```python
from dataclasses import dataclass
from jsonic import serialize

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    api_token: str
    credit_card: str

user = User(
    username="alice",
    email="alice@example.com",
    password_hash="hash123",
    api_token="token456",
    credit_card="1234-5678-9012-3456"
)

# Exclude sensitive fields for API response
safe_data = serialize(user, exclude={'password_hash', 'api_token', 'credit_card'})
# Result: {'username': 'alice', 'email': 'alice@example.com', ...}
```

### Include Only Specific Fields

```python
from dataclasses import dataclass
from jsonic import serialize

@dataclass
class Employee:
    id: str
    name: str
    email: str
    salary: float
    ssn: str
    performance_review: str

employee = Employee(
    id="EMP-123",
    name="Bob Smith",
    email="bob@company.com",
    salary=75000.0,
    ssn="123-45-6789",
    performance_review="Excellent work..."
)

# Public profile - only include safe fields
public_profile = serialize(employee, include={'id', 'name', 'email'})
# Result: {'id': 'EMP-123', 'name': 'Bob Smith', 'email': 'bob@company.com', ...}
```

### Nested Field Filtering

```python
from dataclasses import dataclass
from jsonic import serialize

@dataclass
class Credentials:
    username: str
    password: str
    api_key: str

@dataclass
class Database:
    host: str
    port: int
    credentials: Credentials

@dataclass
class Config:
    app_name: str
    version: str
    database: Database

config = Config(
    app_name="MyApp",
    version="1.0.0",
    database=Database(
        host="db.example.com",
        port=5432,
        credentials=Credentials(
            username="admin",
            password="secret123",
            api_key="key456"
        )
    )
)

# Exclude nested password and api_key
safe_config = serialize(config, exclude={'database.credentials.password', 'database.credentials.api_key'})
# Result: Config with username but no password/api_key
```

### Filter Fields in Lists

```python
from dataclasses import dataclass
from typing import List
from jsonic import serialize

@dataclass
class Product:
    name: str
    price: float
    cost: float  # Internal cost
    supplier: str  # Internal info

@dataclass
class Order:
    order_id: str
    customer: str
    items: List[Product]

order = Order(
    order_id="ORD-123",
    customer="Alice",
    items=[
        Product("Widget", 19.99, 10.00, "Supplier A"),
        Product("Gadget", 29.99, 15.00, "Supplier B")
    ]
)

# Exclude internal fields from all items
public_order = serialize(order, exclude={'items.cost', 'items.supplier'})
# Items only have name and price
```

### API Response Filtering

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from jsonic import serialize

@dataclass
class Comment:
    id: str
    text: str
    author: str
    author_email: str
    author_ip: str
    created_at: datetime

@dataclass
class BlogPost:
    id: str
    title: str
    content: str
    author: str
    author_email: str
    draft_notes: str
    comments: List[Comment]

post = BlogPost(
    id="POST-1",
    title="My Blog Post",
    content="Content here...",
    author="Alice",
    author_email="alice@example.com",
    draft_notes="Remember to add images",
    comments=[
        Comment(
            id="C1",
            text="Great post!",
            author="Bob",
            author_email="bob@example.com",
            author_ip="192.168.1.1",
            created_at=datetime.now()
        )
    ]
)

# Public API response - exclude all sensitive data
public_post = serialize(
    post,
    exclude={
        'author_email',
        'draft_notes',
        'comments.author_email',
        'comments.author_ip'
    }
)
```

### Dynamic Field Selection

```python
from dataclasses import dataclass
from typing import Set
from jsonic import serialize

@dataclass
class UserProfile:
    username: str
    email: str
    phone: str
    address: str
    bio: str
    preferences: dict

def serialize_for_role(user: UserProfile, role: str) -> dict:
    """Serialize user based on viewer's role"""
    
    if role == "admin":
        # Admins see everything
        return serialize(user)
    
    elif role == "friend":
        # Friends see most fields
        return serialize(user, exclude={'preferences'})
    
    elif role == "public":
        # Public sees minimal info
        return serialize(user, include={'username', 'bio'})
    
    else:
        return serialize(user, include={'username'})

user = UserProfile(
    username="alice",
    email="alice@example.com",
    phone="555-1234",
    address="123 Main St",
    bio="Software developer",
    preferences={"theme": "dark"}
)

admin_view = serialize_for_role(user, "admin")
friend_view = serialize_for_role(user, "friend")
public_view = serialize_for_role(user, "public")
```

### Logging Without Sensitive Data

```python
from dataclasses import dataclass
from datetime import datetime
from jsonic import serialize
import logging

@dataclass
class PaymentRequest:
    transaction_id: str
    amount: float
    currency: str
    card_number: str
    cvv: str
    timestamp: datetime

def process_payment(payment: PaymentRequest):
    # Log without sensitive data
    log_data = serialize(payment, exclude={'card_number', 'cvv'})
    logging.info(f"Processing payment: {log_data}")
    
    # Process with full data
    # ... payment processing logic ...

payment = PaymentRequest(
    transaction_id="TXN-123",
    amount=99.99,
    currency="USD",
    card_number="1234-5678-9012-3456",
    cvv="123",
    timestamp=datetime.now()
)

process_payment(payment)
```

---

## API Integration

### REST API Client

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import requests
from jsonic import serialize, deserialize

@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime

@dataclass
class APIResponse:
    success: bool
    data: Optional[User]
    error: Optional[str]

class UserAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_user(self, user_id: int) -> User:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        data = response.json()
        return deserialize(data, expected_type=User)
    
    def create_user(self, user: User) -> APIResponse:
        payload = serialize(user, string_output=True)
        response = requests.post(
            f"{self.base_url}/users",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        return deserialize(response.json(), expected_type=APIResponse)

# Usage
api = UserAPI("https://api.example.com")
user = api.get_user(123)
print(f"User: {user.username}")
```

### GraphQL Integration

```python
from dataclasses import dataclass
from typing import List
from jsonic import serialize, deserialize

@dataclass
class Post:
    id: str
    title: str
    content: str
    author: str

@dataclass
class GraphQLResponse:
    data: dict
    errors: List[dict] = None

def fetch_posts() -> List[Post]:
    query = """
    query {
        posts {
            id
            title
            content
            author
        }
    }
    """
    
    response = requests.post(
        "https://api.example.com/graphql",
        json={"query": query}
    )
    
    gql_response = deserialize(response.json(), expected_type=GraphQLResponse)
    
    # Convert to Post objects
    posts = [deserialize(post, expected_type=Post) 
             for post in gql_response.data['posts']]
    
    return posts
```

---

## Database Persistence

### SQLite with Jsonic

```python
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from jsonic import serialize, deserialize

@dataclass
class BlogPost:
    id: Optional[int]
    title: str
    content: str
    author: str
    created_at: datetime
    tags: List[str]

class BlogRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        """)
    
    def save(self, post: BlogPost) -> int:
        # Serialize to JSON string
        json_data = serialize(post, string_output=True)
        
        cursor = self.conn.execute(
            "INSERT INTO posts (data) VALUES (?)",
            (json_data,)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get(self, post_id: int) -> Optional[BlogPost]:
        cursor = self.conn.execute(
            "SELECT data FROM posts WHERE id = ?",
            (post_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return deserialize(row[0], string_input=True, expected_type=BlogPost)
        return None
    
    def get_all(self) -> List[BlogPost]:
        cursor = self.conn.execute("SELECT data FROM posts")
        return [
            deserialize(row[0], string_input=True, expected_type=BlogPost)
            for row in cursor.fetchall()
        ]

# Usage
repo = BlogRepository("blog.db")

post = BlogPost(
    id=None,
    title="Getting Started with Jsonic",
    content="Jsonic makes serialization easy...",
    author="Alice",
    created_at=datetime.now(),
    tags=["python", "serialization"]
)

post_id = repo.save(post)
loaded_post = repo.get(post_id)
```

### Redis Cache

```python
import redis
from dataclasses import dataclass
from typing import Optional
from jsonic import serialize, deserialize

@dataclass
class CachedUser:
    user_id: str
    username: str
    email: str
    preferences: dict

class UserCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def set(self, user: CachedUser, ttl: int = 3600):
        key = f"user:{user.user_id}"
        value = serialize(user, string_output=True)
        self.redis.setex(key, ttl, value)
    
    def get(self, user_id: str) -> Optional[CachedUser]:
        key = f"user:{user_id}"
        value = self.redis.get(key)
        
        if value:
            return deserialize(
                value.decode('utf-8'),
                string_input=True,
                expected_type=CachedUser
            )
        return None

# Usage
cache = UserCache("redis://localhost:6379")

user = CachedUser(
    user_id="123",
    username="alice",
    email="alice@example.com",
    preferences={"theme": "dark", "notifications": True}
)

cache.set(user, ttl=3600)
cached_user = cache.get("123")
```

---

## Microservices

### Message Queue (RabbitMQ)

```python
import pika
from dataclasses import dataclass
from datetime import datetime
from typing import List
from jsonic import serialize, deserialize

@dataclass
class OrderEvent:
    order_id: str
    customer_id: str
    items: List[dict]
    total: float
    created_at: datetime

class OrderPublisher:
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='orders')
    
    def publish_order(self, order: OrderEvent):
        message = serialize(order, string_output=True)
        self.channel.basic_publish(
            exchange='',
            routing_key='orders',
            body=message
        )

class OrderConsumer:
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='orders')
    
    def process_orders(self, callback):
        def on_message(ch, method, properties, body):
            order = deserialize(
                body.decode('utf-8'),
                string_input=True,
                expected_type=OrderEvent
            )
            callback(order)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        self.channel.basic_consume(
            queue='orders',
            on_message_callback=on_message
        )
        self.channel.start_consuming()

# Usage
publisher = OrderPublisher("amqp://localhost")
order = OrderEvent(
    order_id="ORD-123",
    customer_id="CUST-456",
    items=[{"product": "Laptop", "qty": 1}],
    total=999.99,
    created_at=datetime.now()
)
publisher.publish_order(order)

consumer = OrderConsumer("amqp://localhost")
consumer.process_orders(lambda order: print(f"Processing {order.order_id}"))
```

### gRPC Service

```python
from dataclasses import dataclass
from typing import List
from jsonic import serialize, deserialize

@dataclass
class Product:
    id: str
    name: str
    price: float
    in_stock: bool

@dataclass
class ProductRequest:
    product_ids: List[str]

@dataclass
class ProductResponse:
    products: List[Product]

class ProductService:
    def GetProducts(self, request_data: bytes) -> bytes:
        # Deserialize request
        request = deserialize(
            request_data.decode('utf-8'),
            string_input=True,
            expected_type=ProductRequest
        )
        
        # Fetch products (mock)
        products = [
            Product(id=pid, name=f"Product {pid}", price=99.99, in_stock=True)
            for pid in request.product_ids
        ]
        
        # Serialize response
        response = ProductResponse(products=products)
        return serialize(response, string_output=True).encode('utf-8')
```

---

## Configuration Management

### Application Config

```python
from dataclasses import dataclass
from typing import List, Dict
import json
from pathlib import Path
from jsonic import serialize, deserialize

@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str

@dataclass
class APIConfig:
    base_url: str
    timeout: int
    retry_attempts: int
    api_keys: Dict[str, str]

@dataclass
class AppConfig:
    environment: str
    debug: bool
    database: DatabaseConfig
    api: APIConfig
    features: List[str]

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
    
    def load(self) -> AppConfig:
        with open(self.config_path) as f:
            data = json.load(f)
        return deserialize(data, expected_type=AppConfig)
    
    def save(self, config: AppConfig):
        data = serialize(config)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

# Usage
config = AppConfig(
    environment="production",
    debug=False,
    database=DatabaseConfig(
        host="db.example.com",
        port=5432,
        username="app_user",
        password="secret",
        database="app_db"
    ),
    api=APIConfig(
        base_url="https://api.example.com",
        timeout=30,
        retry_attempts=3,
        api_keys={"service_a": "key1", "service_b": "key2"}
    ),
    features=["feature_a", "feature_b"]
)

manager = ConfigManager("config.json")
manager.save(config)
loaded_config = manager.load()
```

### Environment-Specific Configs

```python
from dataclasses import dataclass
from enum import Enum
from jsonic import serialize, deserialize

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class Config:
    environment: Environment
    database_url: str
    log_level: str
    cache_enabled: bool

def load_config(env: Environment) -> Config:
    configs = {
        Environment.DEVELOPMENT: Config(
            environment=Environment.DEVELOPMENT,
            database_url="sqlite:///dev.db",
            log_level="DEBUG",
            cache_enabled=False
        ),
        Environment.PRODUCTION: Config(
            environment=Environment.PRODUCTION,
            database_url="postgresql://prod-db:5432/app",
            log_level="WARNING",
            cache_enabled=True
        )
    }
    return configs[env]

# Usage
config = load_config(Environment.PRODUCTION)
config_json = serialize(config, string_output=True)
```

---

## Advanced Patterns

### Custom Serializers

```python
from decimal import Decimal
from jsonic import jsonic_serializer, jsonic_deserializer, serialize, deserialize

@jsonic_serializer(Decimal)
def serialize_decimal(obj: Decimal) -> dict:
    return {
        'value': str(obj),
        '_serialized_type': 'Decimal'
    }

@jsonic_deserializer('Decimal')
def deserialize_decimal(data: dict) -> Decimal:
    return Decimal(data['value'])

# Usage
from dataclasses import dataclass

@dataclass
class Invoice:
    amount: Decimal
    tax: Decimal

invoice = Invoice(Decimal("99.99"), Decimal("8.50"))
data = serialize(invoice)
restored = deserialize(data, expected_type=Invoice)
```

### Transient Attributes

```python
from jsonic import Serializable
from datetime import datetime

class Session(Serializable):
    transient_attributes = ['_cache', 'connection']
    
    def __init__(self, user_id: str, token: str):
        super().__init__()
        self.user_id = user_id
        self.token = token
        self.created_at = datetime.now()
        self._cache = {}  # Won't be serialized
        self.connection = None  # Won't be serialized

session = Session("user123", "token456")
data = serialize(session)
# Only user_id, token, and created_at are serialized
```

### Init Parameter Mapping

```python
from jsonic import register_jsonic_type

class LegacyUser:
    def __init__(self, uid: str, uname: str):
        self.user_id = uid  # Different name!
        self.username = uname  # Different name!

# Map constructor params to attributes
register_jsonic_type(
    LegacyUser,
    init_parameters_mapping={
        'uid': 'user_id',
        'uname': 'username'
    }
)

user = LegacyUser("123", "alice")
data = serialize(user)
restored = deserialize(data, expected_type=LegacyUser)
```

### Slots Support

```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class Point:
    __slots__ = ['x', 'y', 'z']
    x: float
    y: float
    z: float

point = Point(1.0, 2.0, 3.0)
data = serialize(point)
restored = deserialize(data, expected_type=Point)
```

---

## Migration Guides

### From Manual JSON Handling

**Before:**
```python
import json
from datetime import datetime

class User:
    def __init__(self, name: str, created_at: datetime):
        self.name = name
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            created_at=datetime.fromisoformat(data['created_at'])
        )

user = User("Alice", datetime.now())
json_str = json.dumps(user.to_dict())
loaded = User.from_dict(json.loads(json_str))
```

**After:**
```python
from dataclasses import dataclass
from datetime import datetime
from jsonic import serialize, deserialize

@dataclass
class User:
    name: str
    created_at: datetime

user = User("Alice", datetime.now())
json_str = serialize(user, string_output=True)
loaded = deserialize(json_str, string_input=True, expected_type=User)
```

### From dataclasses-json

**Before:**
```python
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class User:
    name: str
    age: int

user = User("Alice", 30)
json_str = user.to_json()
loaded = User.from_json(json_str)
```

**After:**
```python
from dataclasses import dataclass
from jsonic import serialize, deserialize

@dataclass
class User:
    name: str
    age: int

user = User("Alice", 30)
json_str = serialize(user, string_output=True)
loaded = deserialize(json_str, string_input=True, expected_type=User)
```

---

## Tips and Best Practices

### 1. Use Type Hints
```python
# Good
@dataclass
class User:
    name: str
    age: int

# Better - more specific
from typing import List, Optional

@dataclass
class User:
    name: str
    age: int
    emails: List[str]
    phone: Optional[str] = None
```

### 2. Prefer Dataclasses
```python
# Simpler and cleaner
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
```

### 3. Use expected_type for Safety
```python
# Type-safe deserialization
user = deserialize(data, expected_type=User)

# Catches type mismatches early
try:
    product = deserialize(user_data, expected_type=Product)
except TypeError:
    print("Wrong type!")
```

### 4. Handle Errors Gracefully
```python
from jsonic.exceptions import DeserializationError

try:
    user = deserialize(data, expected_type=User)
except DeserializationError as e:
    print(f"Failed at: {e.path}")
    print(f"Error: {e}")
```

---

For more examples, see the [tests](tests/) directory.
