from typing import List

from serialization import Serializable


class AttributeProfile(Serializable):
    def __init__(self, attribute_id: str, values: List[str], **kwargs):
        super().__init__(**kwargs)
        self.attribute_id = attribute_id
        self.values = values

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        return cls(**data)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, AttributeProfile):
            return NotImplemented
        return self.attribute_id == o.attribute_id and self.values == o.values

    def __ne__(self, o: object) -> bool:
        return not self == o


class CategoryProfile(Serializable):
    def __init__(self, category_id: str, attributes: List[AttributeProfile], **kwargs):
        super().__init__(**kwargs)
        self.category_id = category_id
        self.attributes = attributes

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        category_id = data['category_id']
        attributes = list(map(AttributeProfile.from_json, data['attributes']))
        return cls(category_id, attributes)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CategoryProfile):
            return NotImplemented
        return self.category_id == o.category_id and self.attributes == o.attributes

    def __ne__(self, o: object) -> bool:
        return not self == o


class Amount(Serializable):
    def __init__(self, amount: int, **kwargs):
        super().__init__(**kwargs)
        self.amount = amount

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        return cls(**data)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Amount):
            return NotImplemented
        return self.amount == o.amount

    def __ne__(self, o: object) -> bool:
        return not self == o


class Coordinate(Serializable):
    def __init__(self, longitude: float, latitude: float, **kwargs):
        super().__init__(**kwargs)
        self.longitude = longitude
        self.latitude = latitude

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        return cls(**data)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Coordinate):
            return NotImplemented
        return self.longitude == o.longitude and self.latitude == o.latitude

    def __ne__(self, o: object) -> bool:
        return not self == o


class Address(Serializable):
    def __init__(self, address: str, **kwargs):
        super().__init__(**kwargs)
        self.address = address

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        return cls(**data)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Address):
            return NotImplemented
        return self.address == o.address

    def __ne__(self, o: object) -> bool:
        return not self == o


class Location(Serializable):
    def __init__(self, coord: Coordinate, address: Address, **kwargs):
        super().__init__(**kwargs)
        self.coord = coord
        self.address = address

    @classmethod
    def from_json(cls, data):
        if not data:
            return None

        coord = Coordinate.from_json(data['coord'])
        address = Address.from_json(data['address'])
        return cls(coord, address)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Location):
            return NotImplemented
        return self.coord == o.coord and self.address == o.address

    def __ne__(self, o: object) -> bool:
        return not self == o


class ContactDetails(Serializable):
    def __init__(self, phone_number: str, email: str, **kwargs):
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.email = email

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        return cls(**data)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ContactDetails):
            return NotImplemented
        return self.phone_number == o.phone_number and self.email == o.email

    def __ne__(self, o: object) -> bool:
        return not self == o
