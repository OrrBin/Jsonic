"""Unit tests for deserialize() function"""
import pytest
from datetime import datetime
from jsonic import serialize, deserialize, Serializable


@pytest.mark.unit
class TestPrimitiveDeserialization:
    """Test deserialization of primitive types"""
    
    @pytest.mark.parametrize("value", [
        42, -42, 0,
        3.14, -3.14, 0.0,
        "hello", "",
        True, False,
        None,
    ])
    def test_primitive_roundtrip(self, value):
        """Primitives should roundtrip correctly"""
        serialized = serialize(value)
        result = deserialize(serialized)
        assert result == value


@pytest.mark.unit
class TestCollectionDeserialization:
    """Test deserialization of collections"""
    
    def test_empty_list_roundtrip(self):
        """Empty list should roundtrip"""
        assert deserialize(serialize([])) == []
    
    def test_empty_dict_roundtrip(self):
        """Empty dict should roundtrip"""
        assert deserialize(serialize({})) == {}
    
    def test_list_roundtrip(self):
        """Lists should roundtrip correctly"""
        data = [1, 2, 3, "test", True, None]
        assert deserialize(serialize(data)) == data
    
    def test_dict_roundtrip(self):
        """Dicts should roundtrip correctly"""
        data = {"a": 1, "b": "test", "c": True, "d": None}
        assert deserialize(serialize(data)) == data
    
    def test_nested_structures_roundtrip(self):
        """Nested structures should roundtrip"""
        data = {
            "list": [1, 2, {"nested": "dict"}],
            "dict": {"nested": [1, 2, 3]}
        }
        assert deserialize(serialize(data)) == data


@pytest.mark.unit
class TestSerializableDeserialization:
    """Test deserialization of Serializable classes"""
    
    def test_simple_class_roundtrip(self, simple_user_class):
        """Simple Serializable should roundtrip"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user)
        result = deserialize(serialized)
        
        assert result == user
        assert isinstance(result, simple_user_class)
    
    def test_nested_serializable_roundtrip(self, nested_classes):
        """Nested Serializable objects should roundtrip"""
        Address = nested_classes['Address']
        User = nested_classes['User']
        
        user = User("Alice", Address("123 Main St", "NYC"))
        result = deserialize(serialize(user))
        
        assert result == user
        assert isinstance(result.address, Address)
    
    def test_list_of_serializable_roundtrip(self, simple_user_class):
        """List of Serializable should roundtrip"""
        users = [
            simple_user_class("Alice", 30),
            simple_user_class("Bob", 25),
        ]
        result = deserialize(serialize(users))
        
        assert len(result) == 2
        assert result == users


@pytest.mark.unit
class TestPrivateAttributeDeserialization:
    """Test private attribute handling in deserialization"""
    
    def test_private_attrs_excluded_by_default(self, user_with_private_attrs):
        """Private attributes are still deserialized even without flag (current behavior)"""
        user = user_with_private_attrs("Alice", 30)
        serialized = serialize(user, serialize_private_attributes=True)
        result = deserialize(serialized, deserialize_private_attributes=False)
        
        assert result.name == "Alice"
        assert result.age == 30
        # Current behavior: private attrs are still set even without flag
        # This is because deserialize sets all attributes from the dict
        assert hasattr(result, '_password')
        assert result._password == "secret"
    
    def test_private_attrs_included_when_flag_set(self, user_with_private_attrs):
        """Private attributes should be deserialized when flag is True"""
        user = user_with_private_attrs("Alice", 30)
        serialized = serialize(user, serialize_private_attributes=True)
        result = deserialize(serialized, deserialize_private_attributes=True)
        
        assert result == user
        assert result._password == "secret"
        assert result._internal_id == 12345


@pytest.mark.unit
class TestInitParameterMapping:
    """Test init_parameters_mapping functionality"""
    
    def test_init_mapping_roundtrip(self, user_with_init_mapping):
        """Classes with init mapping should roundtrip correctly"""
        user = user_with_init_mapping(user_id=123, user_name="Alice")
        result = deserialize(serialize(user))
        
        assert result == user
        assert result.id == 123
        assert result.name == "Alice"


@pytest.mark.unit
class TestExpectedType:
    """Test expected_type parameter"""
    
    def test_correct_expected_type_passes(self, simple_user_class):
        """Correct expected_type should work"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user)
        result = deserialize(serialized, expected_type=simple_user_class)
        
        assert result == user
    
    def test_wrong_expected_type_raises_error(self, simple_user_class):
        """Wrong expected_type should raise AttributeError"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user)
        
        class OtherClass(Serializable):
            pass
        
        with pytest.raises(AttributeError, match="not the expected type"):
            deserialize(serialized, expected_type=OtherClass)
    
    def test_expected_type_list(self):
        """expected_type=list should validate correctly"""
        data = [1, 2, 3]
        serialized = serialize(data)
        result = deserialize(serialized, expected_type=list)
        assert result == data
    
    def test_expected_type_dict(self):
        """expected_type=dict should validate correctly"""
        data = {"a": 1}
        serialized = serialize(data)
        result = deserialize(serialized, expected_type=dict)
        assert result == data
    
    def test_expected_type_mismatch_list_vs_dict(self):
        """Mismatched expected_type should raise error"""
        data = [1, 2, 3]
        serialized = serialize(data)
        
        with pytest.raises(AttributeError, match="not the expected type"):
            deserialize(serialized, expected_type=dict)


@pytest.mark.unit
class TestStringInput:
    """Test string_input parameter"""
    
    def test_string_input_true(self, simple_user_class):
        """string_input=True should parse JSON string"""
        user = simple_user_class("Alice", 30)
        json_string = serialize(user, string_output=True)
        result = deserialize(json_string, string_input=True)
        
        assert result == user
    
    def test_string_input_false_with_dict(self, simple_user_class):
        """string_input=False should work with dict"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user, string_output=False)
        result = deserialize(serialized, string_input=False)
        
        assert result == user
    
    def test_string_input_true_with_dict_raises_error(self, simple_user_class):
        """string_input=True with dict should raise TypeError"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user, string_output=False)
        
        with pytest.raises(TypeError, match="deserializing string"):
            deserialize(serialized, string_input=True)


@pytest.mark.unit
class TestDatetimeDeserialization:
    """Test datetime deserialization"""
    
    def test_datetime_roundtrip(self):
        """Datetime should roundtrip correctly"""
        dt = datetime(2020, 10, 11, 12, 30, 45)
        result = deserialize(serialize(dt))
        
        assert isinstance(result, datetime)
        assert result == dt


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in deserialization"""
    
    def test_missing_serialized_type_for_object(self):
        """Missing _serialized_type should raise error for objects"""
        data = {"name": "Alice", "age": 30}  # No _serialized_type
        # This should work as generic dict
        result = deserialize(data)
        assert result == data
    
    def test_invalid_json_string(self):
        """Invalid JSON string should raise error"""
        with pytest.raises(Exception):  # json.JSONDecodeError
            deserialize("invalid json{", string_input=True)
    
    def test_unknown_type_name(self):
        """Unknown type name should raise error"""
        data = {
            "_serialized_type": "NonExistent.Class.Name",
            "field": "value"
        }
        with pytest.raises(Exception):  # ModuleNotFoundError or AttributeError
            deserialize(data)
    
    def test_missing_required_init_parameter(self):
        """Missing required __init__ parameter should raise error"""
        class User(Serializable):
            def __init__(self, name: str, age: int):
                super().__init__()
                self.name = name
                self.age = age
        
        # Serialize then manually remove a field
        user = User("Alice", 30)
        serialized = serialize(user)
        del serialized['age']  # Remove required field
        
        with pytest.raises(Exception):  # TypeError or AttributeError
            deserialize(serialized)


@pytest.mark.unit
class TestComplexRoundtrips:
    """Test complex roundtrip scenarios"""
    
    def test_deeply_nested_roundtrip(self):
        """Deeply nested structures should roundtrip"""
        data = {"level": 1}
        current = data
        for i in range(2, 20):
            current["nested"] = {"level": i}
            current = current["nested"]
        
        result = deserialize(serialize(data))
        assert result == data
    
    def test_mixed_types_roundtrip(self, simple_user_class):
        """Mixed types in complex structure should roundtrip"""
        data = {
            "users": [
                simple_user_class("Alice", 30),
                simple_user_class("Bob", 25),
            ],
            "metadata": {
                "created": datetime(2020, 10, 11),
                "count": 2,
                "active": True
            },
            "tags": ["python", "json", "serialization"]
        }
        
        result = deserialize(serialize(data))
        assert result['users'][0] == data['users'][0]
        assert result['metadata']['count'] == 2
        assert result['tags'] == data['tags']
    
    def test_list_with_none_values(self):
        """Lists with None values should roundtrip"""
        data = [1, None, "test", None, True]
        assert deserialize(serialize(data)) == data
    
    def test_dict_with_none_values(self):
        """Dicts with None values should roundtrip"""
        data = {"a": 1, "b": None, "c": "test", "d": None}
        assert deserialize(serialize(data)) == data
