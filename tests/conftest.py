"""Shared fixtures and configuration for all tests"""
import pytest

from jsonic import Serializable
from jsonic.decorators import _JsonicSerializer, _JsonicDeserializer


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global registries between tests to ensure isolation"""
    original_types = Serializable.jsonic_types.copy()
    original_serializers = _JsonicSerializer.serializers.copy()
    original_deserializers = _JsonicDeserializer.deserializers.copy()
    
    yield
    
    Serializable.jsonic_types = original_types
    _JsonicSerializer.serializers = original_serializers
    _JsonicDeserializer.deserializers = original_deserializers


@pytest.fixture
def simple_user_class():
    """Simple user class for testing"""
    class User(Serializable):
        def __init__(self, name: str, age: int):
            super().__init__()
            self.name = name
            self.age = age
        
        def __eq__(self, other):
            return isinstance(other, User) and self.name == other.name and self.age == other.age
    
    return User


@pytest.fixture
def user_with_private_attrs():
    """User class with private attributes"""
    class User(Serializable):
        def __init__(self, name: str, age: int):
            super().__init__()
            self.name = name
            self.age = age
            self._password = "secret"
            self._internal_id = 12345
        
        def __eq__(self, other):
            return (isinstance(other, User) and 
                   self.name == other.name and 
                   self.age == other.age and
                   self._password == other._password and
                   self._internal_id == other._internal_id)
    
    return User


@pytest.fixture
def user_with_transient():
    """User class with transient attributes"""
    class User(Serializable):
        transient_attributes = ['cached_data', 'temp_value']
        
        def __init__(self, name: str, age: int):
            super().__init__()
            self.name = name
            self.age = age
            self.cached_data = "should not serialize"
            self.temp_value = 999
        
        def __eq__(self, other):
            return isinstance(other, User) and self.name == other.name and self.age == other.age
    
    return User


@pytest.fixture
def user_with_init_mapping():
    """User class with init parameter mapping"""
    class User(Serializable):
        init_parameters_mapping = {'user_id': 'id', 'user_name': 'name'}
        
        def __init__(self, user_id: int, user_name: str):
            super().__init__()
            self.id = user_id
            self.name = user_name
        
        def __eq__(self, other):
            return isinstance(other, User) and self.id == other.id and self.name == other.name
    
    return User


@pytest.fixture
def nested_classes():
    """Nested class structure for testing"""
    class Address(Serializable):
        def __init__(self, street: str, city: str):
            super().__init__()
            self.street = street
            self.city = city
        
        def __eq__(self, other):
            return isinstance(other, Address) and self.street == other.street and self.city == other.city
    
    class User(Serializable):
        def __init__(self, name: str, address: Address):
            super().__init__()
            self.name = name
            self.address = address
        
        def __eq__(self, other):
            return isinstance(other, User) and self.name == other.name and self.address == other.address
    
    return {'User': User, 'Address': Address}


@pytest.fixture
def external_class():
    """External class (not Serializable) for register_jsonic_type testing"""
    class ExternalUser:
        def __init__(self, name: str, email: str):
            self.name = name
            self.email = email
        
        def __eq__(self, other):
            return isinstance(other, ExternalUser) and self.name == other.name and self.email == other.email
    
    return ExternalUser
