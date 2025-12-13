"""Comprehensive tests for tuple serialization/deserialization."""

import pytest
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
from jsonic import serialize, deserialize, Serializable


class TestBasicTuples:
    """Test basic tuple serialization/deserialization."""
    
    def test_simple_tuple(self):
        """Simple tuple with primitives."""
        t = (1, 2, 3)
        result = deserialize(serialize(t))
        
        assert result == (1, 2, 3)
        assert isinstance(result, tuple)
    
    def test_mixed_type_tuple(self):
        """Tuple with mixed types."""
        t = (1, "hello", 3.14, True)
        result = deserialize(serialize(t))
        
        assert result == (1, "hello", 3.14, True)
        assert isinstance(result, tuple)
    
    def test_empty_tuple(self):
        """Empty tuple."""
        t = ()
        result = deserialize(serialize(t))
        
        assert result == ()
        assert isinstance(result, tuple)
    
    def test_single_element_tuple(self):
        """Single element tuple."""
        t = (42,)
        result = deserialize(serialize(t))
        
        assert result == (42,)
        assert isinstance(result, tuple)
        assert len(result) == 1


class TestNestedTuples:
    """Test nested tuple structures."""
    
    def test_tuple_of_tuples(self):
        """Tuple containing other tuples."""
        t = ((1, 2), (3, 4), (5, 6))
        result = deserialize(serialize(t))
        
        assert result == ((1, 2), (3, 4), (5, 6))
        assert isinstance(result, tuple)
        assert isinstance(result[0], tuple)
    
    def test_deeply_nested_tuples(self):
        """Multiple levels of nested tuples."""
        t = (1, (2, (3, (4, 5))))
        result = deserialize(serialize(t))
        
        assert result == (1, (2, (3, (4, 5))))
        assert isinstance(result[1], tuple)
        assert isinstance(result[1][1], tuple)
    
    def test_tuple_with_list(self):
        """Tuple containing list."""
        t = (1, [2, 3], 4)
        result = deserialize(serialize(t))
        
        assert result == (1, [2, 3], 4)
        assert isinstance(result, tuple)
        assert isinstance(result[1], list)


class TestTuplesInCollections:
    """Test tuples inside other collections."""
    
    def test_list_of_tuples(self):
        """List containing tuples."""
        data = [(1, 2), (3, 4), (5, 6)]
        result = deserialize(serialize(data))
        
        assert result == [(1, 2), (3, 4), (5, 6)]
        assert isinstance(result[0], tuple)
    
    def test_dict_with_tuple_values(self):
        """Dict with tuple values."""
        data = {"a": (1, 2), "b": (3, 4)}
        result = deserialize(serialize(data))
        
        assert result == {"a": (1, 2), "b": (3, 4)}
        assert isinstance(result["a"], tuple)
    
    def test_nested_collections_with_tuples(self):
        """Complex nested structure with tuples."""
        data = {
            "coords": [(1, 2), (3, 4)],
            "ranges": {"x": (0, 10), "y": (0, 20)}
        }
        result = deserialize(serialize(data))
        
        assert result == data
        assert isinstance(result["coords"][0], tuple)
        assert isinstance(result["ranges"]["x"], tuple)


class TestTuplesInSerializable:
    """Test tuples in Serializable classes."""
    
    def test_serializable_with_tuple_attribute(self):
        """Serializable class with tuple attribute."""
        class Point(Serializable):
            def __init__(self, coords: Tuple[float, float]):
                super().__init__()
                self.coords = coords
        
        point = Point((10.5, 20.3))
        result = deserialize(serialize(point))
        
        assert result.coords == (10.5, 20.3)
        assert isinstance(result.coords, tuple)
    
    def test_serializable_with_multiple_tuples(self):
        """Serializable with multiple tuple attributes."""
        class Rectangle(Serializable):
            def __init__(self, top_left, bottom_right):
                super().__init__()
                self.top_left = top_left
                self.bottom_right = bottom_right
        
        rect = Rectangle((0, 0), (100, 50))
        result = deserialize(serialize(rect))
        
        assert result.top_left == (0, 0)
        assert result.bottom_right == (100, 50)
        assert isinstance(result.top_left, tuple)


class TestTuplesInDataclasses:
    """Test tuples in dataclasses."""
    
    def test_dataclass_with_tuple(self):
        """Dataclass with tuple field."""
        @dataclass
        class Point:
            coords: Tuple[int, int]
        
        point = Point((5, 10))
        result = deserialize(serialize(point), expected_type=Point)
        
        assert result.coords == (5, 10)
        assert isinstance(result.coords, tuple)
    
    def test_dataclass_with_optional_tuple(self):
        """Dataclass with Optional tuple."""
        @dataclass
        class Location:
            name: str
            coords: Optional[Tuple[float, float]] = None
        
        loc1 = Location("Home", (40.7, -74.0))
        result1 = deserialize(serialize(loc1), expected_type=Location)
        assert result1.coords == (40.7, -74.0)
        assert isinstance(result1.coords, tuple)
        
        loc2 = Location("Unknown")
        result2 = deserialize(serialize(loc2), expected_type=Location)
        assert result2.coords is None
    
    def test_dataclass_with_nested_tuples(self):
        """Dataclass with nested tuple structure."""
        @dataclass
        class Matrix:
            data: Tuple[Tuple[int, int], Tuple[int, int]]
        
        matrix = Matrix(((1, 2), (3, 4)))
        result = deserialize(serialize(matrix), expected_type=Matrix)
        
        assert result.data == ((1, 2), (3, 4))
        assert isinstance(result.data, tuple)
        assert isinstance(result.data[0], tuple)


class TestTuplesInTypeHinted:
    """Test tuples in type-hinted classes."""
    
    def test_typehinted_class_with_tuple(self):
        """Type-hinted class with tuple."""
        class Vector:
            def __init__(self, components: Tuple[float, ...]):
                self.components = components
        
        vec = Vector((1.0, 2.0, 3.0, 4.0))
        result = deserialize(serialize(vec), expected_type=Vector)
        
        assert result.components == (1.0, 2.0, 3.0, 4.0)
        assert isinstance(result.components, tuple)
    
    def test_typehinted_with_tuple_of_strings(self):
        """Type-hinted class with string tuple."""
        class Tags:
            def __init__(self, tags: Tuple[str, ...]):
                self.tags = tags
        
        obj = Tags(("python", "json", "serialization"))
        result = deserialize(serialize(obj), expected_type=Tags)
        
        assert result.tags == ("python", "json", "serialization")
        assert isinstance(result.tags, tuple)


class TestTupleEdgeCases:
    """Test edge cases for tuple support."""
    
    def test_tuple_with_none(self):
        """Tuple containing None."""
        t = (1, None, 3)
        result = deserialize(serialize(t))
        
        assert result == (1, None, 3)
        assert isinstance(result, tuple)
    
    def test_tuple_of_booleans(self):
        """Tuple of boolean values."""
        t = (True, False, True)
        result = deserialize(serialize(t))
        
        assert result == (True, False, True)
        assert isinstance(result, tuple)
    
    def test_large_tuple(self):
        """Large tuple with many elements."""
        t = tuple(range(100))
        result = deserialize(serialize(t))
        
        assert result == t
        assert isinstance(result, tuple)
        assert len(result) == 100
    
    def test_tuple_roundtrip_preserves_type(self):
        """Multiple roundtrips preserve tuple type."""
        original = (1, 2, 3)
        
        # First roundtrip
        s1 = serialize(original)
        r1 = deserialize(s1)
        assert isinstance(r1, tuple)
        
        # Second roundtrip
        s2 = serialize(r1)
        r2 = deserialize(s2)
        assert isinstance(r2, tuple)
        assert r2 == original


class TestTuplesWithObjects:
    """Test tuples containing complex objects."""
    
    def test_tuple_of_dataclasses(self):
        """Tuple containing dataclass instances."""
        @dataclass
        class Item:
            name: str
            value: int
        
        t = (Item("a", 1), Item("b", 2))
        result = deserialize(serialize(t))
        
        assert len(result) == 2
        assert isinstance(result, tuple)
        assert isinstance(result[0], Item)
        assert result[0].name == "a"
        assert result[1].value == 2
    
    def test_dataclass_with_tuple_of_dataclasses(self):
        """Dataclass containing tuple of dataclasses."""
        @dataclass
        class Point:
            x: int
            y: int
        
        @dataclass
        class Line:
            points: Tuple[Point, Point]
        
        line = Line((Point(0, 0), Point(10, 10)))
        result = deserialize(serialize(line), expected_type=Line)
        
        assert isinstance(result.points, tuple)
        assert isinstance(result.points[0], Point)
        assert result.points[0].x == 0
        assert result.points[1].y == 10
