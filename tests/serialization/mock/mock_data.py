from datetime import datetime
from typing import List

from tests.serialization.model import Product, CategoryProfile, User, Amount, Donation, AttributeProfile, Coordinate, \
    UserCredentials, ContactDetails, Location, Address

users: List[User] = [
    User(user_id='user_1', birth_time=datetime(1995, 7, 5, 0),
         user_credentials=UserCredentials(token='token', exp=datetime(2020, 11, 1, 0))),
    User(user_id='user_2', birth_time=datetime(1996, 2, 3, 0),
         user_credentials=UserCredentials(token='token', exp=datetime(2020, 11, 1, 0))),
    User(user_id='user_3', birth_time=datetime(1997, 4, 9, 6),
         user_credentials=UserCredentials(token='token', exp=datetime(2020, 11, 1, 0)))
]

products: List[Product] = [
    Product('product_1', 'user_1', 'Product 1 - Chair', CategoryProfile('furniture', [
        AttributeProfile('furniture_type', ['chair']),
        AttributeProfile('condition', ['new'])
    ]), time=datetime(2020, 1, 1, 10, 5, 35)),
    Product('product_2', 'user_1', 'Product 2 - Table', CategoryProfile('furniture', [
        AttributeProfile('furniture_type', ['table']),
        AttributeProfile('condition', ['as_new'])
    ]), time=datetime(2020, 2, 2, 10, 5, 35)),

    Product('product_3', 'user_2', 'Product 3 - Food', CategoryProfile('food', [
        AttributeProfile('food_type', ['frozen', 'vegetables']),
        AttributeProfile('food_sub_type', ['tomatoes', 'lettuce'])
    ]), time=datetime(2020, 3, 3, 10, 5, 35)),

    Product('product_4', 'user_3', 'Product 4 - Shirt', CategoryProfile('clothes', [
        AttributeProfile('cloth_type', ['shirt']),
        AttributeProfile('condition', ['as_new'])
    ]), amount=Amount(amount=complex(-4.123, -5.0001)), time=datetime(2020, 4, 4, 10, 5, 35)),

    Product('product_5', 'user_3', 'Product 5 - Pants', CategoryProfile('clothes', [
        AttributeProfile('cloth_type', ['pants']),
        AttributeProfile('condition', ['as_new'])
    ]), amount=Amount(amount=complex(-1000, 3)), time=datetime(2020, 5, 5, 10, 5, 35)),

    Product('product_6', 'user_2', 'Product 6 - Pants', CategoryProfile('clothes', [
        AttributeProfile('cloth_type', ['pants']),
        AttributeProfile('condition', ['as_new'])
    ]), amount=Amount(amount=complex(1.123, -3.245)), time=datetime(2020, 6, 6, 10, 5, 35)),
]

donations: List[Donation] = [
    Donation('donation_1', 'user_1', ['product_1', 'product_2'],
             location=Location(coord=Coordinate(lat=32.0853, lon=34.7818), address=Address(address='Tel Aviv')),
             time=datetime(2020, 1, 1, 10, 5, 35),
             contact=ContactDetails(email='orr.bob@hotmail.com', phone_number='0509999999')),
    Donation('donation_2', 'user_2', ['product_3', 'product_6'],
             location=Location(coord=Coordinate(lat=32.0853, lon=34.7818), address=Address(address='Tel Aviv')),
             time=datetime(2020, 2, 2, 10, 5, 35),
             contact=ContactDetails(email='orrbenyamini@gmail.com', phone_number='0508888888')),
    Donation('donation_3', 'user_3', ['product_4', 'product_5'],
             location=Location(coord=Coordinate(lat=32.0853, lon=34.7818), address=Address(address='Tel Aviv')),
             time=datetime(2020, 3, 3, 10, 5, 35)),
]
