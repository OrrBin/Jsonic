"""Thread safety tests for concurrent serialization/deserialization"""
import pytest
import threading
from datetime import datetime
from jsonic import serialize, deserialize, Serializable, register_jsonic_type


@pytest.mark.unit
class TestConcurrentSerialization:
    """Test serialization from multiple threads"""
    
    def test_concurrent_serialize_same_object(self, simple_user_class):
        """Multiple threads serializing the same object"""
        user = simple_user_class("Alice", 30)
        results = []
        errors = []
        
        def serialize_task():
            try:
                result = serialize(user)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=serialize_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        # All results should be identical
        for result in results:
            assert result['name'] == "Alice"
            assert result['age'] == 30
    
    def test_concurrent_serialize_different_objects(self, simple_user_class):
        """Multiple threads serializing different objects"""
        results = []
        errors = []
        
        def serialize_task(name, age):
            try:
                user = simple_user_class(name, age)
                result = serialize(user)
                results.append((name, result))
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=serialize_task, args=(f"User{i}", i))
            for i in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20
        
        # Verify each result matches its input
        result_dict = {name: result for name, result in results}
        for i in range(20):
            name = f"User{i}"
            assert result_dict[name]['name'] == name
            assert result_dict[name]['age'] == i


@pytest.mark.unit
class TestConcurrentDeserialization:
    """Test deserialization from multiple threads"""
    
    def test_concurrent_deserialize_same_data(self, simple_user_class):
        """Multiple threads deserializing the same data"""
        user = simple_user_class("Alice", 30)
        serialized = serialize(user)
        results = []
        errors = []
        
        def deserialize_task():
            try:
                result = deserialize(serialized)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=deserialize_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        for result in results:
            assert result.name == "Alice"
            assert result.age == 30
    
    def test_concurrent_deserialize_different_data(self, simple_user_class):
        """Multiple threads deserializing different data"""
        serialized_data = [
            serialize(simple_user_class(f"User{i}", i))
            for i in range(20)
        ]
        results = []
        errors = []
        
        def deserialize_task(data, index):
            try:
                result = deserialize(data)
                results.append((index, result))
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=deserialize_task, args=(data, i))
            for i, data in enumerate(serialized_data)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20
        
        # Verify each result
        result_dict = {idx: result for idx, result in results}
        for i in range(20):
            assert result_dict[i].name == f"User{i}"
            assert result_dict[i].age == i


@pytest.mark.unit
class TestConcurrentRoundtrip:
    """Test full serialize/deserialize cycle from multiple threads"""
    
    def test_concurrent_roundtrip(self, simple_user_class):
        """Multiple threads doing full roundtrip"""
        results = []
        errors = []
        
        def roundtrip_task(name, age):
            try:
                user = simple_user_class(name, age)
                serialized = serialize(user)
                deserialized = deserialize(serialized)
                results.append((name, deserialized))
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=roundtrip_task, args=(f"User{i}", i))
            for i in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50
        
        result_dict = {name: user for name, user in results}
        for i in range(50):
            name = f"User{i}"
            assert result_dict[name].name == name
            assert result_dict[name].age == i


@pytest.mark.unit
class TestConcurrentRegistration:
    """Test concurrent type registration"""
    
    def test_concurrent_register_same_type(self):
        """Multiple threads registering the same type"""
        errors = []
        
        class TestClass:
            def __init__(self, value):
                self.value = value
        
        def register_task():
            try:
                register_jsonic_type(TestClass)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=register_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not error - last registration wins
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify it works
        obj = TestClass(42)
        result = deserialize(serialize(obj))
        assert result.value == 42
    
    def test_concurrent_register_different_types(self):
        """Multiple threads registering different types"""
        errors = []
        
        def register_task(i):
            try:
                # Create unique class for each thread
                cls = type(f'TestClass{i}', (), {
                    '__init__': lambda self, value: setattr(self, 'value', value)
                })
                register_jsonic_type(cls)
                
                # Test it works
                obj = cls(i)
                result = deserialize(serialize(obj))
                assert result.value == i
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=register_task, args=(i,))
            for i in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"


@pytest.mark.unit
class TestConcurrentCustomSerializers:
    """Test concurrent custom serializer registration"""
    
    def test_concurrent_custom_serializer_registration(self):
        """Multiple threads registering custom serializers"""
        from jsonic import jsonic_serializer, jsonic_deserializer
        errors = []
        
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        def register_serializer_task():
            try:
                @jsonic_serializer(serialized_type=Point)
                def serialize_point(p):
                    return {'x': p.x, 'y': p.y}
                
                @jsonic_deserializer(deserialized_type_name=Point)
                def deserialize_point(data):
                    return Point(data['x'], data['y'])
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=register_serializer_task) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not error - last registration wins
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify it works
        point = Point(10, 20)
        result = deserialize(serialize(point))
        assert result.x == 10
        assert result.y == 20


@pytest.mark.unit
class TestConcurrentMixedOperations:
    """Test mixed operations from multiple threads"""
    
    def test_concurrent_mixed_operations(self, simple_user_class):
        """Mix of serialize, deserialize, and register operations"""
        results = []
        errors = []
        
        def serialize_task(i):
            try:
                user = simple_user_class(f"User{i}", i)
                result = serialize(user)
                results.append(('serialize', i, result))
            except Exception as e:
                errors.append(('serialize', e))
        
        def deserialize_task(i):
            try:
                user = simple_user_class(f"User{i}", i)
                serialized = serialize(user)
                result = deserialize(serialized)
                results.append(('deserialize', i, result))
            except Exception as e:
                errors.append(('deserialize', e))
        
        def register_task(i):
            try:
                cls = type(f'DynamicClass{i}', (), {
                    '__init__': lambda self, val: setattr(self, 'val', val)
                })
                register_jsonic_type(cls)
                results.append(('register', i, cls))
            except Exception as e:
                errors.append(('register', e))
        
        threads = []
        for i in range(30):
            if i % 3 == 0:
                threads.append(threading.Thread(target=serialize_task, args=(i,)))
            elif i % 3 == 1:
                threads.append(threading.Thread(target=deserialize_task, args=(i,)))
            else:
                threads.append(threading.Thread(target=register_task, args=(i,)))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 30


@pytest.mark.unit
class TestConcurrentWithDatetime:
    """Test concurrent operations with datetime objects"""
    
    def test_concurrent_datetime_serialization(self):
        """Multiple threads serializing datetime objects"""
        results = []
        errors = []
        
        def serialize_datetime_task(i):
            try:
                dt = datetime(2020, 1, 1, i % 24, i % 60, i % 60)
                result = serialize(dt)
                results.append((i, result))
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=serialize_datetime_task, args=(i,))
            for i in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 100


@pytest.mark.unit
class TestConcurrentStressTest:
    """Stress test with high concurrency"""
    
    def test_high_concurrency_stress(self, simple_user_class):
        """Stress test with 100 concurrent threads"""
        results = []
        errors = []
        
        def stress_task(i):
            try:
                # Create, serialize, deserialize
                user = simple_user_class(f"User{i}", i % 100)
                serialized = serialize(user)
                deserialized = deserialize(serialized)
                
                # Verify
                assert deserialized.name == f"User{i}"
                assert deserialized.age == i % 100
                results.append(i)
            except Exception as e:
                errors.append((i, e))
        
        threads = [
            threading.Thread(target=stress_task, args=(i,))
            for i in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 100
