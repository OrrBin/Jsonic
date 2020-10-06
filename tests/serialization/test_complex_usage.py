import tests.serialization.mock as mock
from serialization import serialize, deserialize, register_serializable_type
from tests.serialization.model import UserCredentials


def test_complex_usage():

    # Register UserCredentials which represents class from another module that does not implement Serializable
    register_serializable_type(UserCredentials)

    for user in mock.users:
        user_json_obj = serialize(user, serialize_private_attributes=True)
        print(f'serialized user: {user_json_obj}')
        new_user = deserialize(user_json_obj, deserialize_private_attributes=True)
        print(f'deserialized user: {new_user}')
        assert new_user == user

    for product in mock.products:
        product_json_obj = serialize(product, serialize_private_attributes=True)
        print(f'serialized product: {product_json_obj}')
        new_product = deserialize(product_json_obj, deserialize_private_attributes=True)
        print(f'deserialized product: {new_product}')
        assert new_product == product

    for donation in mock.donations:
        donation_json_obj = serialize(donation, serialize_private_attributes=True)
        print(f'serialized donation: {donation_json_obj}')
        new_donation = deserialize(donation_json_obj, deserialize_private_attributes=True)
        print(f'deserialized donation: {new_donation}')
        assert new_donation == donation
