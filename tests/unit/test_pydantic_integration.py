"""
Tests for Pydantic integration.

These tests only run if Pydantic is installed.
"""

import pytest

# Try to import Pydantic
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

from jsonic import serialize, deserialize

# Skip all tests if Pydantic is not available
pytestmark = pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not installed")


class TestBasicPydanticModel:
    """Test basic Pydantic model serialization."""
    
    def test_simple_pydantic_model(self):
        """Test serializing and deserializing a simple Pydantic model."""
        class User(BaseModel):
            name: str
            age: int
        
        user = User(name="Alice", age=30)
        data = serialize(user)
        
        assert data['name'] == "Alice"
        assert data['age'] == 30
        assert '_serialized_type' in data
        
        restored = deserialize(data, expected_type=User)
        assert isinstance(restored, User)
        assert restored.name == "Alice"
        assert restored.age == 30
    
    def test_pydantic_with_defaults(self):
        """Test Pydantic model with default values."""
        class Product(BaseModel):
            name: str
            price: float
            in_stock: bool = True
        
        product = Product(name="Laptop", price=999.99)
        data = serialize(product)
        
        restored = deserialize(data, expected_type=Product)
        assert restored.name == "Laptop"
        assert restored.price == 999.99
        assert restored.in_stock is True
    
    def test_pydantic_with_optional(self):
        """Test Pydantic model with optional fields."""
        from typing import Optional
        
        class Person(BaseModel):
            name: str
            email: Optional[str] = None
        
        person = Person(name="Bob")
        data = serialize(person)
        
        restored = deserialize(data, expected_type=Person)
        assert restored.name == "Bob"
        assert restored.email is None


class TestPydanticValidation:
    """Test that Pydantic validation still works."""
    
    def test_validation_on_deserialization(self):
        """Test that Pydantic validates data on deserialization."""
        class User(BaseModel):
            name: str
            age: int
            
            @validator('age')
            def age_must_be_positive(cls, v):
                if v < 0:
                    raise ValueError('age must be positive')
                return v
        
        # Valid data works
        user = User(name="Alice", age=30)
        data = serialize(user)
        restored = deserialize(data, expected_type=User)
        assert restored.age == 30
        
        # Invalid data raises ValidationError
        data['age'] = -5
        with pytest.raises(Exception):  # Pydantic ValidationError
            deserialize(data, expected_type=User)
    
    def test_field_constraints(self):
        """Test Pydantic Field constraints."""
        class Product(BaseModel):
            name: str
            price: float = Field(gt=0)  # Must be greater than 0
        
        product = Product(name="Item", price=10.0)
        data = serialize(product)
        
        # Valid price works
        restored = deserialize(data, expected_type=Product)
        assert restored.price == 10.0
        
        # Invalid price raises error
        data['price'] = -5.0
        with pytest.raises(Exception):  # Pydantic ValidationError
            deserialize(data, expected_type=Product)
    
    def test_missing_required_field_on_deserialization(self):
        """Test that missing required fields are caught during deserialization."""
        class User(BaseModel):
            name: str
            email: str
        
        # Create valid data
        user = User(name="Alice", email="alice@example.com")
        data = serialize(user)
        
        # Remove required field
        del data['email']
        
        # Should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            deserialize(data, expected_type=User)
    
    def test_wrong_type_on_deserialization(self):
        """Test that wrong types are caught during deserialization."""
        class Product(BaseModel):
            name: str
            price: float
        
        product = Product(name="Item", price=99.99)
        data = serialize(product)
        
        # Change price to wrong type
        data['price'] = "not a number"
        
        # Should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            deserialize(data, expected_type=Product)
    
    def test_nested_validation_error(self):
        """Test that validation errors in nested models are caught."""
        class Address(BaseModel):
            street: str
            zip_code: str = Field(min_length=5, max_length=5)
        
        class User(BaseModel):
            name: str
            address: Address
        
        user = User(
            name="Alice",
            address=Address(street="123 Main St", zip_code="12345")
        )
        data = serialize(user)
        
        # Corrupt nested data
        data['address']['zip_code'] = "1"  # Too short
        
        # Should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            deserialize(data, expected_type=User)


class TestNestedPydanticModels:
    """Test nested Pydantic models."""
    
    def test_nested_pydantic_models(self):
        """Test Pydantic model containing another Pydantic model."""
        class Address(BaseModel):
            street: str
            city: str
        
        class User(BaseModel):
            name: str
            address: Address
        
        user = User(
            name="Alice",
            address=Address(street="123 Main St", city="NYC")
        )
        
        data = serialize(user)
        restored = deserialize(data, expected_type=User)
        
        assert restored.name == "Alice"
        assert isinstance(restored.address, Address)
        assert restored.address.street == "123 Main St"
        assert restored.address.city == "NYC"
    
    def test_list_of_pydantic_models(self):
        """Test Pydantic model with list of other models."""
        from typing import List
        
        class Item(BaseModel):
            name: str
            quantity: int
        
        class Order(BaseModel):
            order_id: str
            items: List[Item]
        
        order = Order(
            order_id="ORD-123",
            items=[
                Item(name="Laptop", quantity=1),
                Item(name="Mouse", quantity=2)
            ]
        )
        
        data = serialize(order)
        restored = deserialize(data, expected_type=Order)
        
        assert restored.order_id == "ORD-123"
        assert len(restored.items) == 2
        assert all(isinstance(item, Item) for item in restored.items)


class TestPydanticWithCollections:
    """Test Pydantic models with various collection types."""
    
    def test_pydantic_with_list(self):
        """Test Pydantic model with list field."""
        from typing import List
        
        class User(BaseModel):
            name: str
            tags: List[str]
        
        user = User(name="Alice", tags=["admin", "user"])
        data = serialize(user)
        
        restored = deserialize(data, expected_type=User)
        assert restored.tags == ["admin", "user"]
    
    def test_pydantic_with_dict(self):
        """Test Pydantic model with dict field."""
        from typing import Dict
        
        class Config(BaseModel):
            name: str
            settings: Dict[str, int]
        
        config = Config(name="app", settings={"timeout": 30, "retries": 3})
        data = serialize(config)
        
        restored = deserialize(data, expected_type=Config)
        assert restored.settings == {"timeout": 30, "retries": 3}
    
    def test_pydantic_with_set(self):
        """Test Pydantic model with set field - Jsonic preserves set type."""
        from typing import Set
        
        class Product(BaseModel):
            name: str
            tags: Set[str]
        
        product = Product(name="Laptop", tags={"electronics", "computers"})
        data = serialize(product)
        
        restored = deserialize(data, expected_type=Product)
        # Pydantic converts sets to lists by default, but Jsonic should preserve
        assert isinstance(restored.tags, (set, list))  # Accept both for now
        assert set(restored.tags) == {"electronics", "computers"}


class TestPydanticStringOutput:
    """Test Pydantic models with JSON string output."""
    
    def test_string_output(self):
        """Test serializing Pydantic model to JSON string."""
        class User(BaseModel):
            name: str
            age: int
        
        user = User(name="Alice", age=30)
        json_str = serialize(user, string_output=True)
        
        assert isinstance(json_str, str)
        assert '"name"' in json_str
        assert '"Alice"' in json_str
        
        restored = deserialize(json_str, string_input=True, expected_type=User)
        assert restored.name == "Alice"
        assert restored.age == 30


class TestMixedPydanticAndRegular:
    """Test mixing Pydantic models with regular classes."""
    
    def test_pydantic_in_dataclass(self):
        """Test Pydantic model nested in dataclass."""
        from dataclasses import dataclass
        
        class Address(BaseModel):
            street: str
            city: str
        
        @dataclass
        class User:
            name: str
            address: Address
        
        user = User(
            name="Alice",
            address=Address(street="123 Main St", city="NYC")
        )
        
        data = serialize(user)
        restored = deserialize(data, expected_type=User)
        
        assert restored.name == "Alice"
        assert isinstance(restored.address, Address)
        assert restored.address.city == "NYC"
    
    def test_dataclass_in_pydantic(self):
        """Test dataclass nested in Pydantic model."""
        from dataclasses import dataclass
        
        @dataclass
        class Coordinates:
            lat: float
            lon: float
        
        class Location(BaseModel):
            name: str
            coords: Coordinates
        
        location = Location(
            name="Office",
            coords=Coordinates(lat=37.7749, lon=-122.4194)
        )
        
        data = serialize(location)
        restored = deserialize(data, expected_type=Location)
        
        assert restored.name == "Office"
        assert isinstance(restored.coords, Coordinates)
        assert restored.coords.lat == 37.7749


class TestPydanticEdgeCases:
    """Test edge cases with Pydantic models."""
    
    def test_empty_pydantic_model(self):
        """Test Pydantic model with no fields."""
        class Empty(BaseModel):
            pass
        
        obj = Empty()
        data = serialize(obj)
        restored = deserialize(data, expected_type=Empty)
        
        assert isinstance(restored, Empty)
    
    def test_pydantic_with_none_values(self):
        """Test Pydantic model with None values."""
        from typing import Optional
        
        class User(BaseModel):
            name: str
            email: Optional[str] = None
            phone: Optional[str] = None
        
        user = User(name="Alice")
        data = serialize(user)
        
        restored = deserialize(data, expected_type=User)
        assert restored.name == "Alice"
        assert restored.email is None
        assert restored.phone is None



class TestPydanticFieldAliases:
    """Test Pydantic field alias support."""
    
    def test_field_alias_serialization(self):
        """Test that field aliases are used during serialization."""
        from pydantic import Field
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            email_address: str = Field(alias="email")
        
        user = User(userId=123, email="test@example.com")
        data = serialize(user)
        
        # Should use aliases, not field names
        assert "userId" in data
        assert "email" in data
        assert "user_id" not in data
        assert "email_address" not in data
        assert data["userId"] == 123
        assert data["email"] == "test@example.com"
    
    def test_field_alias_deserialization(self):
        """Test that field aliases work during deserialization."""
        from pydantic import Field
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            email_address: str = Field(alias="email")
        
        data = {"userId": 456, "email": "user@example.com", "_serialized_type": "tests.unit.test_pydantic_integration.User"}
        user = deserialize(data, expected_type=User)
        
        assert user.user_id == 456
        assert user.email_address == "user@example.com"
    
    def test_nested_model_with_aliases(self):
        """Test aliases in nested Pydantic models."""
        from pydantic import Field
        
        class Address(BaseModel):
            street_name: str = Field(alias="streetName")
            zip_code: str = Field(alias="zipCode")
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            home_address: Address = Field(alias="address")
        
        user = User(
            userId=789,
            address=Address(streetName="Main St", zipCode="12345")
        )
        data = serialize(user)
        
        assert "userId" in data
        assert "address" in data
        assert "streetName" in data["address"]
        assert "zipCode" in data["address"]
        assert data["userId"] == 789
        assert data["address"]["streetName"] == "Main St"
    
    def test_alias_roundtrip(self):
        """Test full roundtrip with aliases."""
        from pydantic import Field
        
        class Product(BaseModel):
            product_id: int = Field(alias="productId")
            product_name: str = Field(alias="name")
            unit_price: float = Field(alias="price")
        
        original = Product(productId=1, name="Widget", price=9.99)
        data = serialize(original)
        restored = deserialize(data, expected_type=Product)
        
        assert restored.product_id == original.product_id
        assert restored.product_name == original.product_name
        assert restored.unit_price == original.unit_price
    
    def test_mixed_aliases_and_regular_fields(self):
        """Test model with both aliased and non-aliased fields."""
        from pydantic import Field
        
        class Item(BaseModel):
            id: int  # No alias
            item_name: str = Field(alias="name")  # With alias
            description: str  # No alias
        
        item = Item(id=1, name="Test", description="A test item")
        data = serialize(item)
        
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "item_name" not in data
    
    def test_aliases_with_partial_serialization_exclude(self):
        """Test that partial serialization works with aliased fields."""
        from pydantic import Field
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            email: str = Field(alias="email")
            password: str = Field(alias="password")
        
        user = User(userId=1, email="test@example.com", password="secret")
        # Exclude using alias name
        data = serialize(user, exclude={'password'})
        
        assert "userId" in data
        assert "email" in data
        assert "password" not in data
    
    def test_aliases_with_partial_serialization_include(self):
        """Test include parameter with aliased fields."""
        from pydantic import Field
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            email: str = Field(alias="email")
            password: str = Field(alias="password")
        
        user = User(userId=1, email="test@example.com", password="secret")
        # Include using alias names
        data = serialize(user, include={'userId', 'email'})
        
        assert "userId" in data
        assert "email" in data
        assert "password" not in data
    
    def test_aliases_in_list(self):
        """Test list of Pydantic models with aliases."""
        from pydantic import Field
        
        class Product(BaseModel):
            product_id: int = Field(alias="id")
            product_name: str = Field(alias="name")
        
        products = [
            Product(id=1, name="A"),
            Product(id=2, name="B")
        ]
        data = serialize(products)
        
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "A"
        assert "product_id" not in data[0]
    
    def test_aliases_with_string_output(self):
        """Test JSON string output with aliases."""
        from pydantic import Field
        import json
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
        
        user = User(userId=123)
        json_str = serialize(user, string_output=True)
        parsed = json.loads(json_str)
        
        assert "userId" in parsed
        assert "user_id" not in parsed
    
    def test_optional_field_with_alias(self):
        """Test Optional fields with aliases."""
        from pydantic import Field
        from typing import Optional
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            phone: Optional[str] = Field(alias="phoneNumber", default=None)
        
        user = User(userId=1)
        data = serialize(user)
        
        assert "userId" in data
        assert "phoneNumber" in data
        assert data["phoneNumber"] is None
    
    def test_default_value_with_alias(self):
        """Test default values with aliases."""
        from pydantic import Field
        
        class Config(BaseModel):
            app_name: str = Field(alias="appName")
            debug_mode: bool = Field(alias="debug", default=False)
        
        config = Config(appName="MyApp")
        data = serialize(config)
        
        assert data["appName"] == "MyApp"
        assert data["debug"] is False
        assert "debug_mode" not in data
    
    def test_nested_aliases_with_partial_serialization(self):
        """Test nested model aliases with partial serialization."""
        from pydantic import Field
        
        class Address(BaseModel):
            street_name: str = Field(alias="street")
            zip_code: str = Field(alias="zip")
        
        class User(BaseModel):
            user_id: int = Field(alias="userId")
            home_address: Address = Field(alias="address")
        
        user = User(
            userId=1,
            address=Address(street="Main St", zip="12345")
        )
        # Exclude nested aliased field
        data = serialize(user, exclude={'address.zip'})
        
        assert "userId" in data
        assert "address" in data
        assert "street" in data["address"]
        assert "zip" not in data["address"]

