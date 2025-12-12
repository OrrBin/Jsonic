"""Unit tests for custom serializers and deserializers"""
import pytest
from jsonic import serialize, deserialize, jsonic_serializer, jsonic_deserializer


@pytest.mark.unit
class TestCustomSerializers:
    """Test @jsonic_serializer decorator"""
    
    def test_custom_serializer_basic(self):
        """Custom serializer should be used"""
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y
        
        @jsonic_serializer(serialized_type=Point)
        def serialize_point(point):
            return {'x': point.x, 'y': point.y}
        
        point = Point(10, 20)
        result = serialize(point)
        
        assert result['x'] == 10
        assert result['y'] == 20
        assert result['_serialized_type'] == 'Point'
    
    def test_custom_serializer_with_transformation(self):
        """Custom serializer can transform data"""
        class Temperature:
            def __init__(self, celsius: float):
                self.celsius = celsius
        
        @jsonic_serializer(serialized_type=Temperature)
        def serialize_temp(temp):
            return {
                'celsius': temp.celsius,
                'fahrenheit': temp.celsius * 9/5 + 32
            }
        
        temp = Temperature(100)
        result = serialize(temp)
        
        assert result['celsius'] == 100
        assert result['fahrenheit'] == 212


@pytest.mark.unit
class TestCustomDeserializers:
    """Test @jsonic_deserializer decorator"""
    
    def test_custom_deserializer_basic(self):
        """Custom deserializer should be used"""
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y
            
            def __eq__(self, other):
                return isinstance(other, Point) and self.x == other.x and self.y == other.y
        
        @jsonic_serializer(serialized_type=Point)
        def serialize_point(point):
            return {'x': point.x, 'y': point.y}
        
        @jsonic_deserializer(deserialized_type_name=Point)
        def deserialize_point(data):
            return Point(data['x'], data['y'])
        
        point = Point(10, 20)
        result = deserialize(serialize(point))
        
        assert result == point
        assert result.x == 10
        assert result.y == 20


@pytest.mark.unit
class TestCustomSerializerDeserializerPair:
    """Test custom serializer/deserializer pairs"""
    
    def test_roundtrip_with_custom_pair(self):
        """Custom serializer/deserializer pair should roundtrip"""
        class Color:
            def __init__(self, r: int, g: int, b: int):
                self.r = r
                self.g = g
                self.b = b
            
            def __eq__(self, other):
                return (isinstance(other, Color) and 
                       self.r == other.r and 
                       self.g == other.g and 
                       self.b == other.b)
        
        @jsonic_serializer(serialized_type=Color)
        def serialize_color(color):
            return {'hex': f'#{color.r:02x}{color.g:02x}{color.b:02x}'}
        
        @jsonic_deserializer(deserialized_type_name=Color)
        def deserialize_color(data):
            hex_str = data['hex'][1:]  # Remove #
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return Color(r, g, b)
        
        color = Color(255, 128, 64)
        result = deserialize(serialize(color))
        
        assert result == color
    
    def test_custom_serializer_in_nested_structure(self):
        """Custom serializers should work in nested structures"""
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y
            
            def __eq__(self, other):
                return isinstance(other, Point) and self.x == other.x and self.y == other.y
        
        @jsonic_serializer(serialized_type=Point)
        def serialize_point(point):
            return {'x': point.x, 'y': point.y}
        
        @jsonic_deserializer(deserialized_type_name=Point)
        def deserialize_point(data):
            return Point(data['x'], data['y'])
        
        data = {
            'points': [Point(1, 2), Point(3, 4)],
            'origin': Point(0, 0)
        }
        
        result = deserialize(serialize(data))
        
        assert result['points'][0] == Point(1, 2)
        assert result['origin'] == Point(0, 0)


@pytest.mark.unit
class TestCustomSerializerOverride:
    """Test overriding custom serializers"""
    
    def test_last_serializer_wins(self):
        """Last registered serializer should be used"""
        class Value:
            def __init__(self, val: int):
                self.val = val
        
        @jsonic_serializer(serialized_type=Value)
        def serialize_v1(value):
            return {'value': value.val, 'version': 1}
        
        obj = Value(42)
        result1 = serialize(obj)
        assert result1['version'] == 1
        
        @jsonic_serializer(serialized_type=Value)
        def serialize_v2(value):
            return {'value': value.val, 'version': 2}
        
        result2 = serialize(obj)
        assert result2['version'] == 2
