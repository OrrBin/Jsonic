"""
Example demonstrating Jsonic + Pydantic integration.

Shows how Jsonic automatically works with Pydantic models while
preserving advanced types like sets and tuples, AND keeping Pydantic validation.
"""

from pydantic import BaseModel, Field, ValidationError
from typing import Set, List
from jsonic import serialize, deserialize


# Define Pydantic models with validation
class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Must be > 0
    tags: Set[str]  # Jsonic preserves set type!


class Order(BaseModel):
    order_id: str
    products: List[Product]
    total: float = Field(ge=0)  # Must be >= 0


# Create instances
laptop = Product(name="Laptop", price=999.99, tags={"electronics", "computers"})
mouse = Product(name="Mouse", price=29.99, tags={"electronics", "accessories"})

order = Order(
    order_id="ORD-123",
    products=[laptop, mouse],
    total=1029.98
)

print("=" * 60)
print("PART 1: Normal Serialization/Deserialization")
print("=" * 60)

# Serialize - Jsonic handles Pydantic models automatically
print("\n✓ Serializing Pydantic models...")
data = serialize(order)
print(f"  Order ID: {data['order_id']}")
print(f"  Products: {len(data['products'])}")
print(f"  Laptop tags (preserved as set): {data['products'][0]['tags']}")

# Deserialize - Pydantic validation still works!
print("\n✓ Deserializing...")
restored_order = deserialize(data, expected_type=Order)
print(f"  Restored order: {restored_order.order_id}")
print(f"  First product: {restored_order.products[0].name}")
print(f"  Tags type: {type(restored_order.products[0].tags)}")  # Still a set!
assert isinstance(restored_order.products[0].tags, set), "Tags should be a set!"

print("\n" + "=" * 60)
print("PART 2: Validation on Object Creation")
print("=" * 60)

# Validation works on creation
print("\n✗ Trying to create product with negative price...")
try:
    bad_product = Product(name="Bad", price=-10, tags={"test"})
    print("  ERROR: Should have raised ValidationError!")
except ValidationError as e:
    print(f"  ✓ Validation caught: {len(e.errors())} error(s)")
    print(f"    - {e.errors()[0]['msg']}")

print("\n" + "=" * 60)
print("PART 3: Validation During Deserialization")
print("=" * 60)

# Test 1: Invalid price in serialized data
print("\n✗ Test 1: Deserializing product with negative price...")
bad_data = {
    'name': 'Invalid Product',
    'price': -50.0,  # Invalid!
    'tags': {'items': ['test'], '_is_set': True, '_serialized_type': 'set'},
    '_serialized_type': '__main__.Product'
}

try:
    bad_product = deserialize(bad_data, expected_type=Product)
    print("  ERROR: Should have raised ValidationError!")
except ValidationError as e:
    print(f"  ✓ Validation caught: {len(e.errors())} error(s)")
    print(f"    - Field: {e.errors()[0]['loc'][0]}")
    print(f"    - Error: {e.errors()[0]['msg']}")

# Test 2: Missing required field
print("\n✗ Test 2: Deserializing product with missing field...")
incomplete_data = {
    'name': 'Incomplete',
    # Missing 'price' field!
    'tags': {'items': ['test'], '_is_set': True, '_serialized_type': 'set'},
    '_serialized_type': '__main__.Product'
}

try:
    incomplete_product = deserialize(incomplete_data, expected_type=Product)
    print("  ERROR: Should have raised ValidationError!")
except ValidationError as e:
    print(f"  ✓ Validation caught: {len(e.errors())} error(s)")
    print(f"    - Missing field: {e.errors()[0]['loc'][0]}")

# Test 3: Wrong type
print("\n✗ Test 3: Deserializing product with wrong type...")
wrong_type_data = {
    'name': 'Wrong Type',
    'price': "not a number",  # Should be float!
    'tags': {'items': ['test'], '_is_set': True, '_serialized_type': 'set'},
    '_serialized_type': '__main__.Product'
}

try:
    wrong_product = deserialize(wrong_type_data, expected_type=Product)
    print("  ERROR: Should have raised ValidationError!")
except ValidationError as e:
    print(f"  ✓ Validation caught: {len(e.errors())} error(s)")
    print(f"    - Field: {e.errors()[0]['loc'][0]}")
    print(f"    - Error: {e.errors()[0]['type']}")

# Test 4: Invalid nested data
print("\n✗ Test 4: Deserializing order with invalid product...")
order_data = serialize(order)
# Corrupt the first product's price
order_data['products'][0]['price'] = -100

try:
    bad_order = deserialize(order_data, expected_type=Order)
    print("  ERROR: Should have raised ValidationError!")
except ValidationError as e:
    print(f"  ✓ Validation caught: {len(e.errors())} error(s)")
    print(f"    - Location: {'.'.join(str(x) for x in e.errors()[0]['loc'])}")
    print(f"    - Error: {e.errors()[0]['msg']}")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
print("\nKey Takeaways:")
print("  1. Jsonic reconstructs sets and native Pydantic validation runs")
print("  2. Pydantic validation works during deserialization")
print("  3. Invalid data is caught with clear error messages")
print("  4. Works with nested models and complex structures")
