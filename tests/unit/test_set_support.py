"""Tests for set serialization/deserialization support."""

from dataclasses import dataclass
from typing import Set, Optional
from jsonic import serialize, deserialize, Serializable


class TestBasicSets:
    """Test basic set serialization."""
    
    def test_simple_set(self):
        """Simple set of integers."""
        data = {1, 2, 3}
        result = deserialize(serialize(data))
        assert result == {1, 2, 3}
        assert isinstance(result, set)
    
    def test_mixed_type_set(self):
        """Set with mixed types."""
        data = {1, "two", 3.0}
        result = deserialize(serialize(data))
        assert result == {1, "two", 3.0}
        assert isinstance(result, set)
    
    def test_empty_set(self):
        """Empty set."""
        data = set()
        result = deserialize(serialize(data))
        assert result == set()
        assert isinstance(result, set)
    
    def test_single_element_set(self):
        """Set with single element."""
        data = {42}
        result = deserialize(serialize(data))
        assert result == {42}
        assert isinstance(result, set)


class TestNestedSets:
    """Test nested set structures."""
    
    def test_set_with_list(self):
        """Set cannot contain lists (unhashable), but can be in a list."""
        data = [{1, 2}, {3, 4}]
        result = deserialize(serialize(data))
        assert result == [{1, 2}, {3, 4}]
        assert all(isinstance(s, set) for s in result)


class TestSetsInCollections:
    """Test sets within other collections."""
    
    def test_list_of_sets(self):
        """List containing sets."""
        data = [{1, 2}, {3, 4}, {5, 6}]
        result = deserialize(serialize(data))
        assert result == [{1, 2}, {3, 4}, {5, 6}]
        assert all(isinstance(s, set) for s in result)
    
    def test_dict_with_set_values(self):
        """Dict with set values."""
        data = {"a": {1, 2}, "b": {3, 4}}
        result = deserialize(serialize(data))
        assert result == {"a": {1, 2}, "b": {3, 4}}
        assert all(isinstance(v, set) for v in result.values())
    
    def test_nested_collections_with_sets(self):
        """Complex nested structure with sets."""
        data = {
            "tags": [{1, 2}, {3, 4}],
            "groups": {"x": {0, 10}, "y": {0, 20}}
        }
        result = deserialize(serialize(data))
        assert result == data
        assert all(isinstance(s, set) for s in result["tags"])
        assert all(isinstance(v, set) for v in result["groups"].values())


class TestSetsInSerializable:
    """Test sets in Serializable classes."""
    
    def test_serializable_with_set_attribute(self):
        """Serializable class with set attribute."""
        class TaggedItem(Serializable):
            def __init__(self, tags: Set[str]):
                super().__init__()
                self.tags = tags
        
        item = TaggedItem({"python", "json", "serialization"})
        result = deserialize(serialize(item))
        
        assert result.tags == {"python", "json", "serialization"}
        assert isinstance(result.tags, set)
    
    def test_serializable_with_multiple_sets(self):
        """Serializable with multiple set attributes."""
        class Document(Serializable):
            def __init__(self, tags, categories):
                super().__init__()
                self.tags = tags
                self.categories = categories
        
        doc = Document({"tag1", "tag2"}, {"cat1", "cat2"})
        result = deserialize(serialize(doc))
        
        assert result.tags == {"tag1", "tag2"}
        assert result.categories == {"cat1", "cat2"}
        assert isinstance(result.tags, set)
        assert isinstance(result.categories, set)


class TestSetsInDataclasses:
    """Test sets in dataclass fields."""
    
    def test_dataclass_with_set(self):
        """Dataclass with set field."""
        @dataclass
        class TaggedItem:
            tags: Set[str]
        
        item = TaggedItem({"python", "json"})
        result = deserialize(serialize(item), expected_type=TaggedItem)
        
        assert result.tags == {"python", "json"}
        assert isinstance(result.tags, set)
    
    def test_dataclass_with_optional_set(self):
        """Dataclass with Optional set."""
        @dataclass
        class Item:
            name: str
            tags: Optional[Set[str]] = None
        
        item1 = Item("test", {"tag1", "tag2"})
        result1 = deserialize(serialize(item1), expected_type=Item)
        assert result1.tags == {"tag1", "tag2"}
        assert isinstance(result1.tags, set)
        
        item2 = Item("test2", None)
        result2 = deserialize(serialize(item2), expected_type=Item)
        assert result2.tags is None
    
    def test_dataclass_with_int_set(self):
        """Dataclass with set of integers."""
        @dataclass
        class NumberSet:
            numbers: Set[int]
        
        ns = NumberSet({1, 2, 3, 4, 5})
        result = deserialize(serialize(ns), expected_type=NumberSet)
        
        assert result.numbers == {1, 2, 3, 4, 5}
        assert isinstance(result.numbers, set)


class TestSetsInTypeHinted:
    """Test sets in type-hinted classes."""
    
    def test_typehinted_class_with_set(self):
        """Type-hinted class with set."""
        class Item:
            def __init__(self, tags: Set[str]):
                self.tags = tags
        
        item = Item({"python", "json"})
        result = deserialize(serialize(item))
        
        assert result.tags == {"python", "json"}
        assert isinstance(result.tags, set)
    
    def test_typehinted_with_set_of_ints(self):
        """Type-hinted class with set of integers."""
        class NumberCollection:
            def __init__(self, numbers: Set[int]):
                self.numbers = numbers
        
        nc = NumberCollection({10, 20, 30})
        result = deserialize(serialize(nc))
        
        assert result.numbers == {10, 20, 30}
        assert isinstance(result.numbers, set)


class TestSetEdgeCases:
    """Test edge cases for set support."""
    
    def test_set_with_none(self):
        """Set containing None."""
        data = {None, 1, 2}
        result = deserialize(serialize(data))
        assert result == {None, 1, 2}
        assert isinstance(result, set)
    
    def test_set_of_booleans(self):
        """Set of boolean values."""
        data = {True, False}
        result = deserialize(serialize(data))
        assert result == {True, False}
        assert isinstance(result, set)
    
    def test_large_set(self):
        """Large set."""
        data = set(range(1000))
        result = deserialize(serialize(data))
        assert result == data
        assert isinstance(result, set)
    
    def test_set_roundtrip_preserves_type(self):
        """Verify set type is preserved through serialization."""
        data = {1, 2, 3}
        serialized = serialize(data)
        result = deserialize(serialized)
        assert type(result) == set
        assert result == data


class TestSetsWithObjects:
    """Test sets containing or within objects."""
    
    def test_dataclass_with_set_of_strings(self):
        """Dataclass containing set of strings."""
        @dataclass
        class Document:
            title: str
            tags: Set[str]
        
        doc = Document("My Doc", {"python", "tutorial", "beginner"})
        result = deserialize(serialize(doc), expected_type=Document)
        
        assert isinstance(result.tags, set)
        assert result.tags == {"python", "tutorial", "beginner"}
        assert result.title == "My Doc"
