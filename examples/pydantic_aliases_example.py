"""
Example demonstrating Pydantic field alias support in Jsonic.

This example shows how Jsonic respects Pydantic field aliases,
which is useful for mapping Python snake_case to JSON camelCase
or other naming conventions required by APIs.
"""

from pydantic import BaseModel, Field
from jsonic import serialize, deserialize
from typing import List, Optional


class Address(BaseModel):
    """Address with field aliases for API compatibility."""
    street_name: str = Field(alias="streetName")
    city_name: str = Field(alias="cityName")
    zip_code: str = Field(alias="zipCode")
    country_code: str = Field(alias="countryCode")


class User(BaseModel):
    """User model with camelCase aliases for JSON API."""
    user_id: int = Field(alias="userId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email_address: str = Field(alias="email")
    phone_number: Optional[str] = Field(alias="phone", default=None)
    home_address: Address = Field(alias="address")


class Product(BaseModel):
    """Product with mixed naming conventions."""
    product_id: int = Field(alias="productId")
    product_name: str = Field(alias="name")
    unit_price: float = Field(alias="price")
    stock_quantity: int = Field(alias="stock")
    category: str  # No alias - uses field name


def example_1_basic_aliases():
    """Example 1: Basic field alias usage."""
    print("=" * 60)
    print("Example 1: Basic Field Aliases")
    print("=" * 60)
    
    user = User(
        userId=123,
        firstName="Alice",
        lastName="Smith",
        email="alice@example.com",
        phone="+1-555-0100",
        address=Address(
            streetName="123 Main St",
            cityName="New York",
            zipCode="10001",
            countryCode="US"
        )
    )
    
    # Serialize - uses aliases
    data = serialize(user)
    
    print("\nSerialized data (uses aliases):")
    print(f"  userId: {data['userId']}")
    print(f"  firstName: {data['firstName']}")
    print(f"  email: {data['email']}")
    print(f"  address.streetName: {data['address']['streetName']}")
    print(f"  address.zipCode: {data['address']['zipCode']}")
    
    print("\nField names NOT in serialized data:")
    print(f"  'user_id' present: {'user_id' in data}")
    print(f"  'first_name' present: {'first_name' in data}")
    print(f"  'email_address' present: {'email_address' in data}")


def example_2_api_response():
    """Example 2: API response with camelCase."""
    print("\n" + "=" * 60)
    print("Example 2: API Response Format")
    print("=" * 60)
    
    user = User(
        userId=456,
        firstName="Bob",
        lastName="Johnson",
        email="bob@example.com",
        address=Address(
            streetName="456 Oak Ave",
            cityName="San Francisco",
            zipCode="94102",
            countryCode="US"
        )
    )
    
    # Serialize to JSON string for API
    json_response = serialize(user, string_output=True)
    
    print("\nJSON API Response:")
    print(json_response)
    
    # Deserialize from API response
    restored = deserialize(json_response, string_input=True, expected_type=User)
    
    print("\nDeserialized user:")
    print(f"  Python field access: user.first_name = {restored.first_name}")
    print(f"  Python field access: user.email_address = {restored.email_address}")


def example_3_mixed_conventions():
    """Example 3: Mixed naming conventions."""
    print("\n" + "=" * 60)
    print("Example 3: Mixed Naming Conventions")
    print("=" * 60)
    
    product = Product(
        productId=789,
        name="Laptop",
        price=999.99,
        stock=50,
        category="Electronics"  # No alias
    )
    
    data = serialize(product)
    
    print("\nProduct data:")
    print(f"  productId (aliased): {data['productId']}")
    print(f"  name (aliased): {data['name']}")
    print(f"  price (aliased): {data['price']}")
    print(f"  category (not aliased): {data['category']}")
    
    print("\nAliased fields use alias names:")
    print(f"  'product_id' present: {'product_id' in data}")
    print(f"  'product_name' present: {'product_name' in data}")
    print(f"  'unit_price' present: {'unit_price' in data}")


def example_4_list_of_models():
    """Example 4: List of models with aliases."""
    print("\n" + "=" * 60)
    print("Example 4: List of Models with Aliases")
    print("=" * 60)
    
    products = [
        Product(productId=1, name="Widget", price=10.0, stock=100, category="Tools"),
        Product(productId=2, name="Gadget", price=20.0, stock=50, category="Electronics"),
        Product(productId=3, name="Doohickey", price=15.0, stock=75, category="Tools")
    ]
    
    data = serialize(products)
    
    print("\nSerialized product list:")
    for i, product in enumerate(data, 1):
        print(f"  Product {i}: {product['name']} (ID: {product['productId']}) - ${product['price']}")


def example_5_roundtrip():
    """Example 5: Full roundtrip with validation."""
    print("\n" + "=" * 60)
    print("Example 5: Roundtrip with Validation")
    print("=" * 60)
    
    original = User(
        userId=999,
        firstName="Charlie",
        lastName="Brown",
        email="charlie@example.com",
        address=Address(
            streetName="789 Elm St",
            cityName="Boston",
            zipCode="02101",
            countryCode="US"
        )
    )
    
    # Serialize
    data = serialize(original)
    print(f"\nOriginal user ID: {original.user_id}")
    print(f"Serialized uses alias: 'userId' = {data['userId']}")
    
    # Deserialize
    restored = deserialize(data, expected_type=User)
    print(f"\nRestored user ID: {restored.user_id}")
    print(f"Names match: {restored.first_name == original.first_name}")
    print(f"Addresses match: {restored.home_address.street_name == original.home_address.street_name}")
    
    # Pydantic validation still works
    print("\nPydantic validation preserved:")
    try:
        invalid_data = {"userId": "not-a-number", "firstName": "Test", "lastName": "User", 
                       "email": "test@example.com", "address": {}}
        deserialize(invalid_data, expected_type=User)
    except Exception as e:
        print(f"  Validation error caught: {type(e).__name__}")


if __name__ == "__main__":
    example_1_basic_aliases()
    example_2_api_response()
    example_3_mixed_conventions()
    example_4_list_of_models()
    example_5_roundtrip()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
