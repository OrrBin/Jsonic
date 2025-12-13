"""Tests for type hint-based serialization/deserialization."""

import pytest
from typing import List, Dict, Optional, Union, Tuple, Set
from jsonic import serialize, deserialize


class TestBasicTypeHints:
    """Test basic type hint inference."""
    
    def test_class_with_type_hints(self):
        """Regular class with type hints (no dataclass)."""
        class Person:
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
        
        person = Person("Alice", 30)
        result = deserialize(serialize(person), expected_type=Person)
        
        assert result.name == "Alice"
        assert result.age == 30
        assert isinstance(result, Person)
    
    def test_class_with_optional_type_hint(self):
        """Class with Optional type hints."""
        class User:
            def __init__(self, username: str, email: Optional[str] = None):
                self.username = username
                self.email = email
        
        user1 = User("alice", "alice@example.com")
        result1 = deserialize(serialize(user1), expected_type=User)
        assert result1.email == "alice@example.com"
        
        user2 = User("bob")
        result2 = deserialize(serialize(user2), expected_type=User)
        assert result2.email is None


class TestCollectionTypeHints:
    """Test collection type hints."""
    
    def test_list_type_hint(self):
        """Class with List[T] type hint."""
        class Team:
            def __init__(self, name: str, members: List[str]):
                self.name = name
                self.members = members
        
        team = Team("DevOps", ["Alice", "Bob"])
        result = deserialize(serialize(team), expected_type=Team)
        
        assert result.members == ["Alice", "Bob"]
    
    def test_dict_type_hint(self):
        """Class with Dict[K, V] type hint."""
        class Config:
            def __init__(self, settings: Dict[str, int]):
                self.settings = settings
        
        config = Config({"timeout": 30, "retries": 3})
        result = deserialize(serialize(config), expected_type=Config)
        
        assert result.settings == {"timeout": 30, "retries": 3}
    
    def test_nested_collection_type_hints(self):
        """Class with nested collection type hints."""
        class Matrix:
            def __init__(self, data: List[List[int]]):
                self.data = data
        
        matrix = Matrix([[1, 2], [3, 4]])
        result = deserialize(serialize(matrix), expected_type=Matrix)
        
        assert result.data == [[1, 2], [3, 4]]


class TestComplexTypeHints:
    """Test complex type hint patterns."""
    
    def test_union_type_hint(self):
        """Class with Union type hint."""
        class Response:
            def __init__(self, data: Union[str, int]):
                self.data = data
        
        resp1 = Response("success")
        result1 = deserialize(serialize(resp1), expected_type=Response)
        assert result1.data == "success"
        
        resp2 = Response(200)
        result2 = deserialize(serialize(resp2), expected_type=Response)
        assert result2.data == 200
    
    def test_tuple_type_hint(self):
        """Class with Tuple type hint."""
        class Point:
            def __init__(self, coords: Tuple[float, float]):
                self.coords = coords
        
        point = Point((10.5, 20.3))
        result = deserialize(serialize(point), expected_type=Point)
        
        # Tuples are now properly preserved!
        assert result.coords == (10.5, 20.3)
        assert isinstance(result.coords, tuple)
    
    def test_optional_list_type_hint(self):
        """Class with Optional[List[T]] type hint."""
        class Container:
            def __init__(self, items: Optional[List[str]] = None):
                self.items = items
        
        container1 = Container(["a", "b"])
        result1 = deserialize(serialize(container1), expected_type=Container)
        assert result1.items == ["a", "b"]
        
        container2 = Container()
        result2 = deserialize(serialize(container2), expected_type=Container)
        assert result2.items is None


class TestNestedTypeHints:
    """Test nested objects with type hints."""
    
    def test_nested_typed_objects(self):
        """Class containing another typed class."""
        class Address:
            def __init__(self, street: str, city: str):
                self.street = street
                self.city = city
        
        class Person:
            def __init__(self, name: str, address: Address):
                self.name = name
                self.address = address
        
        person = Person("Alice", Address("123 Main", "NYC"))
        result = deserialize(serialize(person), expected_type=Person)
        
        assert result.name == "Alice"
        assert result.address.street == "123 Main"
        assert result.address.city == "NYC"
    
    def test_list_of_typed_objects(self):
        """Class with List of typed objects."""
        class Item:
            def __init__(self, name: str, price: float):
                self.name = name
                self.price = price
        
        class Cart:
            def __init__(self, items: List[Item]):
                self.items = items
        
        cart = Cart([Item("Widget", 9.99), Item("Gadget", 19.99)])
        result = deserialize(serialize(cart), expected_type=Cart)
        
        assert len(result.items) == 2
        assert result.items[0].name == "Widget"
        assert result.items[1].price == 19.99


class TestTypeHintEdgeCases:
    """Test edge cases for type hint support."""
    
    def test_class_without_type_hints(self):
        """Class without type hints should still work."""
        class Legacy:
            def __init__(self, value):
                self.value = value
        
        obj = Legacy(42)
        result = deserialize(serialize(obj), expected_type=Legacy)
        assert result.value == 42
    
    def test_partial_type_hints(self):
        """Class with some parameters having type hints."""
        class Mixed:
            def __init__(self, typed: str, untyped):
                self.typed = typed
                self.untyped = untyped
        
        obj = Mixed("hello", 123)
        result = deserialize(serialize(obj), expected_type=Mixed)
        
        assert result.typed == "hello"
        assert result.untyped == 123
    
    def test_class_with_extra_attributes(self):
        """Class that sets attributes not in __init__."""
        class Computed:
            def __init__(self, value: int):
                self.value = value
                self.doubled = value * 2
        
        obj = Computed(5)
        result = deserialize(serialize(obj), expected_type=Computed)
        
        assert result.value == 5
        assert result.doubled == 10


class TestTypeHintInheritance:
    """Test inheritance with type hints."""
    
    def test_inheritance_with_type_hints(self):
        """Subclass with type hints."""
        class Animal:
            def __init__(self, name: str):
                self.name = name
        
        class Dog(Animal):
            def __init__(self, name: str, breed: str):
                super().__init__(name)
                self.breed = breed
        
        dog = Dog("Buddy", "Golden Retriever")
        result = deserialize(serialize(dog), expected_type=Dog)
        
        assert result.name == "Buddy"
        assert result.breed == "Golden Retriever"
