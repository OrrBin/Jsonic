"""Integration tests for type resolver system with existing Jsonic features."""

import pytest
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum, IntEnum
from jsonic import Serializable, serialize, deserialize, register_jsonic_type


class TestMixedSerializableAndDataclass:
    """Test mixing Serializable and dataclass."""
    
    def test_serializable_containing_dataclass(self):
        """Serializable class containing dataclass."""
        @dataclass
        class Address:
            street: str
            city: str
        
        class Person(Serializable):
            def __init__(self, name: str, address: Address):
                super().__init__()
                self.name = name
                self.address = address
        
        person = Person("Alice", Address("123 Main", "NYC"))
        result = deserialize(serialize(person))
        
        assert result.name == "Alice"
        assert result.address.street == "123 Main"
    
    def test_dataclass_containing_serializable(self):
        """Dataclass containing Serializable class."""
        class Credentials(Serializable):
            def __init__(self, username: str, token: str):
                super().__init__()
                self.username = username
                self.token = token
        
        @dataclass
        class User:
            name: str
            creds: Credentials
        
        user = User("Alice", Credentials("alice", "secret123"))
        result = deserialize(serialize(user), expected_type=User)
        
        assert result.name == "Alice"
        assert result.creds.username == "alice"


class TestMixedRegisteredAndDataclass:
    """Test mixing registered types and dataclass."""
    
    def test_registered_type_containing_dataclass(self):
        """Registered type containing dataclass."""
        @dataclass
        class Config:
            host: str
            port: int
        
        class Service:
            def __init__(self, name: str, config: Config):
                self.name = name
                self.config = config
        
        register_jsonic_type(Service)
        
        service = Service("API", Config("localhost", 8080))
        result = deserialize(serialize(service))
        
        assert result.name == "API"
        assert result.config.host == "localhost"
    
    def test_dataclass_containing_registered_type(self):
        """Dataclass containing registered type."""
        class Database:
            def __init__(self, host: str, port: int):
                self.host = host
                self.port = port
        
        register_jsonic_type(Database)
        
        @dataclass
        class AppConfig:
            name: str
            database: Database
        
        config = AppConfig("MyApp", Database("db.example.com", 5432))
        result = deserialize(serialize(config), expected_type=AppConfig)
        
        assert result.name == "MyApp"
        assert result.database.host == "db.example.com"


class TestDataclassWithEnums:
    """Test dataclass with enum support."""
    
    def test_dataclass_with_enum_field(self):
        """Dataclass containing enum."""
        class Status(Enum):
            PENDING = "pending"
            APPROVED = "approved"
            REJECTED = "rejected"
        
        @dataclass
        class Task:
            name: str
            status: Status
        
        task = Task("Deploy", Status.APPROVED)
        result = deserialize(serialize(task), expected_type=Task)
        
        assert result.name == "Deploy"
        assert result.status == Status.APPROVED
        assert isinstance(result.status, Status)
    
    def test_dataclass_with_int_enum(self):
        """Dataclass with IntEnum."""
        class Priority(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
        
        @dataclass
        class Issue:
            title: str
            priority: Priority
        
        issue = Issue("Bug fix", Priority.HIGH)
        result = deserialize(serialize(issue), expected_type=Issue)
        
        assert result.priority == Priority.HIGH
        assert isinstance(result.priority, Priority)


class TestDataclassWithDatetime:
    """Test dataclass with datetime support."""
    
    def test_dataclass_with_datetime(self):
        """Dataclass containing datetime."""
        @dataclass
        class Event:
            name: str
            timestamp: datetime
        
        event = Event("Meeting", datetime(2025, 12, 13, 10, 30))
        result = deserialize(serialize(event), expected_type=Event)
        
        assert result.name == "Meeting"
        assert result.timestamp == datetime(2025, 12, 13, 10, 30)


class TestComplexIntegration:
    """Test complex integration scenarios."""
    
    def test_all_styles_mixed(self):
        """Mix Serializable, dataclass, registered, enum, datetime."""
        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
        
        @dataclass
        class Metadata:
            created: datetime
            status: Status
        
        class Config:
            def __init__(self, timeout: int):
                self.timeout = timeout
        
        register_jsonic_type(Config)
        
        class Application(Serializable):
            def __init__(self, name: str, metadata: Metadata, config: Config):
                super().__init__()
                self.name = name
                self.metadata = metadata
                self.config = config
        
        app = Application(
            "MyApp",
            Metadata(datetime(2025, 1, 1), Status.ACTIVE),
            Config(30)
        )
        result = deserialize(serialize(app))
        
        assert result.name == "MyApp"
        assert result.metadata.created == datetime(2025, 1, 1)
        assert result.metadata.status == Status.ACTIVE
        assert result.config.timeout == 30


class TestBackwardCompatibility:
    """Test that new features don't break existing functionality."""
    
    def test_existing_serializable_still_works(self):
        """Existing Serializable classes work unchanged."""
        class OldStyle(Serializable):
            def __init__(self, value: str):
                super().__init__()
                self.value = value
        
        obj = OldStyle("test")
        result = deserialize(serialize(obj))
        assert result.value == "test"
    
    def test_existing_registered_type_still_works(self):
        """Existing registered types work unchanged."""
        class External:
            def __init__(self, data: str):
                self.data = data
        
        register_jsonic_type(External)
        
        obj = External("test")
        result = deserialize(serialize(obj))
        assert result.data == "test"
    
    def test_transient_attributes_still_work(self):
        """Transient attributes in Serializable still work."""
        class WithTransient(Serializable):
            transient_attributes = ['temp']
            
            def __init__(self, value: str, temp: str = "default"):
                super().__init__()
                self.value = value
                self.temp = temp
        
        obj = WithTransient("keep", "discard")
        result = deserialize(serialize(obj))
        
        assert result.value == "keep"
        assert not hasattr(result, 'temp') or result.temp == "default"


class TestPriorityResolution:
    """Test resolver priority system."""
    
    def test_serializable_takes_priority_over_dataclass(self):
        """When class is both Serializable and dataclass, Serializable wins."""
        @dataclass
        class Hybrid(Serializable):
            value: str
            
            def __init__(self, value: str):
                super().__init__()
                self.value = value
        
        obj = Hybrid("test")
        serialized = serialize(obj)
        
        # Should use Serializable serialization
        assert '_serialized_type' in serialized
        
        result = deserialize(serialized)
        assert result.value == "test"
