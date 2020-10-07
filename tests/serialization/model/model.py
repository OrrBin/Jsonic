from typing import List

from serialization import Serializable


class AttributeProfile(Serializable):
    def __init__(self, attribute_id: str, values: List[str]):
        super().__init__()
        self.attribute_id = attribute_id
        self.values = values

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, AttributeProfile):
            return NotImplemented
        return self.attribute_id == o.attribute_id and self.values == o.values

    def __ne__(self, o: object) -> bool:
        return not self == o


class CategoryProfile(Serializable):
    def __init__(self, category_id: str, attributes: List[AttributeProfile]):
        super().__init__()
        self.category_id = category_id
        self.attributes = attributes

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CategoryProfile):
            return NotImplemented
        return self.category_id == o.category_id and self.attributes == o.attributes

    def __ne__(self, o: object) -> bool:
        return not self == o


class Amount(Serializable):
    def __init__(self, amount: int):
        super().__init__()
        self.amount = amount

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Amount):
            return NotImplemented
        return self.amount == o.amount

    def __ne__(self, o: object) -> bool:
        return not self == o


class Coordinate(Serializable):
    def __init__(self, longitude: float, latitude: float):
        super().__init__()
        self.longitude = longitude
        self.latitude = latitude

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Coordinate):
            return NotImplemented
        return self.longitude == o.longitude and self.latitude == o.latitude

    def __ne__(self, o: object) -> bool:
        return not self == o


class Address(Serializable):
    def __init__(self, address: str):
        super().__init__()
        self.address = address

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Address):
            return NotImplemented
        return self.address == o.address

    def __ne__(self, o: object) -> bool:
        return not self == o


class Location(Serializable):
    def __init__(self, coord: Coordinate, address: Address):
        super().__init__()
        self.coord = coord
        self.address = address

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Location):
            return NotImplemented
        return self.coord == o.coord and self.address == o.address

    def __ne__(self, o: object) -> bool:
        return not self == o


class ContactDetails(Serializable):
    def __init__(self, phone_number: str, email: str):
        super().__init__()
        self.phone_number = phone_number
        self.email = email

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ContactDetails):
            return NotImplemented
        return self.phone_number == o.phone_number and self.email == o.email

    def __ne__(self, o: object) -> bool:
        return not self == o
