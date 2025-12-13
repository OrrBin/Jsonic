"""Tests for automatic dataclass serialization/deserialization."""

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from jsonic import serialize, deserialize


class TestBasicDataclass:
    """Test basic dataclass serialization/deserialization."""
    
    def test_simple_dataclass(self):
        """Simple dataclass with primitive types."""
        @dataclass
        class Person:
            name: str
            age: int
        
        person = Person("Alice", 30)
        result = deserialize(serialize(person), expected_type=Person)
        
        assert result.name == "Alice"
        assert result.age == 30
        assert isinstance(result, Person)
    
    def test_dataclass_with_defaults(self):
        """Dataclass with default values."""
        @dataclass
        class Config:
            host: str = "localhost"
            port: int = 8080
            debug: bool = False
        
        config = Config(host="example.com")
        result = deserialize(serialize(config), expected_type=Config)
        
        assert result.host == "example.com"
        assert result.port == 8080
        assert result.debug is False
    
    def test_dataclass_with_optional(self):
        """Dataclass with Optional fields."""
        @dataclass
        class User:
            username: str
            email: Optional[str] = None
        
        user1 = User("alice", "alice@example.com")
        result1 = deserialize(serialize(user1), expected_type=User)
        assert result1.email == "alice@example.com"
        
        user2 = User("bob")
        result2 = deserialize(serialize(user2), expected_type=User)
        assert result2.email is None


class TestDataclassWithCollections:
    """Test dataclasses with collection types."""
    
    def test_dataclass_with_list(self):
        """Dataclass with List type hint."""
        @dataclass
        class Team:
            name: str
            members: List[str]
        
        team = Team("DevOps", ["Alice", "Bob", "Charlie"])
        result = deserialize(serialize(team), expected_type=Team)
        
        assert result.name == "DevOps"
        assert result.members == ["Alice", "Bob", "Charlie"]
    
    def test_dataclass_with_dict(self):
        """Dataclass with Dict type hint."""
        @dataclass
        class Settings:
            name: str
            config: Dict[str, int]
        
        settings = Settings("app", {"timeout": 30, "retries": 3})
        result = deserialize(serialize(settings), expected_type=Settings)
        
        assert result.config == {"timeout": 30, "retries": 3}
    
    def test_dataclass_with_list_of_dataclasses(self):
        """Dataclass containing list of other dataclasses."""
        @dataclass
        class Item:
            name: str
            price: float
        
        @dataclass
        class Order:
            order_id: str
            items: List[Item]
        
        order = Order("ORD-123", [
            Item("Widget", 9.99),
            Item("Gadget", 19.99)
        ])
        result = deserialize(serialize(order), expected_type=Order)
        
        assert result.order_id == "ORD-123"
        assert len(result.items) == 2
        assert result.items[0].name == "Widget"
        assert result.items[1].price == 19.99


class TestNestedDataclasses:
    """Test nested dataclass structures."""
    
    def test_nested_dataclass(self):
        """Dataclass containing another dataclass."""
        @dataclass
        class Address:
            street: str
            city: str
        
        @dataclass
        class Person:
            name: str
            address: Address
        
        person = Person("Alice", Address("123 Main St", "NYC"))
        result = deserialize(serialize(person), expected_type=Person)
        
        assert result.name == "Alice"
        assert result.address.street == "123 Main St"
        assert result.address.city == "NYC"
    
    def test_deeply_nested_dataclasses(self):
        """Multiple levels of nested dataclasses."""
        @dataclass
        class Coordinates:
            lat: float
            lon: float
        
        @dataclass
        class Location:
            name: str
            coords: Coordinates
        
        @dataclass
        class Event:
            title: str
            location: Location
        
        event = Event("Conference", Location("Convention Center", Coordinates(40.7, -74.0)))
        result = deserialize(serialize(event), expected_type=Event)
        
        assert result.title == "Conference"
        assert result.location.name == "Convention Center"
        assert result.location.coords.lat == 40.7


class TestDataclassFeatures:
    """Test specific dataclass features."""
    
    def test_frozen_dataclass(self):
        """Frozen (immutable) dataclass."""
        @dataclass(frozen=True)
        class ImmutablePoint:
            x: int
            y: int
        
        point = ImmutablePoint(10, 20)
        result = deserialize(serialize(point), expected_type=ImmutablePoint)
        
        assert result.x == 10
        assert result.y == 20
    
    def test_dataclass_with_field_default_factory(self):
        """Dataclass with field default_factory."""
        @dataclass
        class Container:
            name: str
            items: List[str] = field(default_factory=list)
        
        container1 = Container("box1", ["item1", "item2"])
        result1 = deserialize(serialize(container1), expected_type=Container)
        assert result1.items == ["item1", "item2"]
        
        container2 = Container("box2")
        result2 = deserialize(serialize(container2), expected_type=Container)
        assert result2.items == []
    
    def test_dataclass_with_init_false_field(self):
        """Dataclass with field(init=False)."""
        @dataclass
        class Computed:
            value: int
            doubled: int = field(init=False)
            
            def __post_init__(self):
                self.doubled = self.value * 2
        
        obj = Computed(5)
        result = deserialize(serialize(obj), expected_type=Computed)
        
        assert result.value == 5
        assert result.doubled == 10


class TestDataclassInheritance:
    """Test dataclass inheritance."""
    
    def test_dataclass_inheritance(self):
        """Dataclass inheriting from another dataclass."""
        @dataclass
        class Animal:
            name: str
            age: int
        
        @dataclass
        class Dog(Animal):
            breed: str
        
        dog = Dog("Buddy", 3, "Golden Retriever")
        result = deserialize(serialize(dog), expected_type=Dog)
        
        assert result.name == "Buddy"
        assert result.age == 3
        assert result.breed == "Golden Retriever"


class TestDataclassEdgeCases:
    """Test edge cases for dataclass support."""
    
    def test_empty_dataclass(self):
        """Dataclass with no fields."""
        @dataclass
        class Empty:
            pass
        
        obj = Empty()
        result = deserialize(serialize(obj), expected_type=Empty)
        assert isinstance(result, Empty)
    
    def test_dataclass_with_none_values(self):
        """Dataclass with None values."""
        @dataclass
        class Nullable:
            value: Optional[str]
        
        obj = Nullable(None)
        result = deserialize(serialize(obj), expected_type=Nullable)
        assert result.value is None
    
    def test_dataclass_with_complex_types(self):
        """Dataclass with complex nested types."""
        @dataclass
        class Complex:
            data: Dict[str, List[int]]
        
        obj = Complex({"a": [1, 2, 3], "b": [4, 5]})
        result = deserialize(serialize(obj), expected_type=Complex)
        assert result.data == {"a": [1, 2, 3], "b": [4, 5]}


class TestDataclassWithoutExpectedType:
    """Test dataclass deserialization without expected_type parameter."""
    
    def test_deserialize_without_expected_type(self):
        """Should work when type info is in serialized data."""
        @dataclass
        class Product:
            name: str
            price: float
        
        product = Product("Widget", 9.99)
        serialized = serialize(product)
        result = deserialize(serialized)
        
        assert isinstance(result, Product)
        assert result.name == "Widget"
        assert result.price == 9.99
