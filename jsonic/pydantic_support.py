"""
Pydantic integration for Jsonic.

Provides automatic detection and handling of Pydantic BaseModel instances.
Supports both Pydantic V1 and V2.
"""

from typing import Any, Type, Optional

# Try to import Pydantic, but don't fail if it's not installed
try:
    from pydantic import BaseModel, VERSION
    PYDANTIC_AVAILABLE = True
    PYDANTIC_V2 = VERSION.startswith('2.')
except ImportError:
    PYDANTIC_AVAILABLE = False
    PYDANTIC_V2 = False
    BaseModel = None


def is_pydantic_model(obj: Any) -> bool:
    """
    Check if an object is a Pydantic BaseModel instance.
    
    Args:
        obj: Object to check
        
    Returns:
        True if obj is a Pydantic model instance, False otherwise
    """
    if not PYDANTIC_AVAILABLE or BaseModel is None:
        return False
    return isinstance(obj, BaseModel)


def is_pydantic_class(cls: Type) -> bool:
    """
    Check if a class is a Pydantic BaseModel subclass.
    
    Args:
        cls: Class to check
        
    Returns:
        True if cls is a Pydantic model class, False otherwise
    """
    if not PYDANTIC_AVAILABLE or BaseModel is None:
        return False
    try:
        return issubclass(cls, BaseModel)
    except TypeError:
        return False


def serialize_pydantic_model(obj: Any, serialize_private_attributes: bool = False) -> dict:
    """
    Serialize a Pydantic model to a dictionary.
    
    Uses Pydantic's model_dump() (V2) or dict() (V1) method to get the data,
    respecting field aliases. Returns raw Python dict that will be processed
    by Jsonic's _preprocess_for_serialization.
    
    Args:
        obj: Pydantic model instance to serialize
        serialize_private_attributes: Whether to include private attributes
        
    Returns:
        Dictionary representation with _serialized_type marker
        
    Note:
        The returned dict may contain sets, tuples, or other Python objects
        that will be handled by Jsonic's preprocessing step.
        Field aliases are respected (by_alias=True).
    """
    # Use appropriate method based on Pydantic version
    if PYDANTIC_V2:
        # Pydantic V2: use model_dump with mode='python' and by_alias=True
        data = obj.model_dump(mode='python', exclude_none=False, by_alias=True)
    else:
        # Pydantic V1: use dict() with by_alias=True
        data = obj.dict(exclude_none=False, by_alias=True)
    
    # Add Jsonic type marker for deserialization
    data['_serialized_type'] = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
    
    # Note: We return the raw dict here. Sets, tuples, and nested objects
    # will be processed by _preprocess_for_serialization in the main flow.
    return data


def deserialize_pydantic_model(data: dict, cls: Type) -> Any:
    """
    Deserialize a dictionary to a Pydantic model.
    
    Uses Pydantic's model_validate() (V2) or parse_obj() (V1) method
    which includes validation. Recursively deserializes any Jsonic-serialized
    nested structures (sets, tuples, custom objects, nested Pydantic models) before passing to Pydantic.
    
    Args:
        data: Dictionary to deserialize
        cls: Pydantic model class to instantiate
        
    Returns:
        Instance of the Pydantic model
        
    Raises:
        ValidationError: If data doesn't match Pydantic model schema
    """
    # Import here to avoid circular dependency
    from jsonic.serializable import deserialize, SERIALIZED_TYPE_ATTRIBUTE_NAME
    
    def _deserialize_value(v):
        """Recursively deserialize a value."""
        if isinstance(v, dict):
            # Check if it's a Jsonic-serialized structure
            if v.get('_is_set') or v.get('_is_tuple') or SERIALIZED_TYPE_ATTRIBUTE_NAME in v:
                return deserialize(v)
            else:
                # Regular dict, recursively process its values
                return {k: _deserialize_value(nested_v) for k, nested_v in v.items()}
        elif isinstance(v, list):
            # Recursively deserialize list items
            return [_deserialize_value(item) for item in v]
        else:
            return v
    
    # Remove Jsonic metadata and recursively deserialize nested structures
    clean_data = {}
    for k, v in data.items():
        if k == '_serialized_type':
            continue
        clean_data[k] = _deserialize_value(v)
    
    # Use appropriate method based on Pydantic version
    if PYDANTIC_V2:
        # Pydantic V2: use model_validate
        return cls.model_validate(clean_data)
    else:
        # Pydantic V1: use parse_obj
        return cls.parse_obj(clean_data)
