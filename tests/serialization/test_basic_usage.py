from datetime import datetime

from serialization import *


class Address:
    def __init__(self, city: str, street: str) -> None:
        self.city = city
        self.street = street

    def __str__(self) -> str:
        return f'Address({self.city}, {self.street})'


# @serializer(serialized_type=Address)
# def serialize_address(address_obj: Address):
#     return {'city': address_obj.city, 'street': address_obj.street}
#
#
# @deserializer(deserialized_type_name=Address)
# def deserialize_datetime(serialized_address):
#     return Address(**serialized_address)


register_serializable_type(Address)


class ContactDetails(Serializable):
    def __init__(self, phone: str, email: str, _private_in_contact: str = '', **kwargs) -> None:
        super().__init__(**kwargs)
        self.phone = phone
        self.email = email
        self._private_in_contact = _private_in_contact

    def __str__(self) -> str:
        return f'ContactDetails({self.phone}, {self.email}, _private_in_contact: {self._private_in_contact})'


class User(Serializable):
    def __init__(self, name: str, id: int, address: Address, time: datetime, contact: ContactDetails,
                 _private_in_user='testPrivate', **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = name
        self.id = id
        self.address = address
        self.time = time
        self.contact = contact
        self._private_in_user = _private_in_user

    def __str__(self) -> str:
        return f'name:{self.name} id:{self.id} address:{self.address},' \
               f' contact: {self.contact}, {self.time}, _private: {self._private_in_user}'


def test_basic_usage():
    testUser = User(name='testUser', id=1, address=Address('myCity', 'myStreet'), time=datetime(2020, 10, 5),
                    contact=ContactDetails(phone='05099999', email='abc@gmail.com',
                                           _private_in_contact='_private_in_contact'), _private_in_user='manualPrivate')

    json_str_with_private = serialize(testUser, serialize_private_attributes=True)
    json_str_without_private = serialize(testUser, serialize_private_attributes=False)
    print(f'serialized with private: {json_str_with_private}')
    print(f'serialized without private: {json_str_without_private}')

    obj_with_privates = deserialize(json_str_with_private)
    obj_without_privates = deserialize(json_str_without_private)

    print(f'deserialized with private: {obj_with_privates}')
    print(f'deserialized without private: {obj_without_privates}')
