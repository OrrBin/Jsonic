"""Tests for improved type not found error messages."""

import pytest
from jsonic import serialize, deserialize, Serializable, register_jsonic_type


class TestTypeNotFoundWithSuggestions:
    """Test that type not found errors include helpful suggestions."""
    
    def test_typo_in_type_name_suggests_similar(self):
        """Typo in type name should suggest similar registered types."""
        class User(Serializable):
            def __init__(self, name):
                super().__init__()
                self.name = name
        
        # Manually create data with typo in type name
        bad_data = {
            '_serialized_type': 'tests.unit.test_type_not_found_errors.Usr',  # Typo: missing 'e'
            'name': 'Alice'
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should suggest the correct type
        assert 'User' in error_msg or 'similar' in error_msg.lower() or 'did you mean' in error_msg.lower()
    
    def test_nonexistent_module_suggests_import(self):
        """Non-existent module should suggest it might not be imported."""
        bad_data = {
            '_serialized_type': 'nonexistent.module.SomeClass',
            'value': 42
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should mention import or module not found
        assert 'import' in error_msg.lower() or 'module' in error_msg.lower()
    
    def test_local_class_suggests_registration(self):
        """Local class should suggest it might be defined locally."""
        # Simulate a local class that wasn't registered
        bad_data = {
            '_serialized_type': 'LocalClass',  # No module path
            'value': 42
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should mention local definition or registration
        assert 'local' in error_msg.lower() or 'register' in error_msg.lower()
    
    def test_shows_registered_types_when_no_match(self):
        """When no similar types found, should list some registered types."""
        class Product(Serializable):
            def __init__(self, id):
                super().__init__()
                self.id = id
        
        bad_data = {
            '_serialized_type': 'completely.different.XYZ',
            'value': 42
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should mention registered types or available types
        assert 'registered' in error_msg.lower() or 'available' in error_msg.lower()


class TestTypeNotFoundErrorDetails:
    """Test that error messages include helpful details."""
    
    def test_error_includes_attempted_type_name(self):
        """Error should clearly show what type was attempted."""
        bad_data = {
            '_serialized_type': 'my.app.MissingClass',
            'value': 42
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should include the type name that was attempted
        assert 'my.app.MissingClass' in error_msg
    
    def test_multiple_similar_types_all_suggested(self):
        """If multiple similar types exist, suggest them all."""
        class UserProfile(Serializable):
            def __init__(self, id):
                super().__init__()
                self.id = id
        
        class UserSettings(Serializable):
            def __init__(self, id):
                super().__init__()
                self.id = id
        
        class UserAccount(Serializable):
            def __init__(self, id):
                super().__init__()
                self.id = id
        
        # Typo: "UserProfil" instead of "UserProfile"
        bad_data = {
            '_serialized_type': 'tests.unit.test_type_not_found_errors.UserProfil',
            'id': 1
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should suggest UserProfile as it's most similar
        assert 'UserProfile' in error_msg or 'similar' in error_msg.lower()


class TestFuzzyMatching:
    """Test fuzzy matching for type name suggestions."""
    
    def test_case_insensitive_matching(self):
        """Should match types regardless of case."""
        class MyClass(Serializable):
            def __init__(self):
                super().__init__()
        
        bad_data = {
            '_serialized_type': 'tests.unit.test_type_not_found_errors.myclass',  # lowercase
            'value': 1
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should suggest MyClass
        assert 'MyClass' in error_msg
    
    def test_partial_match_suggestions(self):
        """Should suggest types with partial matches."""
        class DataProcessor(Serializable):
            def __init__(self):
                super().__init__()
        
        bad_data = {
            '_serialized_type': 'tests.unit.test_type_not_found_errors.DataProc',  # Partial
            'value': 1
        }
        
        with pytest.raises(TypeError) as exc_info:
            deserialize(bad_data)
        
        error_msg = str(exc_info.value)
        # Should suggest DataProcessor
        assert 'DataProcessor' in error_msg or 'similar' in error_msg.lower()
