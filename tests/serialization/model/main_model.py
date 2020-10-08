from datetime import datetime
import random

from jsonic import register_jsonic_type
from tests.serialization.model import *
from tests.serialization.model import ContactDetails


class UserCredentials:
    """
    Class that represents class from some other module, which does not extends Serializable
    We can register it using register_serializable_type function
    """

    def __init__(self, token: str, exp: datetime):
        self.token = token
        self.expiration_time = exp
        self.calculatedAttr = random.uniform(0, 1)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, UserCredentials):
            return NotImplemented
        return self.token == o.token and self.expiration_time == o.expiration_time and \
               self.calculatedAttr == o.calculatedAttr

    def __str__(self):
        return f'User(token: {self.token}, expiration_time: {self.expiration_time}, calculatedAttr: {self.calculatedAttr}'


# Register UserCredentials which represents class from another module that does not implement Serializable
register_jsonic_type(UserCredentials, init_parameters_mapping={'exp': 'expiration_time'})


class User(Serializable):
    transient_attributes = ['userCalculatedAttr']
    init_parameters_mapping = {'id': 'user_id'}

    def __init__(self, user_id: str, birth_time: datetime, user_credentials: UserCredentials, *args):
        super().__init__()
        self.user_id = user_id
        self.birth_time = birth_time
        self.user_credentials = user_credentials
        self.userCalculatedAttr = 'userCalculatedAttr'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, User):
            return NotImplemented
        return self.user_id == o.user_id and self.birth_time == o.birth_time and self.user_credentials == o.user_credentials

    def __str__(self):
        return f'User(user_credentials: {self.user_credentials})'


class Product:

    def __init__(self, product_id: str, user_id: str, description: str, profile: CategoryProfile,
                 time: datetime, amount: Amount = Amount(amount=complex(2, -3))):
        super().__init__()

        self.product_id = product_id
        self.user_id = user_id
        self.description = description
        self.profile = profile
        self.amount = amount
        self.time = time

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Product):
            return NotImplemented
        return self.product_id == o.product_id and self.user_id == o.user_id and self.description == o.description and \
               self.profile == o.profile and self.amount == o.amount


class Donation(Serializable):
    def __init__(self, donation_id: str, user_id: str, product_ids: List[str], time: datetime, description: str = '',
                 contact: ContactDetails = None, address: Address = None, location: Location = None, **kwargs):
        super().__init__()
        self.donation_id = donation_id
        self.user_id = user_id
        self.product_ids = product_ids
        self.description = description
        self.address = address
        self.location = location
        self.contact = contact
        self._privateAttr = 'donationPrivate'
        self.time = time

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Donation):
            return NotImplemented
        return self.donation_id == o.donation_id and self.user_id == o.user_id and \
               self.product_ids == self.product_ids and self.description == o.description and \
               self.location == o.location and self.address == o.address and self.contact == o.contact
