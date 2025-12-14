"""
Example demonstrating Jsonic + Pydantic integration.

Shows how Jsonic automatically works with Pydantic models while
preserving advanced types like sets and tuples.
"""

from pydantic import BaseModel, Field
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
    total: float


# Create instances
laptop = Product(name="Laptop", price=999.99, tags={"electronics", "computers"})
mouse = Product(name="Mouse", price=29.99, tags={"electronics", "accessories"})

order = Order(
    order_id="ORD-123",
    products=[laptop, mouse],
    total=1029.98
)

# Serialize - Jsonic handles Pydantic models automatically
print("Serializing Pydantic models...")
data = serialize(order)
print(f"Order ID: {data['order_id']}")
print(f"Products: {len(data['products'])}")
print(f"Laptop tags (preserved as set): {data['products'][0]['tags']}")

# Deserialize - Pydantic validation still works!
print("\nDeserializing...")
restored_order = deserialize(data, expected_type=Order)
print(f"Restored order: {restored_order.order_id}")
print(f"First product: {restored_order.products[0].name}")
print(f"Tags type: {type(restored_order.products[0].tags)}")  # Still a set!

# Validation works
print("\nTrying invalid data...")
try:
    bad_product = Product(name="Bad", price=-10, tags={"test"})
except Exception as e:
    print(f"Validation caught: {type(e).__name__}")

print("\n✅ Jsonic + Pydantic integration working perfectly!")
