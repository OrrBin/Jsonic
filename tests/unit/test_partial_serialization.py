"""
Tests for partial serialization (include/exclude parameters).
"""

from dataclasses import dataclass
from jsonic import serialize, deserialize, Serializable


class TestIncludeParameter:
    """Test the include parameter for partial serialization."""
    
    def test_include_specific_fields(self):
        """Test including only specific fields."""
        @dataclass
        class User:
            name: str
            email: str
            password: str
        
        user = User("Alice", "alice@example.com", "secret123")
        data = serialize(user, include={'name', 'email'})
        
        assert 'name' in data
        assert 'email' in data
        assert 'password' not in data
        assert '_serialized_type' in data  # Always included
    
    def test_include_with_list(self):
        """Test include parameter with list instead of set."""
        @dataclass
        class Product:
            name: str
            price: float
            internal_id: str
        
        product = Product("Laptop", 999.99, "INTERNAL-123")
        data = serialize(product, include=['name', 'price'])
        
        assert 'name' in data
        assert 'price' in data
        assert 'internal_id' not in data
    
    def test_include_single_field(self):
        """Test including only one field."""
        @dataclass
        class Config:
            api_key: str
            debug: bool
            timeout: int
        
        config = Config("key123", True, 30)
        data = serialize(config, include={'api_key'})
        
        assert 'api_key' in data
        assert 'debug' not in data
        assert 'timeout' not in data


class TestExcludeParameter:
    """Test the exclude parameter for partial serialization."""
    
    def test_exclude_specific_fields(self):
        """Test excluding specific fields."""
        @dataclass
        class User:
            name: str
            email: str
            password: str
        
        user = User("Bob", "bob@example.com", "secret456")
        data = serialize(user, exclude={'password'})
        
        assert 'name' in data
        assert 'email' in data
        assert 'password' not in data
    
    def test_exclude_multiple_fields(self):
        """Test excluding multiple fields."""
        @dataclass
        class Product:
            name: str
            price: float
            cost: float
            internal_id: str
        
        product = Product("Mouse", 29.99, 10.00, "INT-456")
        data = serialize(product, exclude={'cost', 'internal_id'})
        
        assert 'name' in data
        assert 'price' in data
        assert 'cost' not in data
        assert 'internal_id' not in data
    
    def test_exclude_with_list(self):
        """Test exclude parameter with list."""
        @dataclass
        class Config:
            api_key: str
            secret_key: str
            public_key: str
        
        config = Config("api123", "secret456", "public789")
        data = serialize(config, exclude=['api_key', 'secret_key'])
        
        assert 'public_key' in data
        assert 'api_key' not in data
        assert 'secret_key' not in data


class TestIncludeExcludePrecedence:
    """Test behavior when both include and exclude are provided."""
    
    def test_include_takes_precedence(self):
        """Test that include takes precedence over exclude."""
        @dataclass
        class User:
            name: str
            email: str
            password: str
        
        user = User("Charlie", "charlie@example.com", "secret789")
        # Include takes precedence
        data = serialize(user, include={'name'}, exclude={'email'})
        
        assert 'name' in data
        assert 'email' not in data  # Excluded because not in include
        assert 'password' not in data


class TestPartialSerializationWithSerializable:
    """Test partial serialization with Serializable base class."""
    
    def test_serializable_with_include(self):
        """Test include with Serializable class."""
        class User(Serializable):
            def __init__(self, name: str, email: str, password: str):
                super().__init__()
                self.name = name
                self.email = email
                self.password = password
        
        user = User("Dave", "dave@example.com", "secret")
        data = serialize(user, include={'name', 'email'})
        
        assert 'name' in data
        assert 'email' in data
        assert 'password' not in data
    
    def test_serializable_with_exclude(self):
        """Test exclude with Serializable class."""
        class Product(Serializable):
            def __init__(self, name: str, price: float, cost: float):
                super().__init__()
                self.name = name
                self.price = price
                self.cost = cost
        
        product = Product("Keyboard", 79.99, 30.00)
        data = serialize(product, exclude={'cost'})
        
        assert 'name' in data
        assert 'price' in data
        assert 'cost' not in data


class TestPartialSerializationEdgeCases:
    """Test edge cases for partial serialization."""
    
    def test_include_empty_set(self):
        """Test with empty include set."""
        @dataclass
        class User:
            name: str
            email: str
        
        user = User("Eve", "eve@example.com")
        data = serialize(user, include=set())
        
        # Only _serialized_type should be present
        assert '_serialized_type' in data
        assert 'name' not in data
        assert 'email' not in data
    
    def test_exclude_all_fields(self):
        """Test excluding all fields."""
        @dataclass
        class User:
            name: str
            email: str
        
        user = User("Frank", "frank@example.com")
        data = serialize(user, exclude={'name', 'email'})
        
        # Only _serialized_type should be present
        assert '_serialized_type' in data
        assert 'name' not in data
        assert 'email' not in data
    
    def test_include_nonexistent_field(self):
        """Test including a field that doesn't exist."""
        @dataclass
        class User:
            name: str
        
        user = User("Grace")
        data = serialize(user, include={'name', 'nonexistent'})
        
        # Should only include existing fields
        assert 'name' in data
        assert 'nonexistent' not in data
    
    def test_exclude_nonexistent_field(self):
        """Test excluding a field that doesn't exist."""
        @dataclass
        class User:
            name: str
            email: str
        
        user = User("Henry", "henry@example.com")
        data = serialize(user, exclude={'nonexistent'})
        
        # Should include all actual fields
        assert 'name' in data
        assert 'email' in data


class TestPartialSerializationWithStringOutput:
    """Test partial serialization with string output."""
    
    def test_include_with_string_output(self):
        """Test include parameter with JSON string output."""
        @dataclass
        class User:
            name: str
            email: str
            password: str
        
        user = User("Ivy", "ivy@example.com", "secret")
        json_str = serialize(user, include={'name', 'email'}, string_output=True)
        
        assert '"name"' in json_str
        assert '"email"' in json_str
        assert '"password"' not in json_str
    
    def test_exclude_with_string_output(self):
        """Test exclude parameter with JSON string output."""
        @dataclass
        class Product:
            name: str
            price: float
            cost: float
        
        product = Product("Monitor", 299.99, 150.00)
        json_str = serialize(product, exclude={'cost'}, string_output=True)
        
        assert '"name"' in json_str
        assert '"price"' in json_str
        assert '"cost"' not in json_str


class TestPartialSerializationRoundtrip:
    """Test that partial serialization doesn't break deserialization."""
    
    def test_deserialize_after_include(self):
        """Test deserializing after partial serialization with include."""
        @dataclass
        class User:
            name: str
            email: str
            password: str = "default"
        
        user = User("Jack", "jack@example.com", "secret")
        data = serialize(user, include={'name', 'email'})
        
        # Deserialization should work with default value for missing field
        restored = deserialize(data, expected_type=User)
        assert restored.name == "Jack"
        assert restored.email == "jack@example.com"
        assert restored.password == "default"  # Uses default
    
    def test_deserialize_after_exclude(self):
        """Test deserializing after partial serialization with exclude."""
        @dataclass
        class Product:
            name: str
            price: float
            stock: int = 0
        
        product = Product("Headphones", 149.99, 50)
        data = serialize(product, exclude={'stock'})
        
        # Deserialization should work with default value
        restored = deserialize(data, expected_type=Product)
        assert restored.name == "Headphones"
        assert restored.price == 149.99
        assert restored.stock == 0  # Uses default


class TestNestedFieldFiltering:
    """Test nested field filtering with dot notation."""
    
    def test_exclude_nested_field(self):
        """Test excluding a nested field using dot notation."""
        @dataclass
        class Address:
            street: str
            city: str
            internal_id: str
        
        @dataclass
        class User:
            name: str
            address: Address
        
        user = User("Alice", Address("123 Main St", "NYC", "ADDR-001"))
        data = serialize(user, exclude={'address.internal_id'})
        
        assert 'name' in data
        assert 'address' in data
        assert 'street' in data['address']
        assert 'city' in data['address']
        assert 'internal_id' not in data['address']
    
    def test_include_nested_field(self):
        """Test including only specific nested fields."""
        @dataclass
        class Profile:
            bio: str
            website: str
            ssn: str
        
        @dataclass
        class User:
            username: str
            profile: Profile
        
        user = User("alice", Profile("Developer", "example.com", "123-45-6789"))
        data = serialize(user, include={'username', 'profile.bio', 'profile.website'})
        
        assert 'username' in data
        assert 'profile' in data
        assert 'bio' in data['profile']
        assert 'website' in data['profile']
        assert 'ssn' not in data['profile']
    
    def test_multiple_nested_excludes(self):
        """Test excluding multiple nested fields."""
        @dataclass
        class Contact:
            email: str
            phone: str
            internal_notes: str
        
        @dataclass
        class Company:
            name: str
            contact: Contact
            revenue: float
        
        company = Company("ACME", Contact("info@acme.com", "555-1234", "VIP client"), 1000000)
        data = serialize(company, exclude={'contact.internal_notes', 'revenue'})
        
        assert 'name' in data
        assert 'contact' in data
        assert 'email' in data['contact']
        assert 'phone' in data['contact']
        assert 'internal_notes' not in data['contact']
        assert 'revenue' not in data
    
    def test_nested_field_in_list(self):
        """Test filtering nested fields within lists."""
        @dataclass
        class Item:
            name: str
            price: float
            cost: float
        
        @dataclass
        class Order:
            order_id: str
            items: list
        
        order = Order("ORD-123", [
            Item("Widget", 10.0, 5.0),
            Item("Gadget", 20.0, 12.0)
        ])
        data = serialize(order, exclude={'items.cost'})
        
        assert 'order_id' in data
        assert 'items' in data
        assert len(data['items']) == 2
        assert 'name' in data['items'][0]
        assert 'price' in data['items'][0]
        assert 'cost' not in data['items'][0]
        assert 'cost' not in data['items'][1]
    
    def test_deeply_nested_filtering(self):
        """Test filtering deeply nested structures."""
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
        data = serialize(config, exclude={'database.credentials.password'})
        
        assert 'app_name' in data
        assert 'database' in data
        assert 'host' in data['database']
        assert 'credentials' in data['database']
        assert 'username' in data['database']['credentials']
        assert 'password' not in data['database']['credentials']
    
    def test_nested_include_with_top_level_exclude(self):
        """Test combining nested include with top-level filtering."""
        @dataclass
        class Settings:
            theme: str
            language: str
            api_key: str
        
        @dataclass
        class User:
            name: str
            email: str
            password: str
            settings: Settings
        
        user = User("Alice", "alice@example.com", "secret", 
                   Settings("dark", "en", "key123"))
        data = serialize(user, include={'name', 'settings.theme', 'settings.language'})
        
        assert 'name' in data
        assert 'email' not in data
        assert 'password' not in data
        assert 'settings' in data
        assert 'theme' in data['settings']
        assert 'language' in data['settings']
        assert 'api_key' not in data['settings']
    
    def test_nested_filtering_preserves_serialized_type(self):
        """Test that nested filtering preserves _serialized_type markers."""
        @dataclass
        class Inner:
            value: str
            secret: str
        
        @dataclass
        class Outer:
            name: str
            inner: Inner
        
        obj = Outer("test", Inner("public", "private"))
        data = serialize(obj, exclude={'inner.secret'})
        
        assert '_serialized_type' in data
        assert 'Outer' in data['_serialized_type']
        assert '_serialized_type' in data['inner']
        assert 'Inner' in data['inner']['_serialized_type']
    
    def test_empty_nested_result(self):
        """Test when nested filtering results in empty nested object."""
        @dataclass
        class Metadata:
            internal_id: str
            internal_timestamp: str
        
        @dataclass
        class Document:
            title: str
            metadata: Metadata
        
        doc = Document("Report", Metadata("ID-001", "2025-01-01"))
        data = serialize(doc, exclude={'metadata.internal_id', 'metadata.internal_timestamp'})
        
        assert 'title' in data
        assert 'metadata' in data
        # Metadata should only have _serialized_type
        assert '_serialized_type' in data['metadata']
        assert len([k for k in data['metadata'].keys() if k != '_serialized_type']) == 0



class TestTransientWithPartialSerialization:
    """Test interaction between transient attributes and partial serialization."""
    
    def test_transient_with_exclude(self):
        """Test that transient and exclude work together."""
        class User(Serializable):
            transient_attributes = ['password_hash']
            
            def __init__(self, username, email, password_hash, api_token):
                super().__init__()
                self.username = username
                self.email = email
                self.password_hash = password_hash
                self.api_token = api_token
        
        user = User('alice', 'alice@example.com', 'hash123', 'token456')
        data = serialize(user, exclude={'api_token'})
        
        assert 'username' in data
        assert 'email' in data
        assert 'password_hash' not in data  # Transient
        assert 'api_token' not in data  # Excluded
    
    def test_transient_with_include(self):
        """Test that transient takes precedence over include."""
        class User(Serializable):
            transient_attributes = ['password_hash']
            
            def __init__(self, username, password_hash):
                super().__init__()
                self.username = username
                self.password_hash = password_hash
        
        user = User('alice', 'hash123')
        # Try to include transient field - should still be excluded
        data = serialize(user, include={'username', 'password_hash'})
        
        assert 'username' in data
        assert 'password_hash' not in data  # Transient wins
    
    def test_nested_transient_with_exclude(self):
        """Test transient in nested objects with partial serialization."""
        class Credentials(Serializable):
            transient_attributes = ['password']
            
            def __init__(self, username, password, api_key):
                super().__init__()
                self.username = username
                self.password = password
                self.api_key = api_key
        
        @dataclass
        class Config:
            app_name: str
            credentials: Credentials
        
        config = Config('MyApp', Credentials('admin', 'secret', 'key123'))
        data = serialize(config, exclude={'credentials.api_key'})
        
        assert 'credentials' in data
        assert 'username' in data['credentials']
        assert 'password' not in data['credentials']  # Transient
        assert 'api_key' not in data['credentials']  # Excluded


class TestPartialSerializationWithCollections:
    """Test partial serialization with sets and tuples."""
    
    def test_exclude_field_in_set_items(self):
        """Test filtering fields in set of objects."""
        @dataclass(frozen=True)  # Hashable for set
        class Item:
            name: str
            price: float
            internal_id: str
        
        @dataclass
        class Container:
            items: set
        
        container = Container({
            Item('A', 10.0, 'ID-1'),
            Item('B', 20.0, 'ID-2')
        })
        data = serialize(container, exclude={'items.internal_id'})
        
        assert 'items' in data
        assert data['items']['_is_set'] is True
        for item in data['items']['items']:
            assert 'name' in item
            assert 'price' in item
            assert 'internal_id' not in item
    
    def test_exclude_field_in_tuple_items(self):
        """Test filtering fields in tuple of objects."""
        @dataclass
        class Item:
            name: str
            price: float
            internal_id: str
        
        @dataclass
        class Container:
            items: tuple
        
        container = Container((
            Item('A', 10.0, 'ID-1'),
            Item('B', 20.0, 'ID-2')
        ))
        data = serialize(container, exclude={'items.internal_id'})
        
        assert 'items' in data
        assert data['items']['_is_tuple'] is True
        for item in data['items']['items']:
            assert 'name' in item
            assert 'price' in item
            assert 'internal_id' not in item
    
    def test_include_field_in_set_items(self):
        """Test including only specific fields in set items."""
        @dataclass(frozen=True)
        class Item:
            name: str
            price: float
            internal_id: str
        
        @dataclass
        class Container:
            items: set
        
        container = Container({
            Item('A', 10.0, 'ID-1'),
            Item('B', 20.0, 'ID-2')
        })
        data = serialize(container, include={'items.name', 'items.price'})
        
        assert 'items' in data
        assert data['items']['_is_set'] is True
        for item in data['items']['items']:
            assert 'name' in item
            assert 'price' in item
            assert 'internal_id' not in item


        """Test filtering fields in list (already covered but explicit)."""
        @dataclass
        class Item:
            name: str
            price: float
            internal_id: str
        
        @dataclass
        class Container:
            items: list
        
        container = Container([
            Item('A', 10.0, 'ID-1'),
            Item('B', 20.0, 'ID-2')
        ])
        data = serialize(container, exclude={'items.internal_id'})
        
        assert 'items' in data
        assert 'internal_id' not in data['items'][0]
        assert 'internal_id' not in data['items'][1]
    
    def test_tuple_with_nested_filtering(self):
        """Test that tuples are serialized before filtering is applied."""
        @dataclass
        class Item:
            name: str
            secret: str
        
        @dataclass
        class Container:
            data: tuple
        
        container = Container((Item('A', 'S1'), Item('B', 'S2')))
        # Tuples become dicts with _is_tuple marker, then filtering applies
        data = serialize(container)
        
        # Verify tuple structure is preserved
        assert 'data' in data
        assert isinstance(data['data'], dict)
        assert data['data'].get('_is_tuple') is True
    
    def test_set_with_primitives_and_filtering(self):
        """Test filtering with sets of primitives."""
        @dataclass
        class Container:
            tags: set
            metadata: dict
        
        container = Container({1, 2, 3}, {'key': 'value', 'secret': 'hidden'})
        data = serialize(container, exclude={'metadata.secret'})
        
        assert 'tags' in data
        assert data['tags']['_is_set'] is True
        assert 'secret' not in data['metadata']
    
    def test_nested_list_in_list_filtering(self):
        """Test filtering nested lists."""
        @dataclass
        class SubItem:
            value: str
            secret: str
        
        @dataclass
        class Item:
            name: str
            sub_items: list
        
        @dataclass
        class Container:
            items: list
        
        container = Container([
            Item('A', [SubItem('v1', 's1'), SubItem('v2', 's2')]),
            Item('B', [SubItem('v3', 's3')])
        ])
        data = serialize(container, exclude={'items.sub_items.secret'})
        
        assert len(data['items']) == 2
        assert 'secret' not in data['items'][0]['sub_items'][0]
        assert 'secret' not in data['items'][0]['sub_items'][1]
        assert 'secret' not in data['items'][1]['sub_items'][0]
    
    def test_list_and_dict_mixed_filtering(self):
        """Test filtering with list and dict structures."""
        @dataclass
        class Data:
            value: str
            internal: str
        
        @dataclass
        class Container:
            list_data: list
            metadata: dict
        
        container = Container(
            [Data('L1', 'I1'), Data('L2', 'I2')],
            {'key': 'value', 'secret': 'hidden'}
        )
        data = serialize(container, exclude={'list_data.internal', 'metadata.secret'})
        
        # Check list items are filtered
        for item in data['list_data']:
            assert 'value' in item
            assert 'internal' not in item
        
        # Check dict top-level keys are filtered
        assert 'key' in data['metadata']
        assert 'secret' not in data['metadata']
