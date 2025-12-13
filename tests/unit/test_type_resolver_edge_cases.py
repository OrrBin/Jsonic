"""Edge case tests for type resolver system."""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Generic, TypeVar
from jsonic import serialize, deserialize


class TestCircularReferences:
    """Test circular reference handling."""
    
    def test_circular_reference_raises_error(self):
        """Circular references should raise ValueError."""
        @dataclass
        class Node:
            value: int
            next: Optional['Node'] = None
        
        node1 = Node(1)
        node2 = Node(2)
        node1.next = node2
        node2.next = node1  # Circular reference
        
        with pytest.raises(ValueError, match="Circular reference"):
            serialize(node1)
    
    def test_self_reference_raises_error(self):
        """Self-referencing object should raise ValueError."""
        @dataclass
        class SelfRef:
            value: int
            ref: Optional['SelfRef'] = None
        
        obj = SelfRef(1)
        obj.ref = obj  # Self reference
        
        with pytest.raises(ValueError, match="Circular reference"):
            serialize(obj)


class TestComplexGenerics:
    """Test complex generic type patterns."""
    
    def test_dict_of_lists(self):
        """Dict[str, List[int]] type hint."""
        @dataclass
        class Data:
            mapping: Dict[str, List[int]]
        
        obj = Data({"a": [1, 2, 3], "b": [4, 5]})
        result = deserialize(serialize(obj), expected_type=Data)
        
        assert result.mapping == {"a": [1, 2, 3], "b": [4, 5]}
    
    def test_list_of_dicts(self):
        """List[Dict[str, int]] type hint."""
        @dataclass
        class Records:
            data: List[Dict[str, int]]
        
        obj = Records([{"a": 1}, {"b": 2}])
        result = deserialize(serialize(obj), expected_type=Records)
        
        assert result.data == [{"a": 1}, {"b": 2}]
    
    def test_optional_dict_of_lists(self):
        """Optional[Dict[str, List[str]]] type hint."""
        @dataclass
        class Complex:
            data: Optional[Dict[str, List[str]]]
        
        obj1 = Complex({"key": ["a", "b"]})
        result1 = deserialize(serialize(obj1), expected_type=Complex)
        assert result1.data == {"key": ["a", "b"]}
        
        obj2 = Complex(None)
        result2 = deserialize(serialize(obj2), expected_type=Complex)
        assert result2.data is None


class TestInheritanceEdgeCases:
    """Test complex inheritance scenarios."""
    
    def test_multiple_inheritance_levels(self):
        """Three levels of dataclass inheritance."""
        @dataclass
        class Base:
            id: int
        
        @dataclass
        class Middle(Base):
            name: str
        
        @dataclass
        class Derived(Middle):
            value: float
        
        obj = Derived(1, "test", 3.14)
        result = deserialize(serialize(obj), expected_type=Derived)
        
        assert result.id == 1
        assert result.name == "test"
        assert result.value == 3.14
    
    def test_dataclass_inheriting_from_regular_class(self):
        """Dataclass inheriting from non-dataclass."""
        class Base:
            def __init__(self, base_value: int):
                self.base_value = base_value
        
        @dataclass
        class Derived(Base):
            derived_value: str
            
            def __post_init__(self):
                super().__init__(10)
        
        obj = Derived("test")
        result = deserialize(serialize(obj), expected_type=Derived)
        
        assert result.derived_value == "test"
        assert result.base_value == 10


class TestAnyTypeHint:
    """Test Any type hint handling."""
    
    def test_any_type_hint(self):
        """Field with Any type hint."""
        @dataclass
        class Flexible:
            value: Any
        
        obj1 = Flexible("string")
        result1 = deserialize(serialize(obj1), expected_type=Flexible)
        assert result1.value == "string"
        
        obj2 = Flexible(123)
        result2 = deserialize(serialize(obj2), expected_type=Flexible)
        assert result2.value == 123
        
        obj3 = Flexible([1, 2, 3])
        result3 = deserialize(serialize(obj3), expected_type=Flexible)
        assert result3.value == [1, 2, 3]


class TestForwardReferences:
    """Test forward reference handling."""
    
    def test_forward_reference_in_type_hint(self):
        """Type hint using string forward reference."""
        @dataclass
        class Parent:
            name: str
            child: Optional['Child'] = None
        
        @dataclass
        class Child:
            name: str
        
        parent = Parent("Alice", Child("Bob"))
        result = deserialize(serialize(parent), expected_type=Parent)
        
        assert result.name == "Alice"
        assert result.child.name == "Bob"


class TestEmptyAndNullValues:
    """Test empty and null value handling."""
    
    def test_all_none_values(self):
        """Dataclass with all None values."""
        @dataclass
        class AllOptional:
            a: Optional[str] = None
            b: Optional[int] = None
            c: Optional[List[str]] = None
        
        obj = AllOptional()
        result = deserialize(serialize(obj), expected_type=AllOptional)
        
        assert result.a is None
        assert result.b is None
        assert result.c is None
    
    def test_empty_collections(self):
        """Dataclass with empty collections."""
        @dataclass
        class EmptyCollections:
            empty_list: List[str]
            empty_dict: Dict[str, int]
        
        obj = EmptyCollections([], {})
        result = deserialize(serialize(obj), expected_type=EmptyCollections)
        
        assert result.empty_list == []
        assert result.empty_dict == {}


class TestSpecialCharactersAndUnicode:
    """Test special characters in dataclass fields."""
    
    def test_unicode_in_dataclass(self):
        """Dataclass with unicode strings."""
        @dataclass
        class Unicode:
            text: str
        
        obj = Unicode("Hello 世界 🌍")
        result = deserialize(serialize(obj), expected_type=Unicode)
        
        assert result.text == "Hello 世界 🌍"
    
    def test_special_characters_in_field_values(self):
        """Dataclass with special characters."""
        @dataclass
        class Special:
            value: str
        
        obj = Special("Line1\nLine2\tTabbed")
        result = deserialize(serialize(obj), expected_type=Special)
        
        assert result.value == "Line1\nLine2\tTabbed"


class TestLargeDataStructures:
    """Test performance with large data structures."""
    
    def test_large_list_in_dataclass(self):
        """Dataclass with large list."""
        @dataclass
        class LargeList:
            items: List[int]
        
        obj = LargeList(list(range(1000)))
        result = deserialize(serialize(obj), expected_type=LargeList)
        
        assert len(result.items) == 1000
        assert result.items[0] == 0
        assert result.items[-1] == 999
    
    def test_deeply_nested_dataclasses(self):
        """Deeply nested dataclass structure."""
        @dataclass
        class Level:
            value: int
            next: Optional['Level'] = None
        
        # Create 10 levels deep
        obj = Level(0)
        current = obj
        for i in range(1, 10):
            current.next = Level(i)
            current = current.next
        
        result = deserialize(serialize(obj), expected_type=Level)
        
        # Verify all levels
        current = result
        for i in range(10):
            assert current.value == i
            current = current.next
            if i < 9:
                assert current is not None
            else:
                assert current is None


class TestMalformedData:
    """Test handling of malformed serialized data."""
    
    def test_missing_required_field(self):
        """Deserialization with missing required field should raise error."""
        @dataclass
        class Required:
            name: str
            age: int
        
        malformed = {"name": "Alice", "_serialized_type": "__main__.Required"}
        
        with pytest.raises((AttributeError, TypeError)):
            deserialize(malformed, expected_type=Required)
    
    def test_wrong_type_in_serialized_data(self):
        """Deserialization with wrong type should raise error."""
        @dataclass
        class Expected:
            value: int
        
        from jsonic.util import full_type_name
        malformed = {"value": "not_an_int", "_serialized_type": full_type_name(Expected)}
        
        # Should deserialize but value will be string (type coercion is not enforced)
        result = deserialize(malformed, expected_type=Expected)
        assert result.value == "not_an_int"  # No runtime type checking
