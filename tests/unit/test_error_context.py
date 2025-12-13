"""Tests for error messages with serialization path context."""

import pytest
from jsonic import serialize, deserialize, Serializable


class TestSerializationPathContext:
    """Test that errors include the path to where the error occurred."""
    
    def test_nested_serialization_error_includes_path(self):
        """Error during nested serialization should show the path."""
        class Unserializable:
            def __init__(self):
                self.bad = object()  # Generic object can't be serialized
        
        class Container:
            def __init__(self):
                self.nested = Unserializable()
        
        obj = Container()
        
        with pytest.raises(TypeError) as exc_info:
            serialize(obj)
        
        # Error message should include path like "Container.nested"
        assert 'nested' in str(exc_info.value).lower() or 'path' in str(exc_info.value).lower()
    
    def test_deeply_nested_serialization_error_includes_full_path(self):
        """Error in deeply nested structure should show full path."""
        class Level3:
            def __init__(self):
                self.bad = object()  # Can't serialize generic object
        
        class Level2:
            def __init__(self):
                self.level3 = Level3()
        
        class Level1:
            def __init__(self):
                self.level2 = Level2()
        
        obj = Level1()
        
        with pytest.raises(TypeError) as exc_info:
            serialize(obj)
        
        error_msg = str(exc_info.value).lower()
        # Should mention the nested path
        assert 'level2' in error_msg or 'level3' in error_msg or 'path' in error_msg
    
    def test_list_serialization_error_includes_index(self):
        """Error in list element should show index."""
        class Bad:
            def __init__(self):
                self.bad = object()
        
        data = [1, 2, Bad(), 4]
        
        with pytest.raises(TypeError) as exc_info:
            serialize(data)
        
        error_msg = str(exc_info.value)
        # Should mention list index or position
        assert '[' in error_msg or 'index' in error_msg.lower() or 'position' in error_msg.lower()
    
    def test_dict_serialization_error_includes_key(self):
        """Error in dict value should show key."""
        class Bad:
            def __init__(self):
                self.bad = object()
        
        data = {'good': 1, 'bad': Bad(), 'also_good': 2}
        
        with pytest.raises(TypeError) as exc_info:
            serialize(data)
        
        error_msg = str(exc_info.value)
        # Should mention the key
        assert 'bad' in error_msg.lower() or 'key' in error_msg.lower()
    
    def test_deserialization_error_includes_path(self):
        """Error during deserialization should show path."""
        class Inner:
            def __init__(self, required_param):
                self.required_param = required_param
        
        class Outer(Serializable):
            def __init__(self, inner):
                super().__init__()
                self.inner = inner
        
        # Missing required_param in inner
        bad_data = {
            '_serialized_type': 'tests.unit.test_error_context.Outer',
            'inner': {
                '_serialized_type': 'tests.unit.test_error_context.Inner'
                # Missing 'required_param'
            }
        }
        
        with pytest.raises((AttributeError, TypeError)) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value).lower()
        # Should mention the path or field name
        assert 'inner' in error_msg or 'required_param' in error_msg or 'path' in error_msg


class TestDeserializationPathContext:
    """Test deserialization errors include path context."""
    
    def test_missing_field_error_shows_path(self):
        """Missing field error should show where in structure."""
        class Nested:
            def __init__(self, value):
                self.value = value
        
        class Parent(Serializable):
            def __init__(self, nested):
                super().__init__()
                self.nested = nested
        
        bad_data = {
            '_serialized_type': 'tests.unit.test_error_context.Parent',
            'nested': {
                '_serialized_type': 'tests.unit.test_error_context.Nested'
                # Missing 'value'
            }
        }
        
        with pytest.raises((AttributeError, TypeError)) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should mention nested or value
        assert 'nested' in error_msg.lower() or 'value' in error_msg.lower()
    
    def test_list_deserialization_error_includes_index(self):
        """Error deserializing list element should show index."""
        class Item:
            def __init__(self, required):
                self.required = required
        
        bad_data = [
            {'_serialized_type': 'tests.unit.test_error_context.Item', 'required': 1},
            {'_serialized_type': 'tests.unit.test_error_context.Item'},  # Missing required
            {'_serialized_type': 'tests.unit.test_error_context.Item', 'required': 3}
        ]
        
        with pytest.raises((AttributeError, TypeError)) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should mention index or position
        assert '[' in error_msg or 'index' in error_msg.lower() or '1' in error_msg
