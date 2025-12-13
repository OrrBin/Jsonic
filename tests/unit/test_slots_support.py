"""Tests for __slots__ serialization/deserialization support."""

from jsonic import serialize, deserialize, Serializable


class TestBasicSlots:
    """Test basic __slots__ serialization."""
    
    def test_simple_slots_class(self):
        """Simple class with __slots__."""
        class Point:
            __slots__ = ['x', 'y']
            
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        point = Point(10, 20)
        result = deserialize(serialize(point))
        
        assert result.x == 10
        assert result.y == 20
        assert isinstance(result, Point)
    
    def test_slots_with_single_attribute(self):
        """Class with single __slots__ attribute."""
        class Counter:
            __slots__ = ['count']
            
            def __init__(self, count):
                self.count = count
        
        counter = Counter(42)
        result = deserialize(serialize(counter))
        
        assert result.count == 42
        assert isinstance(result, Counter)
    
    def test_empty_slots(self):
        """Class with empty __slots__."""
        class Empty:
            __slots__ = []
            
            def __init__(self):
                pass
        
        empty = Empty()
        result = deserialize(serialize(empty))
        
        assert isinstance(result, Empty)


class TestSlotsWithSerializable:
    """Test __slots__ with Serializable classes."""
    
    def test_serializable_with_slots(self):
        """Serializable class using __slots__."""
        class User(Serializable):
            __slots__ = ['name', 'age']
            
            def __init__(self, name, age):
                super().__init__()
                self.name = name
                self.age = age
        
        user = User("Alice", 30)
        result = deserialize(serialize(user))
        
        assert result.name == "Alice"
        assert result.age == 30
        assert isinstance(result, User)
    
    def test_serializable_slots_with_transient(self):
        """Serializable with __slots__ and transient attributes."""
        class Account(Serializable):
            __slots__ = ['username', 'balance', '_temp']
            transient_attributes = ['_temp']
            
            def __init__(self, username, balance):
                super().__init__()
                self.username = username
                self.balance = balance
                # Don't set _temp in __init__ - it's transient
        
        account = Account("user1", 1000)
        # Manually set transient attribute after construction
        account._temp = "temporary"
        
        serialized = serialize(account)
        
        # _temp should not be in serialized data
        assert '_temp' not in serialized
        
        result = deserialize(serialized)
        
        assert result.username == "user1"
        assert result.balance == 1000
        # _temp was not serialized and not set during deserialization
        try:
            _ = result._temp
            assert False, "_temp should not be set"
        except AttributeError:
            pass  # Expected - transient attribute not set


class TestSlotsWithComplexTypes:
    """Test __slots__ with complex attribute types."""
    
    def test_slots_with_list(self):
        """__slots__ class with list attribute."""
        class Container:
            __slots__ = ['items']
            
            def __init__(self, items):
                self.items = items
        
        container = Container([1, 2, 3, 4, 5])
        result = deserialize(serialize(container))
        
        assert result.items == [1, 2, 3, 4, 5]
    
    def test_slots_with_dict(self):
        """__slots__ class with dict attribute."""
        class Config:
            __slots__ = ['settings']
            
            def __init__(self, settings):
                self.settings = settings
        
        config = Config({"debug": True, "timeout": 30})
        result = deserialize(serialize(config))
        
        assert result.settings == {"debug": True, "timeout": 30}
    
    def test_slots_with_tuple(self):
        """__slots__ class with tuple attribute."""
        class Coordinate:
            __slots__ = ['position']
            
            def __init__(self, position):
                self.position = position
        
        coord = Coordinate((10.5, 20.3, 30.1))
        result = deserialize(serialize(coord))
        
        assert result.position == (10.5, 20.3, 30.1)
        assert isinstance(result.position, tuple)
    
    def test_slots_with_set(self):
        """__slots__ class with set attribute."""
        class TaggedItem:
            __slots__ = ['tags']
            
            def __init__(self, tags):
                self.tags = tags
        
        item = TaggedItem({"python", "json", "serialization"})
        result = deserialize(serialize(item))
        
        assert result.tags == {"python", "json", "serialization"}
        assert isinstance(result.tags, set)


class TestSlotsWithNestedObjects:
    """Test __slots__ with nested objects."""
    
    def test_slots_containing_regular_object(self):
        """__slots__ class containing regular class instance."""
        class Inner:
            def __init__(self, value):
                self.value = value
        
        class Outer:
            __slots__ = ['inner']
            
            def __init__(self, inner):
                self.inner = inner
        
        outer = Outer(Inner(42))
        result = deserialize(serialize(outer))
        
        assert result.inner.value == 42
    
    def test_slots_containing_slots(self):
        """__slots__ class containing another __slots__ class."""
        class Inner:
            __slots__ = ['value']
            
            def __init__(self, value):
                self.value = value
        
        class Outer:
            __slots__ = ['inner']
            
            def __init__(self, inner):
                self.inner = inner
        
        outer = Outer(Inner(42))
        result = deserialize(serialize(outer))
        
        assert result.inner.value == 42


class TestSlotsEdgeCases:
    """Test edge cases for __slots__ support."""
    
    def test_slots_with_none_value(self):
        """__slots__ with None value."""
        class Optional:
            __slots__ = ['value']
            
            def __init__(self, value=None):
                self.value = value
        
        opt = Optional(None)
        result = deserialize(serialize(opt))
        
        assert result.value is None
    
    def test_slots_with_default_values(self):
        """__slots__ with default parameter values."""
        class WithDefaults:
            __slots__ = ['x', 'y']
            
            def __init__(self, x=0, y=0):
                self.x = x
                self.y = y
        
        obj = WithDefaults(5)
        result = deserialize(serialize(obj))
        
        assert result.x == 5
        assert result.y == 0
    
    def test_slots_string_format(self):
        """__slots__ defined as string instead of list."""
        class Single:
            __slots__ = 'value'  # Single slot as string
            
            def __init__(self, value):
                self.value = value
        
        single = Single(100)
        result = deserialize(serialize(single))
        
        assert result.value == 100
    
    def test_slots_tuple_format(self):
        """__slots__ defined as tuple."""
        class Point:
            __slots__ = ('x', 'y')  # Tuple format
            
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        point = Point(3, 4)
        result = deserialize(serialize(point))
        
        assert result.x == 3
        assert result.y == 4


class TestSlotsInheritance:
    """Test __slots__ with inheritance."""
    
    def test_slots_inheritance(self):
        """Inheritance with __slots__."""
        class Base:
            __slots__ = ['base_attr']
            
            def __init__(self, base_attr):
                self.base_attr = base_attr
        
        class Derived(Base):
            __slots__ = ['derived_attr']
            
            def __init__(self, base_attr, derived_attr):
                super().__init__(base_attr)
                self.derived_attr = derived_attr
        
        derived = Derived("base", "derived")
        result = deserialize(serialize(derived))
        
        assert result.base_attr == "base"
        assert result.derived_attr == "derived"
