from datetime import datetime

from tests.serialization.model import *


class UserCredentials:
    """
    Class that represents class from some other module, which does not extends Serializable
    We can register it using register_serializable_type function
    """

    def __init__(self, token: str, expiration_time: datetime):
        self.token = token
        self.expiration_time = expiration_time

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, UserCredentials):
            return NotImplemented
        return self.token == o.token and self.expiration_time == o.expiration_time


class User(Serializable):
    def __init__(self, user_id: str, birth_time: datetime, user_credentials: UserCredentials, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.birth_time = birth_time
        self.user_credentials = user_credentials

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, User):
            return NotImplemented
        return self.user_id == o.user_id and self.birth_time == o.birth_time and self.user_credentials == o.user_credentials

    @classmethod
    def from_json(cls, data):
        return cls(**data)


class Product(Serializable):
    def __init__(self, product_id: str, user_id: str, description: str, profile: CategoryProfile,
                 time: datetime, amount: Amount = Amount(1), **kwargs):
        super().__init__(**kwargs)

        self.product_id = product_id
        self.user_id = user_id
        self.description = description
        self.profile = profile
        self.amount = amount
        self.time = time

    @classmethod
    def from_json(cls, data):
        profile = CategoryProfile.from_json(data['profile'])
        amount = Amount.from_json(data['amount'])
        return cls(data['product_id'], data['user_id'], data['description'], profile, amount)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Product):
            return NotImplemented
        return self.product_id == o.product_id and self.user_id == o.user_id and self.description == o.description and \
               self.profile == o.profile and self.amount == o.amount


class Donation(Serializable):
    def __init__(self, donation_id: str, user_id: str, product_ids: List[str], time: datetime, description: str = '',
                 address: Address = None, location: Coordinate = None, contact: ContactDetails = None, **kwargs):
        super().__init__(**kwargs)
        self.donation_id = donation_id
        self.user_id = user_id
        self.product_ids = product_ids
        self.description = description
        self.address = address
        self.location = location
        self.contact = contact
        self._privateAttr = 'donationPrivate'
        self.time = time

    @classmethod
    def from_json(cls, data):
        location = Coordinate.from_json(data['location'])
        address = Address.from_json(data['address'])
        contact = ContactDetails.from_json(data['contact'])

        return cls(donation_id=data['donation_id'], user_id=data['user_id'], product_ids=data['product_ids'],
                   description=data['description'], location=location, address=address,
                   contact=contact)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Donation):
            return NotImplemented
        return self.donation_id == o.donation_id and self.user_id == o.user_id and \
               self.product_ids == self.product_ids and self.description == o.description and \
               self.location == o.location and self.address == o.address and self.contact == o.contact
