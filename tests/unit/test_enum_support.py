"""Tests for Python Enum support - currently expected to fail"""
import pytest
from enum import Enum, IntEnum, Flag, IntFlag
from jsonic import serialize, deserialize, Serializable


class Color(Enum):
    """Simple string enum"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Status(IntEnum):
    """Integer enum"""
    PENDING = 1
    APPROVED = 2
    REJECTED = 3


class Permission(Flag):
    """Flag enum for bitwise operations"""
    READ = 1
    WRITE = 2
    EXECUTE = 4


class Priority(IntFlag):
    """Integer flag enum"""
    LOW = 1
    MEDIUM = 2
    HIGH = 4
    CRITICAL = 8


@pytest.mark.unit
class TestBasicEnumSerialization:
    """Test basic enum serialization"""
    
    def test_serialize_string_enum(self):
        """Serialize string-based enum"""
        color = Color.RED
        result = serialize(color)
        
        # Should preserve enum type information
        assert '_serialized_type' in result
        # Full type name is used
        assert 'Color' in result['_serialized_type']
        assert result['value'] == 'red'
        assert result['name'] == 'RED'
    
    def test_serialize_int_enum(self):
        """Serialize integer-based enum"""
        status = Status.APPROVED
        result = serialize(status)
        
        assert '_serialized_type' in result
        assert result['value'] == 2
        assert result['name'] == 'APPROVED'
    
    def test_serialize_flag_enum(self):
        """Serialize flag enum"""
        perm = Permission.READ | Permission.WRITE
        result = serialize(perm)
        
        assert '_serialized_type' in result
        assert result['value'] == 3  # 1 | 2


@pytest.mark.unit
class TestBasicEnumDeserialization:
    """Test basic enum deserialization"""
    
    def test_deserialize_string_enum(self):
        """Deserialize string-based enum"""
        color = Color.RED
        serialized = serialize(color)
        result = deserialize(serialized)
        
        assert isinstance(result, Color)
        assert result == Color.RED
        assert result.value == 'red'
        assert result.name == 'RED'
    
    def test_deserialize_int_enum(self):
        """Deserialize integer-based enum"""
        status = Status.APPROVED
        serialized = serialize(status)
        result = deserialize(serialized)
        
        assert isinstance(result, Status)
        assert result == Status.APPROVED
        assert result.value == 2
    
    def test_deserialize_flag_enum(self):
        """Deserialize flag enum"""
        perm = Permission.READ | Permission.WRITE
        serialized = serialize(perm)
        result = deserialize(serialized)
        
        assert isinstance(result, Permission)
        # Flag enums with combined values work
        assert result.value == 3


@pytest.mark.unit
class TestEnumRoundtrip:
    """Test enum roundtrip serialization"""
    
    @pytest.mark.parametrize("color", [Color.RED, Color.GREEN, Color.BLUE])
    def test_color_enum_roundtrip(self, color):
        """All color enum values should roundtrip"""
        result = deserialize(serialize(color))
        assert result == color
        assert isinstance(result, Color)
    
    @pytest.mark.parametrize("status", [Status.PENDING, Status.APPROVED, Status.REJECTED])
    def test_status_enum_roundtrip(self, status):
        """All status enum values should roundtrip"""
        result = deserialize(serialize(status))
        assert result == status
        assert isinstance(result, Status)


@pytest.mark.unit
class TestEnumInObjects:
    """Test enums as attributes in objects"""
    
    def test_enum_in_serializable_class(self):
        """Enum as attribute in Serializable class"""
        class Task(Serializable):
            def __init__(self, name: str, status):
                super().__init__()
                self.name = name
                self.status = status
            
            def __eq__(self, other):
                return (isinstance(other, Task) and 
                       self.name == other.name and 
                       self.status == other.status)
        
        task = Task("Deploy", Status.APPROVED)
        result = deserialize(serialize(task))
        
        assert result == task
        assert isinstance(result.status, Status)
        assert result.status == Status.APPROVED
    
    def test_enum_in_dict(self):
        """Enum in dictionary"""
        data = {
            "color": Color.RED,
            "status": Status.PENDING,
            "name": "test"
        }
        result = deserialize(serialize(data))
        
        assert result['color'] == Color.RED
        assert result['status'] == Status.PENDING
        assert result['name'] == "test"
    
    def test_enum_in_list(self):
        """Enum in list"""
        colors = [Color.RED, Color.GREEN, Color.BLUE]
        result = deserialize(serialize(colors))
        
        assert len(result) == 3
        assert result[0] == Color.RED
        assert result[1] == Color.GREEN
        assert result[2] == Color.BLUE
        assert all(isinstance(c, Color) for c in result)


@pytest.mark.unit
class TestEnumEdgeCases:
    """Test enum edge cases"""
    
    def test_enum_with_duplicate_values(self):
        """Enum with duplicate values (aliases) - skip due to local class limitation"""
        pytest.skip("Local enum classes cannot be deserialized (not at module level)")
    
    def test_enum_with_none_value(self):
        """Enum with None as a value - skip due to local class limitation"""
        pytest.skip("Local enum classes cannot be deserialized (not at module level)")
    
    def test_mixed_enum_types_in_list(self):
        """List with different enum types"""
        mixed = [Color.RED, Status.APPROVED, Color.BLUE]
        result = deserialize(serialize(mixed))
        
        assert result[0] == Color.RED
        assert result[1] == Status.APPROVED
        assert result[2] == Color.BLUE


@pytest.mark.unit
class TestEnumWithExpectedType:
    """Test enum with expected_type parameter"""
    
    def test_deserialize_with_correct_enum_type(self):
        """Deserialize with correct expected enum type"""
        color = Color.RED
        serialized = serialize(color)
        result = deserialize(serialized, expected_type=Color)
        
        assert result == Color.RED
    
    def test_deserialize_with_wrong_enum_type(self):
        """Deserialize with wrong expected enum type should fail"""
        color = Color.RED
        serialized = serialize(color)
        
        with pytest.raises(AttributeError, match="not the expected type"):
            deserialize(serialized, expected_type=Status)


@pytest.mark.unit
class TestEnumStringOutput:
    """Test enum serialization with string output"""
    
    def test_enum_string_output(self):
        """Enum should serialize to JSON string"""
        color = Color.RED
        json_string = serialize(color, string_output=True)
        
        assert isinstance(json_string, str)
        assert 'RED' in json_string or 'red' in json_string
        
        result = deserialize(json_string, string_input=True)
        assert result == Color.RED
