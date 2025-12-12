"""Edge case tests for Jsonic"""
import pytest
from jsonic import serialize, deserialize, Serializable


@pytest.mark.edge_case
class TestNoneValues:
    """Test None value handling"""
    
    def test_none_serialization(self):
        """None should serialize correctly"""
        assert serialize(None) is None
    
    def test_none_in_list(self):
        """None in list should work"""
        data = [1, None, 3, None, 5]
        assert deserialize(serialize(data)) == data
    
    def test_none_in_dict(self):
        """None in dict should work"""
        data = {"a": 1, "b": None, "c": 3}
        assert deserialize(serialize(data)) == data
    
    def test_all_none_list(self):
        """List of all None should work"""
        data = [None, None, None]
        assert deserialize(serialize(data)) == data
    
    def test_none_as_object_attribute(self, simple_user_class):
        """None as attribute should work"""
        class User(Serializable):
            def __init__(self, name: str, email=None):
                super().__init__()
                self.name = name
                self.email = email
            
            def __eq__(self, other):
                return (isinstance(other, User) and 
                       self.name == other.name and 
                       self.email == other.email)
        
        user = User("Alice", None)
        result = deserialize(serialize(user))
        assert result.email is None


@pytest.mark.edge_case
class TestEmptyCollections:
    """Test empty collection handling"""
    
    def test_empty_list(self):
        """Empty list should work"""
        assert deserialize(serialize([])) == []
    
    def test_empty_dict(self):
        """Empty dict should work"""
        assert deserialize(serialize({})) == {}
    
    def test_empty_string(self):
        """Empty string should work"""
        assert deserialize(serialize("")) == ""
    
    def test_nested_empty_collections(self):
        """Nested empty collections should work"""
        data = {
            "empty_list": [],
            "empty_dict": {},
            "empty_string": "",
            "nested": {"also_empty": []}
        }
        assert deserialize(serialize(data)) == data


@pytest.mark.edge_case
class TestSpecialNumbers:
    """Test special numeric values"""
    
    def test_zero(self):
        """Zero should work"""
        assert deserialize(serialize(0)) == 0
        assert deserialize(serialize(0.0)) == 0.0
    
    def test_negative_numbers(self):
        """Negative numbers should work"""
        assert deserialize(serialize(-42)) == -42
        assert deserialize(serialize(-3.14)) == -3.14
    
    def test_very_large_int(self):
        """Very large integers should work"""
        large = 2**63 - 1
        assert deserialize(serialize(large)) == large
    
    def test_very_small_float(self):
        """Very small floats should work"""
        small = 1e-100
        assert deserialize(serialize(small)) == small
    
    def test_infinity(self):
        """Infinity should serialize"""
        result = serialize(float('inf'))
        assert result == float('inf') or result is None
    
    def test_negative_infinity(self):
        """Negative infinity should serialize"""
        result = serialize(float('-inf'))
        assert result == float('-inf') or result is None


@pytest.mark.edge_case
class TestUnicodeAndSpecialChars:
    """Test Unicode and special character handling"""
    
    def test_unicode_chinese(self):
        """Chinese characters should work"""
        data = "你好世界"
        assert deserialize(serialize(data)) == data
    
    def test_unicode_emoji(self):
        """Emoji should work"""
        data = "🎉🚀💻🌍"
        assert deserialize(serialize(data)) == data
    
    def test_unicode_mixed(self):
        """Mixed Unicode should work"""
        data = "Hello 世界 🌍 مرحبا"
        assert deserialize(serialize(data)) == data
    
    def test_special_chars_newline(self):
        """Newlines should work"""
        data = "line1\nline2\nline3"
        assert deserialize(serialize(data)) == data
    
    def test_special_chars_tab(self):
        """Tabs should work"""
        data = "col1\tcol2\tcol3"
        assert deserialize(serialize(data)) == data
    
    def test_special_chars_quotes(self):
        """Quotes should work"""
        data = 'He said "hello" and \'goodbye\''
        assert deserialize(serialize(data)) == data
    
    def test_special_chars_backslash(self):
        """Backslashes should work"""
        data = "path\\to\\file"
        assert deserialize(serialize(data)) == data
    
    def test_control_characters(self):
        """Control characters should work"""
        data = "text\r\n\t\b\f"
        result = deserialize(serialize(data))
        assert result == data


@pytest.mark.edge_case
class TestDeepNesting:
    """Test deeply nested structures"""
    
    def test_deep_dict_nesting(self):
        """Very deep dict nesting should work"""
        data = {"level": 0}
        current = data
        for i in range(1, 100):
            current["nested"] = {"level": i}
            current = current["nested"]
        
        result = deserialize(serialize(data))
        
        # Verify structure
        current = result
        for i in range(100):
            assert current["level"] == i
            if i < 99:
                current = current["nested"]
    
    def test_deep_list_nesting(self):
        """Very deep list nesting should work"""
        data = [0]
        current = data
        for i in range(1, 50):
            nested = [i]
            current.append(nested)
            current = nested
        
        result = deserialize(serialize(data))
        assert result[0] == 0


@pytest.mark.edge_case
class TestLargeCollections:
    """Test large collections"""
    
    def test_large_list(self):
        """Large list should work"""
        data = list(range(10000))
        result = deserialize(serialize(data))
        assert len(result) == 10000
        assert result[0] == 0
        assert result[-1] == 9999
    
    def test_large_dict(self):
        """Large dict should work"""
        data = {f"key_{i}": i for i in range(1000)}
        result = deserialize(serialize(data))
        assert len(result) == 1000
        assert result["key_0"] == 0
        assert result["key_999"] == 999
    
    def test_list_of_objects(self, simple_user_class):
        """Large list of objects should work"""
        users = [simple_user_class(f"User{i}", i) for i in range(100)]
        result = deserialize(serialize(users))
        
        assert len(result) == 100
        assert result[0].name == "User0"
        assert result[99].name == "User99"


@pytest.mark.edge_case
class TestBooleanEdgeCases:
    """Test boolean edge cases"""
    
    def test_true_false(self):
        """True and False should work"""
        assert deserialize(serialize(True)) is True
        assert deserialize(serialize(False)) is False
    
    def test_bool_in_collections(self):
        """Booleans in collections should work"""
        data = [True, False, True]
        assert deserialize(serialize(data)) == data
        
        data = {"a": True, "b": False}
        assert deserialize(serialize(data)) == data


@pytest.mark.edge_case
class TestMixedTypes:
    """Test mixed type scenarios"""
    
    def test_heterogeneous_list(self):
        """List with mixed types should work"""
        data = [1, "string", 3.14, True, None, {"nested": "dict"}, [1, 2, 3]]
        result = deserialize(serialize(data))
        assert result == data
    
    def test_heterogeneous_dict_values(self):
        """Dict with mixed value types should work"""
        data = {
            "int": 42,
            "str": "hello",
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        result = deserialize(serialize(data))
        assert result == data


@pytest.mark.edge_case
class TestObjectWithProperties:
    """Test objects with @property decorators"""
    
    def test_property_not_serialized(self):
        """@property should not be serialized"""
        class User(Serializable):
            def __init__(self, first: str, last: str):
                super().__init__()
                self.first = first
                self.last = last
            
            @property
            def full_name(self):
                return f"{self.first} {self.last}"
            
            def __eq__(self, other):
                return (isinstance(other, User) and 
                       self.first == other.first and 
                       self.last == other.last)
        
        user = User("Alice", "Smith")
        serialized = serialize(user)
        
        # Property should not be in serialized data
        assert 'full_name' not in serialized
        assert 'first' in serialized
        assert 'last' in serialized
        
        result = deserialize(serialized)
        assert result.full_name == "Alice Smith"


@pytest.mark.edge_case
class TestInheritance:
    """Test class inheritance scenarios"""
    
    def test_simple_inheritance(self):
        """Simple inheritance should work"""
        class Person(Serializable):
            def __init__(self, name: str):
                super().__init__()
                self.name = name
        
        class Employee(Person):
            def __init__(self, name: str, employee_id: int):
                super().__init__(name)
                self.employee_id = employee_id
            
            def __eq__(self, other):
                return (isinstance(other, Employee) and 
                       self.name == other.name and 
                       self.employee_id == other.employee_id)
        
        emp = Employee("Alice", 123)
        result = deserialize(serialize(emp))
        
        assert result == emp
        assert result.name == "Alice"
        assert result.employee_id == 123
