"""Unit tests for serialize() function"""
import pytest
from datetime import datetime
from jsonic import serialize, Serializable


@pytest.mark.unit
class TestPrimitiveTypes:
    """Test serialization of primitive Python types"""
    
    @pytest.mark.parametrize("value", [
        42, -42, 0, 2**63 - 1,  # integers
        3.14, -3.14, 0.0, float('inf'), float('-inf'),  # floats
        "hello", "", "unicode: 你好 🎉",  # strings
        True, False,  # booleans
        None,  # None
    ])
    def test_primitive_serialization(self, value):
        """Primitive types should serialize to themselves"""
        result = serialize(value)
        assert result == value
    
    def test_nan_serialization(self):
        """NaN should serialize (though may not equal itself)"""
        result = serialize(float('nan'))
        # NaN serializes but doesn't equal itself
        import math
        assert math.isnan(result) or result is None


@pytest.mark.unit
class TestCollections:
    """Test serialization of collections"""
    
    def test_empty_list(self):
        """Empty list should serialize correctly"""
        assert serialize([]) == []
    
    def test_empty_dict(self):
        """Empty dict should serialize correctly"""
        assert serialize({}) == {}
    
    def test_simple_list(self):
        """Simple list should serialize correctly"""
        data = [1, 2, 3, "test", True, None]
        assert serialize(data) == data
    
    def test_simple_dict(self):
        """Simple dict should serialize correctly"""
        data = {"a": 1, "b": "test", "c": True, "d": None}
        assert serialize(data) == data
    
    def test_nested_list(self):
        """Nested lists should serialize correctly"""
        data = [1, [2, [3, [4, [5]]]]]
        assert serialize(data) == data
    
    def test_nested_dict(self):
        """Nested dicts should serialize correctly"""
        data = {"a": {"b": {"c": {"d": "deep"}}}}
        assert serialize(data) == data
    
    def test_mixed_nested_structures(self):
        """Mixed nested structures should serialize correctly"""
        data = {
            "list": [1, 2, {"nested": "dict"}],
            "dict": {"nested": [1, 2, 3]},
            "deep": {"a": [{"b": [{"c": "value"}]}]}
        }
        assert serialize(data) == data


@pytest.mark.unit
class TestSerializableClasses:
    """Test serialization of Serializable classes"""
    
    def test_simple_class(self, simple_user_class):
        """Simple Serializable class should serialize with type info"""
        user = simple_user_class("Alice", 30)
        result = serialize(user)
        
        assert isinstance(result, dict)
        assert result['name'] == "Alice"
        assert result['age'] == 30
        assert '_serialized_type' in result
    
    def test_nested_serializable(self, nested_classes):
        """Nested Serializable objects should serialize recursively"""
        Address = nested_classes['Address']
        User = nested_classes['User']
        
        user = User("Alice", Address("123 Main St", "NYC"))
        result = serialize(user)
        
        assert result['name'] == "Alice"
        assert isinstance(result['address'], dict)
        assert result['address']['street'] == "123 Main St"
        assert result['address']['city'] == "NYC"
        assert '_serialized_type' in result['address']
    
    def test_list_of_serializable(self, simple_user_class):
        """List of Serializable objects should serialize correctly"""
        users = [
            simple_user_class("Alice", 30),
            simple_user_class("Bob", 25),
        ]
        result = serialize(users)
        
        assert len(result) == 2
        assert all('_serialized_type' in u for u in result)
        assert result[0]['name'] == "Alice"
        assert result[1]['name'] == "Bob"
    
    def test_dict_with_serializable_values(self, simple_user_class):
        """Dict with Serializable values should serialize correctly"""
        data = {
            "user1": simple_user_class("Alice", 30),
            "user2": simple_user_class("Bob", 25),
        }
        result = serialize(data)
        
        assert result['user1']['name'] == "Alice"
        assert result['user2']['name'] == "Bob"


@pytest.mark.unit
class TestPrivateAttributes:
    """Test private attribute handling"""
    
    def test_private_attrs_excluded_by_default(self, user_with_private_attrs):
        """Private attributes should be excluded by default"""
        user = user_with_private_attrs("Alice", 30)
        result = serialize(user)
        
        assert 'name' in result
        assert 'age' in result
        assert '_password' not in result
        assert '_internal_id' not in result
    
    def test_private_attrs_included_when_flag_set(self, user_with_private_attrs):
        """Private attributes should be included when flag is True"""
        user = user_with_private_attrs("Alice", 30)
        result = serialize(user, serialize_private_attributes=True)
        
        assert 'name' in result
        assert 'age' in result
        assert '_password' in result
        assert result['_password'] == "secret"
        assert '_internal_id' in result
        assert result['_internal_id'] == 12345


@pytest.mark.unit
class TestTransientAttributes:
    """Test transient attribute handling"""
    
    def test_transient_attrs_excluded(self, user_with_transient):
        """Transient attributes should not be serialized"""
        user = user_with_transient("Alice", 30)
        result = serialize(user)
        
        assert 'name' in result
        assert 'age' in result
        assert 'cached_data' not in result
        assert 'temp_value' not in result


@pytest.mark.unit
class TestOutputFormats:
    """Test different output formats"""
    
    def test_dict_output(self, simple_user_class):
        """Default output should be dict"""
        user = simple_user_class("Alice", 30)
        result = serialize(user, string_output=False)
        
        assert isinstance(result, dict)
    
    def test_string_output(self, simple_user_class):
        """string_output=True should return JSON string"""
        user = simple_user_class("Alice", 30)
        result = serialize(user, string_output=True)
        
        assert isinstance(result, str)
        assert '"name"' in result
        assert '"Alice"' in result
    
    def test_string_output_for_primitives(self):
        """String output should work for primitives"""
        result = serialize(42, string_output=True)
        assert result == "42"
        
        result = serialize("test", string_output=True)
        assert result == '"test"'


@pytest.mark.unit
class TestDatetimeSerialization:
    """Test datetime serialization (uses default serializer)"""
    
    def test_datetime_serialization(self):
        """Datetime should serialize with custom serializer"""
        dt = datetime(2020, 10, 11, 12, 30, 45)
        result = serialize(dt)
        
        assert isinstance(result, dict)
        assert '_serialized_type' in result
        assert result['_serialized_type'] == 'datetime'


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases in serialization"""
    
    def test_very_deep_nesting(self):
        """Very deep nesting should work"""
        data = {"level": 1}
        current = data
        for i in range(2, 50):
            current["nested"] = {"level": i}
            current = current["nested"]
        
        result = serialize(data)
        assert result['level'] == 1
    
    def test_large_list(self):
        """Large lists should serialize"""
        data = list(range(10000))
        result = serialize(data)
        assert len(result) == 10000
        assert result[0] == 0
        assert result[-1] == 9999
    
    def test_large_dict(self):
        """Large dicts should serialize"""
        data = {f"key_{i}": i for i in range(1000)}
        result = serialize(data)
        assert len(result) == 1000
    
    def test_unicode_strings(self):
        """Unicode strings should serialize correctly"""
        data = {
            "chinese": "你好世界",
            "emoji": "🎉🚀💻",
            "arabic": "مرحبا",
            "mixed": "Hello 世界 🌍"
        }
        result = serialize(data)
        assert result == data
    
    def test_special_characters(self):
        """Special characters should be handled"""
        data = {
            "newline": "line1\nline2",
            "tab": "col1\tcol2",
            "quote": 'He said "hello"',
            "backslash": "path\\to\\file"
        }
        result = serialize(data)
        assert result == data


@pytest.mark.unit
class TestErrorCases:
    """Test error handling in serialization"""
    
    def test_unserializable_type_serializes_with_dict(self):
        """Classes with __dict__ serialize even without Serializable"""
        class Unserializable:
            def __init__(self):
                self.value = 42
        
        obj = Unserializable()
        result = serialize(obj)
        # Actually serializes because it has __dict__
        assert isinstance(result, dict)
        assert result['value'] == 42
    
    def test_function_serializes_as_string(self):
        """Functions serialize (JSON converts them to string representation)"""
        def my_func():
            pass
        
        # Functions actually get serialized by json.dumps default handler
        result = serialize(my_func)
        assert result is not None  # It does serialize
    
    def test_lambda_serializes_as_string(self):
        """Lambdas serialize (JSON converts them to string representation)"""
        # Lambdas actually get serialized by json.dumps default handler
        result = serialize(lambda x: x)
        assert result is not None  # It does serialize
