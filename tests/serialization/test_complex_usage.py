import pytest

import tests.serialization.mock as mock
from serialization import serialize, deserialize


def test_user_serialization():
    for user in mock.users:
        user_json_obj = serialize(user, output_as_string=False, serialize_private_attributes=True)
        print(f'serialized user: {user_json_obj}')
        new_user = deserialize(user_json_obj, string_input=False, deserialize_private_attributes=True)
        print(f'deserialized user: {new_user}')
        assert new_user == user

        user_json_obj = serialize(user, output_as_string=True, serialize_private_attributes=True)
        print(f'serialized user: {user_json_obj}')
        new_user = deserialize(user_json_obj, string_input=True, deserialize_private_attributes=True)
        print(f'deserialized user: {new_user}')
        assert new_user == user

        user_json_obj = serialize(user, output_as_string=False, serialize_private_attributes=True)
        print(f'serialized user: {user_json_obj}')
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(user_json_obj, string_input=True, deserialize_private_attributes=True)


def test_user_list_serialization():
    json_list = serialize(mock.users, serialize_private_attributes=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.users

    json_list = serialize(mock.users)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.users

    json_list = serialize(mock.users, serialize_private_attributes=True, output_as_string=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.users


def test_product_serialization():
    for product in mock.products:
        product_json_obj = serialize(product, serialize_private_attributes=True)
        print(f'serialized product: {product_json_obj}')
        new_product = deserialize(product_json_obj, deserialize_private_attributes=True)
        print(f'deserialized product: {new_product}')
        assert new_product == product

        product_json_obj = serialize(product, output_as_string=True, serialize_private_attributes=True)
        print(f'serialized product: {product_json_obj}')
        new_product = deserialize(product_json_obj, string_input=True, deserialize_private_attributes=True)
        print(f'deserialized product: {new_product}')
        assert new_product == product

        product_json_obj = serialize(product, output_as_string=False, serialize_private_attributes=True)
        print(f'serialized product: {product_json_obj}')
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(product_json_obj, string_input=True, deserialize_private_attributes=True)


def test_product_list_serialization():
    json_list = serialize(mock.products, serialize_private_attributes=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.products

    json_list = serialize(mock.products)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.products

    json_list = serialize(mock.products, serialize_private_attributes=True, output_as_string=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.products


def test_donation_serialization():
    for donation in mock.donations:
        donation_json_obj = serialize(donation, serialize_private_attributes=True)
        print(f'serialized donation: {donation_json_obj}')
        new_donation = deserialize(donation_json_obj, deserialize_private_attributes=True)
        print(f'deserialized donation: {new_donation}')
        assert new_donation == donation

        donation_json_obj = serialize(donation, output_as_string=True, serialize_private_attributes=True)
        print(f'serialized donation: {donation_json_obj}')
        new_donation = deserialize(donation_json_obj, string_input=True, deserialize_private_attributes=True)
        print(f'deserialized donation: {new_donation}')
        assert new_donation == donation

        donation_json_obj = serialize(donation, output_as_string=False, serialize_private_attributes=True)
        print(f'serialized donation: {donation_json_obj}')
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(donation_json_obj, string_input=True, deserialize_private_attributes=True)


def test_donation_list_serialization():
    json_list = serialize(mock.donations, serialize_private_attributes=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.donations

    json_list = serialize(mock.donations)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.donations

    json_list = serialize(mock.donations, serialize_private_attributes=True, output_as_string=True)
    print(f'serialized donation: {json_list}')
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    print(f'deserialized donation: {new_list}')
    assert new_list == mock.donations
