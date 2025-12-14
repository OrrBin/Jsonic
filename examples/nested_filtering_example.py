"""
Example demonstrating nested field filtering with Jsonic.

This example shows how to use dot notation to filter nested fields
during serialization, useful for hiding sensitive data or internal fields
in complex object hierarchies.
"""

from dataclasses import dataclass
from typing import List
from jsonic import serialize


@dataclass
class Credentials:
    """Database credentials."""
    username: str
    password: str
    api_key: str


@dataclass
class Database:
    """Database configuration."""
    host: str
    port: int
    credentials: Credentials


@dataclass
class Item:
    """Product item."""
    name: str
    price: float
    internal_cost: float
    supplier_id: str


@dataclass
class Order:
    """Customer order."""
    order_id: str
    customer_email: str
    items: List[Item]
    internal_notes: str


@dataclass
class AppConfig:
    """Application configuration."""
    app_name: str
    version: str
    database: Database
    debug_mode: bool


def example_1_exclude_nested_password():
    """Example 1: Exclude password from nested credentials."""
    print("=" * 60)
    print("Example 1: Exclude nested password field")
    print("=" * 60)
    
    config = AppConfig(
        app_name="MyApp",
        version="1.0.0",
        database=Database(
            host="localhost",
            port=5432,
            credentials=Credentials("admin", "secret123", "key-abc-123")
        ),
        debug_mode=True
    )
    
    # Exclude only the password field from nested credentials
    safe_config = serialize(config, exclude={'database.credentials.password'})
    
    print("\nOriginal config has password:", config.database.credentials.password)
    print("\nSerialized config (password excluded):")
    print(f"  App: {safe_config['app_name']}")
    print(f"  Database: {safe_config['database']['host']}:{safe_config['database']['port']}")
    print(f"  Username: {safe_config['database']['credentials']['username']}")
    print(f"  Password: {'password' in safe_config['database']['credentials']}")  # False
    print(f"  API Key: {safe_config['database']['credentials']['api_key']}")


def example_2_exclude_multiple_nested():
    """Example 2: Exclude multiple nested fields."""
    print("\n" + "=" * 60)
    print("Example 2: Exclude multiple nested sensitive fields")
    print("=" * 60)
    
    config = AppConfig(
        app_name="MyApp",
        version="1.0.0",
        database=Database(
            host="localhost",
            port=5432,
            credentials=Credentials("admin", "secret123", "key-abc-123")
        ),
        debug_mode=True
    )
    
    # Exclude password and API key
    safe_config = serialize(config, exclude={
        'database.credentials.password',
        'database.credentials.api_key'
    })
    
    print("\nSerialized config (password and API key excluded):")
    print(f"  Username: {safe_config['database']['credentials']['username']}")
    print(f"  Has password: {'password' in safe_config['database']['credentials']}")
    print(f"  Has API key: {'api_key' in safe_config['database']['credentials']}")


def example_3_include_nested_fields():
    """Example 3: Include only specific nested fields."""
    print("\n" + "=" * 60)
    print("Example 3: Include only public nested fields")
    print("=" * 60)
    
    config = AppConfig(
        app_name="MyApp",
        version="1.0.0",
        database=Database(
            host="localhost",
            port=5432,
            credentials=Credentials("admin", "secret123", "key-abc-123")
        ),
        debug_mode=True
    )
    
    # Include only non-sensitive fields
    public_config = serialize(config, include={
        'app_name',
        'version',
        'database.host',
        'database.port'
    })
    
    print("\nPublic config (only safe fields included):")
    print(f"  App: {public_config['app_name']} v{public_config['version']}")
    print(f"  Database: {public_config['database']['host']}:{public_config['database']['port']}")
    print(f"  Has credentials: {'credentials' in public_config['database']}")  # False
    print(f"  Has debug_mode: {'debug_mode' in public_config}")  # False


def example_4_filter_list_items():
    """Example 4: Filter fields in list items."""
    print("\n" + "=" * 60)
    print("Example 4: Filter nested fields in list items")
    print("=" * 60)
    
    order = Order(
        order_id="ORD-123",
        customer_email="customer@example.com",
        items=[
            Item("Widget", 10.0, 5.0, "SUP-001"),
            Item("Gadget", 20.0, 12.0, "SUP-002"),
            Item("Doohickey", 15.0, 8.0, "SUP-001")
        ],
        internal_notes="Rush order - VIP customer"
    )
    
    # Exclude internal cost and supplier from all items
    public_order = serialize(order, exclude={
        'items.internal_cost',
        'items.supplier_id',
        'internal_notes'
    })
    
    print(f"\nOrder ID: {public_order['order_id']}")
    print(f"Customer: {public_order['customer_email']}")
    print(f"Has internal notes: {'internal_notes' in public_order}")  # False
    print("\nItems (internal fields excluded):")
    for item in public_order['items']:
        print(f"  - {item['name']}: ${item['price']}")
        print(f"    Has internal_cost: {'internal_cost' in item}")  # False
        print(f"    Has supplier_id: {'supplier_id' in item}")  # False


def example_5_deeply_nested():
    """Example 5: Filter deeply nested structures."""
    print("\n" + "=" * 60)
    print("Example 5: Filter deeply nested fields (3+ levels)")
    print("=" * 60)
    
    config = AppConfig(
        app_name="MyApp",
        version="1.0.0",
        database=Database(
            host="localhost",
            port=5432,
            credentials=Credentials("admin", "secret123", "key-abc-123")
        ),
        debug_mode=True
    )
    
    # Use dot notation for deep nesting
    safe_config = serialize(config, exclude={
        'database.credentials.password',
        'database.credentials.api_key',
        'debug_mode'
    })
    
    print("\nFiltered config:")
    print(f"  App: {safe_config['app_name']}")
    print(f"  Database host: {safe_config['database']['host']}")
    print(f"  Credentials username: {safe_config['database']['credentials']['username']}")
    print(f"  Credentials has password: {'password' in safe_config['database']['credentials']}")
    print(f"  Config has debug_mode: {'debug_mode' in safe_config}")


if __name__ == "__main__":
    example_1_exclude_nested_password()
    example_2_exclude_multiple_nested()
    example_3_include_nested_fields()
    example_4_filter_list_items()
    example_5_deeply_nested()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
