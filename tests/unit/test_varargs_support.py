"""Tests for classes with *args and **kwargs in __init__."""

import pytest
from dataclasses import dataclass
from typing import Any
from jsonic import serialize, deserialize, Serializable


class TestVarArgsInInit:
    """Test classes with *args in __init__."""
    
    def test_class_with_args_only(self):
        """Class that accepts *args."""
        class FlexibleList:
            def __init__(self, *args):
                self.items = list(args)
        
        obj = FlexibleList(1, 2, 3, 4, 5)
        result = deserialize(serialize(obj), expected_type=FlexibleList)
        
        assert result.items == [1, 2, 3, 4, 5]
    
    def test_class_with_regular_and_args(self):
        """Class with regular params and *args."""
        class Container:
            def __init__(self, name: str, *items):
                self.name = name
                self.items = list(items)
        
        obj = Container("box", "apple", "banana", "orange")
        result = deserialize(serialize(obj), expected_type=Container)
        
        assert result.name == "box"
        assert result.items == ["apple", "banana", "orange"]
    
    def test_serializable_with_args(self):
        """Serializable class with *args."""
        class FlexibleSerializable(Serializable):
            def __init__(self, name: str, *values):
                super().__init__()
                self.name = name
                self.values = list(values)
        
        obj = FlexibleSerializable("test", 1, 2, 3)
        result = deserialize(serialize(obj))
        
        assert result.name == "test"
        assert result.values == [1, 2, 3]


class TestKwargsInInit:
    """Test classes with **kwargs in __init__."""
    
    def test_class_with_kwargs_only(self):
        """Class that accepts **kwargs."""
        class FlexibleDict:
            def __init__(self, **kwargs):
                self.data = kwargs
        
        obj = FlexibleDict(a=1, b=2, c=3)
        result = deserialize(serialize(obj), expected_type=FlexibleDict)
        
        assert result.data == {"a": 1, "b": 2, "c": 3}
    
    def test_class_with_regular_and_kwargs(self):
        """Class with regular params and **kwargs."""
        class Config:
            def __init__(self, name: str, **settings):
                self.name = name
                self.settings = settings
        
        obj = Config("app", debug=True, timeout=30, retries=3)
        result = deserialize(serialize(obj), expected_type=Config)
        
        assert result.name == "app"
        assert result.settings == {"debug": True, "timeout": 30, "retries": 3}
    
    def test_serializable_with_kwargs(self):
        """Serializable class with **kwargs."""
        class FlexibleSerializable(Serializable):
            def __init__(self, id: int, **metadata):
                super().__init__()
                self.id = id
                self.metadata = metadata
        
        obj = FlexibleSerializable(123, author="Alice", version="1.0")
        result = deserialize(serialize(obj))
        
        assert result.id == 123
        assert result.metadata == {"author": "Alice", "version": "1.0"}


class TestMixedVarArgs:
    """Test classes with both *args and **kwargs."""
    
    def test_class_with_args_and_kwargs(self):
        """Class with both *args and **kwargs."""
        class Flexible:
            def __init__(self, name: str, *args, **kwargs):
                self.name = name
                self.args = list(args)
                self.kwargs = kwargs
        
        obj = Flexible("test", 1, 2, 3, a="x", b="y")
        result = deserialize(serialize(obj), expected_type=Flexible)
        
        assert result.name == "test"
        assert result.args == [1, 2, 3]
        assert result.kwargs == {"a": "x", "b": "y"}
    
    def test_serializable_with_args_and_kwargs(self):
        """Serializable with both *args and **kwargs."""
        class SuperFlexible(Serializable):
            def __init__(self, id: int, *tags, **metadata):
                super().__init__()
                self.id = id
                self.tags = list(tags)
                self.metadata = metadata
        
        obj = SuperFlexible(1, "python", "json", author="Bob", year=2025)
        result = deserialize(serialize(obj))
        
        assert result.id == 1
        assert result.tags == ["python", "json"]
        assert result.metadata == {"author": "Bob", "year": 2025}


class TestVarArgsEdgeCases:
    """Test edge cases with varargs."""
    
    def test_empty_args(self):
        """Class with *args but none provided."""
        class Container:
            def __init__(self, name: str, *items):
                self.name = name
                self.items = list(items)
        
        obj = Container("empty")
        result = deserialize(serialize(obj), expected_type=Container)
        
        assert result.name == "empty"
        assert result.items == []
    
    def test_empty_kwargs(self):
        """Class with **kwargs but none provided."""
        class Config:
            def __init__(self, name: str, **settings):
                self.name = name
                self.settings = settings
        
        obj = Config("minimal")
        result = deserialize(serialize(obj), expected_type=Config)
        
        assert result.name == "minimal"
        assert result.settings == {}
    
    def test_nested_objects_in_kwargs(self):
        """Nested objects passed via **kwargs."""
        @dataclass
        class Address:
            city: str
        
        class Person:
            def __init__(self, name: str, **extra):
                self.name = name
                self.extra = extra
        
        obj = Person("Alice", address=Address("NYC"), age=30)
        result = deserialize(serialize(obj), expected_type=Person)
        
        assert result.name == "Alice"
        assert result.extra["age"] == 30
        assert isinstance(result.extra["address"], Address)
        assert result.extra["address"].city == "NYC"


class TestDataclassWithVarArgs:
    """Test if dataclasses can have varargs (they can't by default)."""
    
    def test_dataclass_with_custom_init_limitation(self):
        """Dataclasses with custom __init__ have limitations."""
        # LIMITATION: DataclassResolver only serializes declared fields
        # Attributes set in custom __init__ that aren't fields won't be serialized
        
        @dataclass
        class CustomInit:
            name: str
            
            def __init__(self, name: str, *args, **kwargs):
                self.name = name
                self.extra_args = list(args)  # NOT a field, won't be serialized
                self.extra_kwargs = kwargs     # NOT a field, won't be serialized
        
        obj = CustomInit("test", 1, 2, x=3)
        
        # Only declared fields are serialized
        serialized = serialize(obj)
        assert "name" in serialized
        assert "extra_args" not in serialized  # Not a field!
        assert "extra_kwargs" not in serialized  # Not a field!
        
        # Deserialization only restores declared fields
        result = deserialize(serialized, expected_type=CustomInit)
        assert result.name == "test"
        assert result.extra_args == []  # Empty because no args passed
        assert result.extra_kwargs == {}  # Empty because no kwargs passed
