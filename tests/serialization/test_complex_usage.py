from datetime import datetime

import pytest

import tests.serialization.mock as mock
from jsonic import serialize, deserialize
from tests.serialization.model import Product, Donation


def test_user_serialization():
    for user in mock.users:
        user_json_obj = serialize(user, string_output=False, serialize_private_attributes=True)
        new_user = deserialize(user_json_obj, string_input=False, deserialize_private_attributes=True)
        assert new_user == user

        user_json_obj = serialize(user, string_output=True, serialize_private_attributes=True)
        new_user = deserialize(user_json_obj, string_input=True, deserialize_private_attributes=True)
        assert new_user == user

        user_json_obj = serialize(user, string_output=False, serialize_private_attributes=True)
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(user_json_obj, string_input=True, deserialize_private_attributes=True)


def test_user_list_serialization():
    json_list = serialize(mock.users, serialize_private_attributes=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    assert new_list == mock.users

    json_list = serialize(mock.users)
    new_list = deserialize(json_list)
    assert new_list == mock.users

    json_list = serialize(mock.users, serialize_private_attributes=True, string_output=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    assert new_list == mock.users


def test_user_dict_serialization():
    user = mock.users[0]
    obj = {
        'user': user,
        'timestamp': datetime(2020, 10, 7, 1, 2, 3, 4),
        'list': ['item1', 'item2', 'item3', mock.users[1]]
    }

    json_obj = serialize(obj)
    new_obj = deserialize(json_obj)

    assert obj == new_obj

    json_obj = serialize(obj, string_output=True)
    new_obj = deserialize(json_obj, string_input=True)

    assert obj == new_obj


def test_product_serialization():
    for product in mock.products:
        product_json_obj = serialize(product, serialize_private_attributes=True)
        new_product = deserialize(product_json_obj, deserialize_private_attributes=True)
        assert new_product == product

        product_json_obj = serialize(product, string_output=True, serialize_private_attributes=True)
        new_product = deserialize(product_json_obj, string_input=True, deserialize_private_attributes=True)
        assert new_product == product

        product_json_obj = serialize(product, string_output=False, serialize_private_attributes=True)
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(product_json_obj, string_input=True, deserialize_private_attributes=True)


def test_product_list_serialization():
    json_list = serialize(mock.products, serialize_private_attributes=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    assert new_list == mock.products

    json_list = serialize(mock.products)
    new_list = deserialize(json_list)
    assert new_list == mock.products

    json_list = serialize(mock.products, serialize_private_attributes=True, string_output=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    assert new_list == mock.products


def test_product_dict_serialization():
    product = mock.products[0]
    user = mock.users[0]
    obj = {
        'product_details': {
            'product': product,
            'details': {
                'timestamp': datetime(2020, 10, 7, 1, 2, 3, 4),
                'user': user
            },
            'list': ['item1', 'item2', 'item3', mock.users[1]]
        },

    }

    json_obj = serialize(obj)
    new_obj = deserialize(json_obj)

    assert obj == new_obj

    json_obj = serialize(obj, string_output=True)
    new_obj = deserialize(json_obj, string_input=True)

    assert obj == new_obj


def test_donation_serialization():
    for donation in mock.donations:
        donation_json_obj = serialize(donation, serialize_private_attributes=True)
        new_donation = deserialize(donation_json_obj, deserialize_private_attributes=True)
        assert new_donation == donation

        donation_json_obj = serialize(donation, string_output=True, serialize_private_attributes=True)
        new_donation = deserialize(donation_json_obj, string_input=True, deserialize_private_attributes=True)
        assert new_donation == donation

        donation_json_obj = serialize(donation, string_output=False, serialize_private_attributes=True)
        with pytest.raises(TypeError, match='deserializing string'):
            deserialize(donation_json_obj, string_input=True, deserialize_private_attributes=True)


def test_donation_list_serialization():
    json_list = serialize(mock.donations, serialize_private_attributes=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True)
    assert new_list == mock.donations

    json_list = serialize(mock.donations)
    new_list = deserialize(json_list)
    assert new_list == mock.donations

    json_list = serialize(mock.donations, serialize_private_attributes=True, string_output=True)
    new_list = deserialize(json_list, deserialize_private_attributes=True, string_input=True)
    assert new_list == mock.donations


def test_donation_dict_serialization():
    donation = mock.donations[0]
    obj = {
        'donation': donation,
        'timestamp': datetime(2020, 10, 7, 1, 2, 3, 4),
        'list': ['item1', 'item2', 'item3', mock.users[1]]
    }

    json_obj = serialize(obj)
    new_obj = deserialize(json_obj)

    assert obj == new_obj

    json_obj = serialize(obj, string_output=True)
    new_obj = deserialize(json_obj, string_input=True)

    assert obj == new_obj

    with pytest.raises(AttributeError, match="not the expected type: <class 'list'>"):
        deserialize(json_obj, string_input=True, expected_type=list)


def test_correct_expected_type():
    donation = mock.donations[0]
    obj = {
        'donation': donation,
        'timestamp': datetime(2020, 10, 7, 1, 2, 3, 4),
        'list': ['item1', 'item2', 'item3', mock.users[1]]
    }

    json_obj = serialize(obj)
    new_obj = deserialize(json_obj, expected_type=dict)

    assert obj == new_obj

    json_list = serialize(mock.donations, serialize_private_attributes=True)
    new_obj = deserialize(json_list, expected_type=list, deserialize_private_attributes=True)

    assert mock.donations == new_obj

    product = mock.products[0]
    product_json_obj = serialize(product, serialize_private_attributes=True)
    new_obj = deserialize(product_json_obj, deserialize_private_attributes=True, expected_type=Product)

    assert product == new_obj


def test_raises_error_when_wrong_expected_type():
    donation = mock.donations[0]
    obj = {
        'donation': donation,
        'timestamp': datetime(2020, 10, 7, 1, 2, 3, 4),
        'list': ['item1', 'item2', 'item3', mock.users[1]]
    }

    json_obj = serialize(obj)

    with pytest.raises(AttributeError, match="not the expected type: <class 'list'>"):
        deserialize(json_obj, expected_type=list)

    json_list = serialize(mock.donations, serialize_private_attributes=True)
    with pytest.raises(AttributeError, match="not the expected type: <class 'dict'>"):
        deserialize(json_list, expected_type=dict, deserialize_private_attributes=True)

    product = mock.products[0]
    product_json_obj = serialize(product, serialize_private_attributes=True)
    with pytest.raises(AttributeError, match="not the expected type:"):
        deserialize(product_json_obj, deserialize_private_attributes=True, expected_type=Donation)
