"""Unit tests for register_jsonic_type() function"""
import pytest
from jsonic import serialize, deserialize, register_jsonic_type, Serializable


@pytest.mark.unit
class TestRegisterExternalClass:
    """Test registering external classes"""
    
    def test_register_simple_external_class(self, external_class):
        """External class should work after registration"""
        register_jsonic_type(external_class)
        
        user = external_class("Alice", "alice@example.com")
        serialized = serialize(user)
        result = deserialize(serialized)
        
        assert result == user
        assert result.name == "Alice"
        assert result.email == "alice@example.com"
    
    def test_register_with_transient_attributes(self, external_class):
        """Transient attributes should be excluded"""
        class UserWithCache:
            def __init__(self, name: str):
                self.name = name
                self.cache = "should not serialize"
            
            def __eq__(self, other):
                return isinstance(other, UserWithCache) and self.name == other.name
        
        register_jsonic_type(UserWithCache, transient_attributes=['cache'])
        
        user = UserWithCache("Alice")
        serialized = serialize(user)
        
        assert 'name' in serialized
        assert 'cache' not in serialized
        
        result = deserialize(serialized)
        assert result.name == "Alice"
    
    def test_register_with_init_mapping(self):
        """Init parameter mapping should work"""
        class User:
            def __init__(self, user_id: int, user_name: str):
                self.id = user_id
                self.name = user_name
            
            def __eq__(self, other):
                return isinstance(other, User) and self.id == other.id and self.name == other.name
        
        register_jsonic_type(
            User,
            init_parameters_mapping={'user_id': 'id', 'user_name': 'name'}
        )
        
        user = User(user_id=123, user_name="Alice")
        result = deserialize(serialize(user))
        
        assert result == user
        assert result.id == 123
        assert result.name == "Alice"
    
    def test_register_with_both_transient_and_mapping(self):
        """Both transient and mapping should work together"""
        class User:
            def __init__(self, user_id: int):
                self.id = user_id
                self.cache = "temp"
            
            def __eq__(self, other):
                return isinstance(other, User) and self.id == other.id
        
        register_jsonic_type(
            User,
            transient_attributes=['cache'],
            init_parameters_mapping={'user_id': 'id'}
        )
        
        user = User(user_id=123)
        serialized = serialize(user)
        
        assert 'cache' not in serialized
        assert 'id' in serialized
        
        result = deserialize(serialized)
        assert result.id == 123


@pytest.mark.unit
class TestRegisterOverride:
    """Test overriding existing registrations"""
    
    def test_override_registration(self, external_class):
        """Later registration should override earlier one"""
        register_jsonic_type(external_class, transient_attributes=['email'])
        
        user = external_class("Alice", "alice@example.com")
        serialized = serialize(user)
        assert 'email' not in serialized
        
        # Re-register without transient
        register_jsonic_type(external_class, transient_attributes=[])
        
        user2 = external_class("Bob", "bob@example.com")
        serialized2 = serialize(user2)
        assert 'email' in serialized2


@pytest.mark.unit
class TestNestedRegisteredTypes:
    """Test nested registered types"""
    
    def test_nested_registered_types(self):
        """Nested registered types should work"""
        class Address:
            def __init__(self, city: str):
                self.city = city
            
            def __eq__(self, other):
                return isinstance(other, Address) and self.city == other.city
        
        class User:
            def __init__(self, name: str, address: Address):
                self.name = name
                self.address = address
            
            def __eq__(self, other):
                return (isinstance(other, User) and 
                       self.name == other.name and 
                       self.address == other.address)
        
        register_jsonic_type(Address)
        register_jsonic_type(User)
        
        user = User("Alice", Address("NYC"))
        result = deserialize(serialize(user))
        
        assert result == user
        assert result.address.city == "NYC"


@pytest.mark.unit
class TestMixedSerializableAndRegistered:
    """Test mixing Serializable and registered types"""
    
    def test_serializable_containing_registered(self, external_class):
        """Serializable can contain registered types"""
        register_jsonic_type(external_class)
        
        class Container(Serializable):
            def __init__(self, user):
                super().__init__()
                self.user = user
            
            def __eq__(self, other):
                return isinstance(other, Container) and self.user == other.user
        
        user = external_class("Alice", "alice@example.com")
        container = Container(user)
        result = deserialize(serialize(container))
        
        assert result == container
        assert result.user.name == "Alice"
    
    def test_registered_containing_serializable(self, simple_user_class):
        """Registered type can contain Serializable"""
        class Container:
            def __init__(self, user):
                self.user = user
            
            def __eq__(self, other):
                return isinstance(other, Container) and self.user == other.user
        
        register_jsonic_type(Container)
        
        user = simple_user_class("Alice", 30)
        container = Container(user)
        result = deserialize(serialize(container))
        
        assert result == container
        assert result.user.name == "Alice"
