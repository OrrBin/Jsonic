"""Tests for cross-feature integration between dataclasses, type hints, tuples, sets, and __slots__."""

from dataclasses import dataclass
from typing import Set, Tuple, Optional, List, Dict
from jsonic import serialize, deserialize, Serializable


class TestDataclassWithTuples:
    """Test dataclasses containing tuples."""
    
    def test_dataclass_with_tuple_of_dataclasses(self):
        """Dataclass containing tuple of other dataclasses."""
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
        assert len(result.points) == 2
        assert isinstance(result.points[0], Point)
        assert result.points[0].x == 0
        assert result.points[1].y == 10


class TestDataclassWithSets:
    """Test dataclasses containing sets."""
    
    def test_dataclass_with_set_of_dataclasses(self):
        """Dataclass containing set - but dataclasses aren't hashable by default."""
        @dataclass
        class Container:
            tags: Set[str]
            counts: Set[int]
        
        container = Container({"python", "json"}, {1, 2, 3})
        result = deserialize(serialize(container), expected_type=Container)
        
        assert result.tags == {"python", "json"}
        assert result.counts == {1, 2, 3}


class TestSerializableWithDataclass:
    """Test Serializable classes containing dataclass instances."""
    
    def test_serializable_containing_dataclass(self):
        """Serializable class with dataclass attribute."""
        @dataclass
        class Address:
            street: str
            city: str
        
        class Person(Serializable):
            def __init__(self, name: str, address: Address):
                super().__init__()
                self.name = name
                self.address = address
        
        person = Person("Alice", Address("123 Main St", "NYC"))
        result = deserialize(serialize(person))
        
        assert result.name == "Alice"
        assert isinstance(result.address, Address)
        assert result.address.city == "NYC"
    
    def test_dataclass_containing_serializable(self):
        """Dataclass with Serializable attribute."""
        class Config(Serializable):
            def __init__(self, debug: bool):
                super().__init__()
                self.debug = debug
        
        @dataclass
        class App:
            name: str
            config: Config
        
        app = App("MyApp", Config(True))
        result = deserialize(serialize(app), expected_type=App)
        
        assert result.name == "MyApp"
        assert isinstance(result.config, Config)
        assert result.config.debug is True


class TestSetsContainingTuples:
    """Test sets containing tuples (tuples are hashable)."""
    
    def test_set_of_tuples(self):
        """Set containing tuple elements."""
        data = {(1, 2), (3, 4), (5, 6)}
        result = deserialize(serialize(data))
        
        assert result == {(1, 2), (3, 4), (5, 6)}
        assert isinstance(result, set)
        assert all(isinstance(item, tuple) for item in result)
    
    def test_dataclass_with_set_of_tuples(self):
        """Dataclass with set of tuples."""
        @dataclass
        class Coordinates:
            points: Set[Tuple[int, int]]
        
        coords = Coordinates({(0, 0), (1, 1), (2, 2)})
        result = deserialize(serialize(coords), expected_type=Coordinates)
        
        assert result.points == {(0, 0), (1, 1), (2, 2)}
        assert isinstance(result.points, set)
        assert all(isinstance(p, tuple) for p in result.points)


class TestTuplesContainingSets:
    """Test tuples containing sets (sets aren't hashable, but can be in tuples)."""
    
    def test_tuple_of_sets(self):
        """Tuple containing set elements."""
        data = ({1, 2}, {3, 4}, {5, 6})
        result = deserialize(serialize(data))
        
        assert result == ({1, 2}, {3, 4}, {5, 6})
        assert isinstance(result, tuple)
        assert all(isinstance(item, set) for item in result)
    
    def test_dataclass_with_tuple_of_sets(self):
        """Dataclass with tuple of sets."""
        @dataclass
        class Groups:
            data: Tuple[Set[int], Set[int]]
        
        groups = Groups(({1, 2, 3}, {4, 5, 6}))
        result = deserialize(serialize(groups), expected_type=Groups)
        
        assert result.data == ({1, 2, 3}, {4, 5, 6})
        assert isinstance(result.data, tuple)
        assert all(isinstance(s, set) for s in result.data)


class TestSlotsWithTypeHints:
    """Test __slots__ classes with type hints."""
    
    def test_slots_with_type_hints(self):
        """Class with both __slots__ and type hints."""
        class Point:
            __slots__ = ['x', 'y']
            
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y
        
        point = Point(10, 20)
        result = deserialize(serialize(point))
        
        assert result.x == 10
        assert result.y == 20
    
    def test_slots_with_complex_type_hints(self):
        """__slots__ with tuple and set type hints."""
        class Container:
            __slots__ = ['coords', 'tags']
            
            def __init__(self, coords: Tuple[int, int], tags: Set[str]):
                self.coords = coords
                self.tags = tags
        
        container = Container((5, 10), {"python", "test"})
        result = deserialize(serialize(container))
        
        assert result.coords == (5, 10)
        assert isinstance(result.coords, tuple)
        assert result.tags == {"python", "test"}
        assert isinstance(result.tags, set)


class TestSlotsWithDataclass:
    """Test __slots__ with dataclass fields."""
    
    def test_slots_containing_dataclass(self):
        """__slots__ class containing dataclass instance."""
        @dataclass
        class Config:
            value: int
        
        class App:
            __slots__ = ['name', 'config']
            
            def __init__(self, name: str, config: Config):
                self.name = name
                self.config = config
        
        app = App("MyApp", Config(42))
        result = deserialize(serialize(app))
        
        assert result.name == "MyApp"
        assert isinstance(result.config, Config)
        assert result.config.value == 42


class TestNestedComplexStructures:
    """Test deeply nested combinations of features."""
    
    def test_dataclass_with_tuple_of_sets(self):
        """Dataclass containing tuple of sets."""
        @dataclass
        class Data:
            groups: Tuple[Set[int], Set[str]]
        
        data = Data(({1, 2, 3}, {"a", "b", "c"}))
        result = deserialize(serialize(data), expected_type=Data)
        
        assert isinstance(result.groups, tuple)
        assert result.groups[0] == {1, 2, 3}
        assert result.groups[1] == {"a", "b", "c"}
    
    def test_serializable_with_set_of_tuples(self):
        """Serializable containing set of tuples."""
        class Graph(Serializable):
            def __init__(self, edges: Set[Tuple[int, int]]):
                super().__init__()
                self.edges = edges
        
        graph = Graph({(1, 2), (2, 3), (3, 4)})
        result = deserialize(serialize(graph))
        
        assert result.edges == {(1, 2), (2, 3), (3, 4)}
        assert isinstance(result.edges, set)
    
    def test_slots_with_tuple_of_dataclasses(self):
        """__slots__ class with tuple of dataclasses."""
        @dataclass
        class Point:
            x: int
            y: int
        
        class Line:
            __slots__ = ['start', 'end']
            
            def __init__(self, start: Point, end: Point):
                self.start = start
                self.end = end
        
        line = Line(Point(0, 0), Point(10, 10))
        result = deserialize(serialize(line))
        
        assert isinstance(result.start, Point)
        assert isinstance(result.end, Point)
        assert result.start.x == 0
        assert result.end.y == 10
    
    def test_triple_nesting(self):
        """Dataclass with set of tuples of dataclasses."""
        @dataclass
        class Item:
            value: int
        
        @dataclass
        class Container:
            # Can't actually have set of tuples of dataclasses (not hashable)
            # But can have list of tuples of dataclasses
            data: List[Tuple[Item, Item]]
        
        container = Container([(Item(1), Item(2)), (Item(3), Item(4))])
        result = deserialize(serialize(container), expected_type=Container)
        
        assert len(result.data) == 2
        assert isinstance(result.data[0], tuple)
        assert isinstance(result.data[0][0], Item)
        assert result.data[0][0].value == 1


class TestMixedSerializableAndSlots:
    """Test Serializable classes with __slots__."""
    
    def test_serializable_with_slots_and_tuples(self):
        """Serializable with __slots__ containing tuples."""
        class Point(Serializable):
            __slots__ = ['coords']
            
            def __init__(self, coords: Tuple[int, int]):
                super().__init__()
                self.coords = coords
        
        point = Point((5, 10))
        result = deserialize(serialize(point))
        
        assert result.coords == (5, 10)
        assert isinstance(result.coords, tuple)
    
    def test_serializable_with_slots_and_sets(self):
        """Serializable with __slots__ containing sets."""
        class Tagged(Serializable):
            __slots__ = ['name', 'tags']
            
            def __init__(self, name: str, tags: Set[str]):
                super().__init__()
                self.name = name
                self.tags = tags
        
        tagged = Tagged("item", {"tag1", "tag2"})
        result = deserialize(serialize(tagged))
        
        assert result.name == "item"
        assert result.tags == {"tag1", "tag2"}
        assert isinstance(result.tags, set)


class TestComplexTypeHints:
    """Test complex type hint combinations."""
    
    def test_optional_tuple(self):
        """Optional tuple type hint."""
        @dataclass
        class Data:
            coords: Optional[Tuple[int, int]] = None
        
        data1 = Data((5, 10))
        result1 = deserialize(serialize(data1), expected_type=Data)
        assert result1.coords == (5, 10)
        
        data2 = Data(None)
        result2 = deserialize(serialize(data2), expected_type=Data)
        assert result2.coords is None
    
    def test_optional_set(self):
        """Optional set type hint."""
        @dataclass
        class Data:
            tags: Optional[Set[str]] = None
        
        data1 = Data({"a", "b"})
        result1 = deserialize(serialize(data1), expected_type=Data)
        assert result1.tags == {"a", "b"}
        
        data2 = Data(None)
        result2 = deserialize(serialize(data2), expected_type=Data)
        assert result2.tags is None
    
    def test_dict_with_tuple_keys_and_set_values(self):
        """Dict with tuple keys and set values."""
        # Note: JSON doesn't support tuple keys, so this will fail
        # But we can test dict with string keys and set values
        @dataclass
        class Mapping:
            data: Dict[str, Set[int]]
        
        mapping = Mapping({"a": {1, 2}, "b": {3, 4}})
        result = deserialize(serialize(mapping), expected_type=Mapping)
        
        assert result.data == {"a": {1, 2}, "b": {3, 4}}
        assert all(isinstance(v, set) for v in result.data.values())
    
    def test_list_of_tuples_of_sets(self):
        """List of tuples of sets."""
        @dataclass
        class Complex:
            data: List[Tuple[Set[int], Set[str]]]
        
        complex_data = Complex([({1, 2}, {"a", "b"}), ({3, 4}, {"c", "d"})])
        result = deserialize(serialize(complex_data), expected_type=Complex)
        
        assert len(result.data) == 2
        assert isinstance(result.data[0], tuple)
        assert isinstance(result.data[0][0], set)
        assert result.data[0][0] == {1, 2}
        assert result.data[0][1] == {"a", "b"}


class TestInheritanceWithNewFeatures:
    """Test inheritance scenarios with new features."""
    
    def test_dataclass_inheritance_with_tuples(self):
        """Dataclass inheritance with tuple fields."""
        @dataclass
        class Base:
            coords: Tuple[int, int]
        
        @dataclass
        class Derived(Base):
            name: str
        
        derived = Derived((5, 10), "point")
        result = deserialize(serialize(derived), expected_type=Derived)
        
        assert result.coords == (5, 10)
        assert isinstance(result.coords, tuple)
        assert result.name == "point"
    
    def test_serializable_inheritance_with_sets(self):
        """Serializable inheritance with set fields."""
        class Base(Serializable):
            def __init__(self, tags: Set[str]):
                super().__init__()
                self.tags = tags
        
        class Derived(Base):
            def __init__(self, tags: Set[str], name: str):
                super().__init__(tags)
                self.name = name
        
        derived = Derived({"tag1", "tag2"}, "item")
        result = deserialize(serialize(derived))
        
        assert result.tags == {"tag1", "tag2"}
        assert isinstance(result.tags, set)
        assert result.name == "item"


class TestEmptyCollectionsInComplexTypes:
    """Test empty tuples and sets in complex structures."""
    
    def test_dataclass_with_empty_tuple(self):
        """Dataclass with empty tuple."""
        @dataclass
        class Data:
            items: Tuple[()]
        
        data = Data(())
        result = deserialize(serialize(data), expected_type=Data)
        
        assert result.items == ()
        assert isinstance(result.items, tuple)
    
    def test_dataclass_with_empty_set(self):
        """Dataclass with empty set."""
        @dataclass
        class Data:
            tags: Set[str]
        
        data = Data(set())
        result = deserialize(serialize(data), expected_type=Data)
        
        assert result.tags == set()
        assert isinstance(result.tags, set)
    
    def test_tuple_with_empty_sets(self):
        """Tuple containing empty sets."""
        data = (set(), {1, 2}, set())
        result = deserialize(serialize(data))
        
        assert result == (set(), {1, 2}, set())
        assert isinstance(result, tuple)
        assert all(isinstance(item, set) for item in result)


class TestNoneInComplexScenarios:
    """Test None values in complex type combinations."""
    
    def test_tuple_with_none_in_dataclass(self):
        """Dataclass with tuple containing None."""
        @dataclass
        class Data:
            values: Tuple[int, None, str]
        
        data = Data((1, None, "test"))
        result = deserialize(serialize(data), expected_type=Data)
        
        assert result.values == (1, None, "test")
        assert isinstance(result.values, tuple)
    
    def test_set_with_none_in_slots(self):
        """__slots__ class with set containing None."""
        class Container:
            __slots__ = ['items']
            
            def __init__(self, items: Set):
                self.items = items
        
        container = Container({None, 1, 2})
        result = deserialize(serialize(container))
        
        assert result.items == {None, 1, 2}
        assert isinstance(result.items, set)
