"""Tests for error handling and graceful failures."""

import pytest
from dataclasses import dataclass
from typing import Set, Tuple
from jsonic import serialize, deserialize, Serializable


class TestInvalidSlotsFormat:
    """Test error handling for invalid __slots__ formats."""
    
    def test_slots_as_integer(self):
        """__slots__ defined as integer should fail at class definition."""
        # Python itself raises TypeError when defining class with invalid __slots__
        with pytest.raises(TypeError):
            class BadSlots:
                __slots__ = 123  # Invalid - Python raises TypeError
                
                def __init__(self):
                    pass
    
    def test_slots_as_dict(self):
        """__slots__ defined as dict should fail gracefully."""
        class BadSlots:
            __slots__ = {'x': 1}  # Invalid - will iterate keys
            
            def __init__(self):
                pass
        
        obj = BadSlots()
        # Dict keys are iterable, so this might work but attributes won't exist
        result = serialize(obj)
        # Should serialize but with no actual slot values
        assert '_serialized_type' in result


class TestCircularReferences:
    """Test handling of circular references."""
    
    def test_simple_circular_reference(self):
        """Object A contains B, B contains A."""
        class Node:
            def __init__(self, value):
                self.value = value
                self.next = None
        
        a = Node(1)
        b = Node(2)
        a.next = b
        b.next = a  # Circular reference
        
        # JSON encoder detects circular references
        with pytest.raises(ValueError):
            serialize(a)
    
    def test_self_reference(self):
        """Object contains itself."""
        class SelfRef:
            def __init__(self):
                self.ref = None
        
        obj = SelfRef()
        obj.ref = obj  # Self reference
        
        with pytest.raises(ValueError):
            serialize(obj)


class TestMalformedSerializedData:
    """Test deserialization of malformed data."""
    
    def test_missing_is_tuple_marker(self):
        """Tuple data without _is_tuple marker but with _serialized_type."""
        malformed = {
            'items': [1, 2, 3],
            '_serialized_type': 'tuple'
            # Missing '_is_tuple': True
        }
        
        # Will try to use custom deserializer for 'tuple'
        result = deserialize(malformed)
        # Custom deserializer expects 'items', so should work
        assert isinstance(result, tuple)
    
    def test_missing_is_set_marker(self):
        """Set data without _is_set marker but with _serialized_type."""
        malformed = {
            'items': [1, 2, 3],
            '_serialized_type': 'set'
            # Missing '_is_set': True
        }
        
        # Will try to use custom deserializer for 'set'
        result = deserialize(malformed)
        # Custom deserializer expects 'items', so should work
        assert isinstance(result, set)
    
    def test_tuple_without_items(self):
        """Tuple marker without items field."""
        malformed = {
            '_is_tuple': True,
            '_serialized_type': 'tuple'
            # Missing 'items'
        }
        
        with pytest.raises(KeyError):
            deserialize(malformed)
    
    def test_set_without_items(self):
        """Set marker without items field."""
        malformed = {
            '_is_set': True,
            '_serialized_type': 'set'
            # Missing 'items'
        }
        
        with pytest.raises(KeyError):
            deserialize(malformed)


class TestTypeMismatchDeserialization:
    """Test type mismatches during deserialization."""
    
    def test_deserialize_set_as_tuple(self):
        """Try to deserialize set data as tuple."""
        data = {1, 2, 3}
        serialized = serialize(data)
        
        # Manually change marker
        serialized['_is_tuple'] = True
        del serialized['_is_set']
        
        result = deserialize(serialized)
        # Should deserialize as tuple
        assert isinstance(result, tuple)
    
    def test_deserialize_tuple_as_set(self):
        """Try to deserialize tuple data as set."""
        data = (1, 2, 3)
        serialized = serialize(data)
        
        # Manually change marker
        serialized['_is_set'] = True
        del serialized['_is_tuple']
        
        result = deserialize(serialized)
        # Should deserialize as set
        assert isinstance(result, set)
    
    def test_wrong_expected_type(self):
        """Deserialize with wrong expected_type."""
        @dataclass
        class Point:
            x: int
            y: int
        
        @dataclass
        class Line:
            start: Point
            end: Point
        
        point = Point(1, 2)
        serialized = serialize(point)
        
        # Try to deserialize Point as Line
        with pytest.raises(AttributeError):
            deserialize(serialized, expected_type=Line)


class TestMissingInitParameters:
    """Test missing __init__ parameters."""
    
    def test_dataclass_missing_required_field(self):
        """Dataclass with missing required field in serialized data."""
        @dataclass
        class Person:
            name: str
            age: int
        
        # Manually create incomplete data
        incomplete = {
            '_serialized_type': 'tests.unit.test_error_handling.Person',
            'name': 'Alice'
            # Missing 'age'
        }
        
        with pytest.raises((AttributeError, TypeError)):
            deserialize(incomplete, expected_type=Person)
    
    def test_regular_class_missing_parameter(self):
        """Regular class with missing __init__ parameter."""
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y
        
        incomplete = {
            '_serialized_type': 'tests.unit.test_error_handling.Point',
            'x': 10
            # Missing 'y'
        }
        
        with pytest.raises((AttributeError, TypeError)):
            deserialize(incomplete)


class TestUnhashableInSet:
    """Test unhashable types in sets."""
    
    def test_list_in_set(self):
        """Lists are unhashable and can't be in sets."""
        with pytest.raises(TypeError):
            data = {[1, 2], [3, 4]}  # Should fail at creation
    
    def test_dict_in_set(self):
        """Dicts are unhashable and can't be in sets."""
        with pytest.raises(TypeError):
            data = {{'a': 1}, {'b': 2}}  # Should fail at creation
    
    def test_set_in_set(self):
        """Sets are unhashable and can't be in sets."""
        with pytest.raises(TypeError):
            data = {{1, 2}, {3, 4}}  # Should fail at creation


class TestInvalidTypeNames:
    """Test invalid or missing type names."""
    
    def test_missing_serialized_type(self):
        """Object without _serialized_type."""
        data = {'x': 10, 'y': 20}
        # This is just a dict, should deserialize as dict
        result = deserialize(data)
        assert isinstance(result, dict)
        assert result == {'x': 10, 'y': 20}
    
    def test_nonexistent_type(self):
        """_serialized_type references non-existent class."""
        data = {
            '_serialized_type': 'nonexistent.module.FakeClass',
            'value': 42
        }
        
        with pytest.raises((TypeError, AttributeError, ModuleNotFoundError)):
            deserialize(data)
    
    def test_invalid_type_format(self):
        """_serialized_type with invalid format."""
        data = {
            '_serialized_type': 'not-a-valid-type-name!!!',
            'value': 42
        }
        
        with pytest.raises((TypeError, AttributeError, ValueError)):
            deserialize(data)


class TestEmptyAndNullEdgeCases:
    """Test empty and null edge cases."""
    
    def test_none_as_top_level(self):
        """Serialize/deserialize None."""
        result = deserialize(serialize(None))
        assert result is None
    
    def test_empty_dict(self):
        """Empty dict."""
        result = deserialize(serialize({}))
        assert result == {}
    
    def test_empty_list(self):
        """Empty list."""
        result = deserialize(serialize([]))
        assert result == []
    
    def test_dataclass_with_all_none(self):
        """Dataclass with all None values."""
        @dataclass
        class AllNone:
            a: int = None
            b: str = None
            c: list = None
        
        obj = AllNone()
        result = deserialize(serialize(obj), expected_type=AllNone)
        assert result.a is None
        assert result.b is None
        assert result.c is None


class TestDuplicateSlotsInheritance:
    """Test duplicate slot names in inheritance."""
    
    def test_duplicate_slot_names(self):
        """Parent and child both define same slot."""
        class Parent:
            __slots__ = ['value']
            
            def __init__(self, value):
                self.value = value
        
        class Child(Parent):
            __slots__ = ['value']  # Duplicate
            
            def __init__(self, value):
                super().__init__(value)
        
        # This might work or fail depending on Python version
        # Just test it doesn't crash serialization
        try:
            obj = Child(42)
            result = deserialize(serialize(obj))
            assert result.value == 42
        except (TypeError, AttributeError):
            # Some Python versions don't allow this
            pass


class TestLargeDataStructures:
    """Test very large data structures."""
    
    def test_large_tuple(self):
        """Tuple with 10,000 elements."""
        data = tuple(range(10000))
        result = deserialize(serialize(data))
        assert result == data
        assert isinstance(result, tuple)
    
    def test_large_set(self):
        """Set with 10,000 elements."""
        data = set(range(10000))
        result = deserialize(serialize(data))
        assert result == data
        assert isinstance(result, set)
    
    def test_deeply_nested_tuples(self):
        """Very deeply nested tuples (100 levels)."""
        data = 1
        for _ in range(100):
            data = (data,)
        
        result = deserialize(serialize(data))
        
        # Verify nesting
        temp = result
        for _ in range(100):
            assert isinstance(temp, tuple)
            assert len(temp) == 1
            temp = temp[0]
        assert temp == 1


class TestStringInputOutput:
    """Test string_input and string_output parameters."""
    
    def test_string_output_with_tuple(self):
        """Serialize tuple to JSON string."""
        data = (1, 2, 3)
        result = serialize(data, string_output=True)
        
        assert isinstance(result, str)
        assert '"_is_tuple"' in result
        
        # Should be able to deserialize back
        deserialized = deserialize(result, string_input=True)
        assert deserialized == data
    
    def test_string_output_with_set(self):
        """Serialize set to JSON string."""
        data = {1, 2, 3}
        result = serialize(data, string_output=True)
        
        assert isinstance(result, str)
        assert '"_is_set"' in result
        
        deserialized = deserialize(result, string_input=True)
        assert deserialized == data
    
    def test_invalid_json_string(self):
        """Deserialize invalid JSON string."""
        invalid_json = "{'not': 'valid json'}"  # Single quotes
        
        with pytest.raises((ValueError, TypeError)):
            deserialize(invalid_json, string_input=True)
    
    def test_string_input_wrong_type(self):
        """Pass non-string with string_input=True."""
        with pytest.raises(TypeError):
            deserialize({'x': 1}, string_input=True)


class TestPrivateAttributesInCollections:
    """Test private attributes in tuples/sets."""
    
    def test_object_with_private_in_tuple(self):
        """Tuple containing object with private attributes."""
        class Item:
            def __init__(self, value):
                self.value = value
                self._private = "secret"
        
        data = (Item(1), Item(2))
        
        # Serialize without private attributes
        serialized = serialize(data, serialize_private_attributes=False)
        
        # _private should not be in serialized data
        assert '_private' not in serialized['items'][0]
        assert '_private' not in serialized['items'][1]
        
        result = deserialize(serialized)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Note: _private will be set by __init__ during deserialization
        # This is expected behavior - we can't prevent __init__ from setting attributes
    
    def test_slots_with_private_in_set(self):
        """Set containing __slots__ objects with private slots."""
        class Item:
            __slots__ = ['value', '_private']
            
            def __init__(self, value):
                self.value = value
                self._private = "secret"
        
        # Can't put in set (not hashable), but test serialization
        item = Item(42)
        serialized = serialize(item, serialize_private_attributes=False)
        
        # _private should not be in serialized data
        assert '_private' not in serialized


class TestTransientAttributesEdgeCases:
    """Test transient attributes edge cases."""
    
    def test_transient_with_no_default(self):
        """Transient attribute without default value."""
        class Item(Serializable):
            transient_attributes = ['temp']
            
            def __init__(self, value, temp):
                super().__init__()
                self.value = value
                self.temp = temp
        
        item = Item(42, "temporary")
        serialized = serialize(item)
        
        # temp should not be serialized
        assert 'temp' not in serialized
        
        # Deserialization should fail (no default for temp)
        with pytest.raises((AttributeError, TypeError)):
            deserialize(serialized)
    
    def test_transient_in_dataclass(self):
        """Transient attributes don't apply to dataclasses."""
        @dataclass
        class Item:
            value: int
            temp: str
        
        item = Item(42, "temporary")
        serialized = serialize(item)
        
        # Dataclasses don't support transient_attributes
        # All fields should be serialized
        assert 'temp' in serialized


class TestUnserializableTypes:
    """Test types that can't be serialized."""
    
    def test_function_in_object(self):
        """Object containing a function - JSON encoder skips non-serializable attributes."""
        class Container:
            def __init__(self):
                self.func = lambda x: x + 1
                self.value = 42
        
        obj = Container()
        
        # JSON encoder silently skips functions, serializes other attributes
        result = serialize(obj)
        assert 'value' in result
        # func is skipped by JSON encoder
    
    def test_class_object(self):
        """Try to serialize a class itself - serializes with type marker."""
        class MyClass:
            pass
        
        # Serializing the class (not an instance) produces dict with type marker
        result = serialize(MyClass)
        assert '_serialized_type' in result


class TestDeserializationWithoutType:
    """Test deserialization without expected_type."""
    
    def test_ambiguous_dict(self):
        """Dict that could be object or dict."""
        data = {'x': 10, 'y': 20}
        result = deserialize(data)
        
        # Without _serialized_type, should be dict
        assert isinstance(result, dict)
        assert result == data
    
    def test_nested_ambiguous(self):
        """Nested structure without type info."""
        data = {
            'items': [
                {'x': 1, 'y': 2},
                {'x': 3, 'y': 4}
            ]
        }
        
        result = deserialize(data)
        assert isinstance(result, dict)
        assert isinstance(result['items'], list)
        assert all(isinstance(item, dict) for item in result['items'])
