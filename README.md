# Jsonic: pythonic utility for JSON Serialization

`Jsonic` is a lightweight utility for serializing/deserializing python objects to/from JSON.

`Jsonic` targets mainly serialization of `data classes`, and aims to make serialization of such classes smooth and painless process.
As a serialization layer on top of your DB layer, or serialization layer for your custom communication protocol
between python micro-services it can do magics

Nevertheless, Jsonic might not be the right tool for serializing your super complex (and awesome) custom data structure to json 
(although you could probably do it with some extra work)

# Install and basic usage
#### Install
    pip install py-jsonic
   
#### Basic usage example 
    
    from jsonic import serialize, deserialize
    
    class User(Serializable):
        def __init__(self, user_id: str, birth_time: datetime):
            super().__init__()
            self.user_id = user_id
            self.birth_time = birth_time
           
     user = User('id1', datetime(2020,10,11))      
     obj = serialize(user) # {'user_id': 'id1', 'birth_time': {'datetime': '2020-10-11 00:00:00', '_serialized_type': 'datetime'}, '_serialized_type': 'User'}
     new_user : User = deserialize(obj) # new_user is a new instance of user with same attributes
      

#### More advanced usage example
    
    from jsonic import Serializable, register_jsonic_type, serialize, deserialize
    
    class UserCredentials:
    """
    Represents class from some other module, which does not extends Serializable
    We can register it using register_serializable_type function
    """

    def __init__(self, token: str, exp: datetime):
        self.token = token
        self.expiration_time = exp
        self.calculatedAttr = random.uniform(0, 1)

    # Register UserCredentials which represents class from another module that does not implement Serializable
    # exp __init__ parameter is mapped to expiration_time instace attribute
    register_jsonic_type(UserCredentials, init_parameters_mapping={'exp': 'expiration_time'})


    class User(Serializable):
        transient_attributes = ['user_calculated_attr'] # user_calculated_attr won't be serialized and deserialzied
        init_parameters_mapping = {'id': 'user_id'} # id __init__ parameter is mapped to user_id instace attribute

        def __init__(self, user_id: str, birth_time: datetime, user_credentials: UserCredentials, *args):
            super().__init__()
            self.user_id = user_id
            self.birth_time = birth_time
            self.user_credentials = user_credentials
            self.user_calculated_attr = 'user_calculated_attr'
            
    user = User(user_id='user_1', birth_time=datetime(1995, 7, 5, 0),
         user_credentials=UserCredentials(token='token', exp=datetime(2020, 11, 1, 0)))
         
    user_json_obj = serialize(user, string_output=True)
    new_user = deserialize(user_json_obj, string_input=True, expected_type=User)


## Definitions

Some definitions that are used in the rest of this file

##### Definition: `jsonic type`  
`jsonic type` is one of the following :
1. `int` `float` `str` `bool`
2. any `data class` (see definition of `data class` below)
3. Class extending ``Serializable``
4. Class registered using ``register_serializable_type`` 
5. Class that a custom `@serializer` and `@deserializer` was registered for
6. `dict` with `str` keys that all it's nested values are of `jsonic type`
7. `list` with which all it's elements are of `jsonic type`  

##### Definition: `jsonic representation`
`jsonic representation` is an output of a successful call of `serialize` function on `jsonic type` instance

Supported forms of representations:
1. Python generic dict
2. JSON string 


#### Definition: `data class`
`data class` is any class that answer the next criteria:
1. it's `__init__` method has no `positional-only` parameters
2. it's `__init__` method has `*args` or `**kwargs` parameters
3. every parameter of it's `__init__` function has corresponding instance attribute with the same name



## Jsonic Features
- serialize any `jsonic type` to `jsonic representation`
    - For classes that extends `Serializable` or are registered using `register_serializable_type` you could 
    declare instance attributes as transient, so they won't participate in the serialization process
    - You could create your own custom serializer for a specific type using `@jsonic_serializer` decorator
    - You can choose to serialize to `python generic dict` or to `JSON string`
    - You can choose to leave private attributes out of the serialization process  
- deserialize `jsonic representation` to `jsonic type` instance
    - For classes that extends `Serializable` or are registered using `register_serializable_type` you could 
    create mapping from `__init__` parameter name to it's corresponding instance attribute name. 
    If not mapped, it is assumed `__init__` parameter has instance attribute with the same name
    - You could deserialize any `Jsonic representation` whether it is `python generic dict` or `JSON string`
    - You could pass the expected deserialized instance type to `deserialize` function for type safety. 
    if the serialized instance was of another type, an error will be raised
    - You can choose to leave private attributes out of the deserialization process  
    
## Jsonic components

### Serializable class
Class extending `Serializable` can be serialized into json dict/string representing the object, and deserialized back to class instance.
Extending classes can declare some attributes as transient. To do so they should have
class attribute:

    transient_attributes: List[str]
    
which should be a list of attributes names that would be transient (won't be serialized and deserialized)

Class that has `__init__` parameter with a different name than it's corresponding instance attribute should have class attribute:

    init_parameters_mapping: Dict[str, str]
    
which should be a dictionary mapping from `__init__` parameter name to the corresponding instance attribute name.
When deserializing class instance, the corresponding instance attribute will be passed to the `__init__` function.
For `__init__` parameter which has no mapping defined, it is assumed that the corresponding instance variable has
the same name as the parameter.

### register_serializable_type function
Used to register classes that don't extend the `Serializable` class, and are not `data class`, therefore optional meta-data is required for them.

This is equivalent to extending `Serializable`, but extending `Serializable` is preferred when possible. 
Most common usage is for classes from external source that you want to serialize, and need to declare some attributes transient or init parameter mapping.

### serialize function
Serializes ``jsonic type`` into ``jsonic representaion`` representing the input

### deserialize function
Deserializes `jsonic representaion` to instance of jsonic type

### @jsonic_serializer Decorator
Used to register custom serializer for specific type.

These custom serializers are used in the process of serializing `jsonic type`   

### @jsonic_deserializer Decorator
Used to register custom deserializer for specific type.

These custom deserializers are used in the process of deserializing `jsonic representation`

## Jsonic current limitations
There are few obvious limitations to `Jsonic` and a few more subtle ones.
The main source of those limitations is the nature of serialization process in general.
The main focus of `Jsonic` is serialization of `data classes`, which represents big chunk 
of common serialization scenarios.

- Most obvious limitation is that only instances of `jsonic type`'s can be serialized.
This means there are classes that cannot be serialized and deserialized correctly using Jsonic
- Jsonic is meant mostly to serialize `data classes`, and have some technical limitations:
    - **constructor with temporary parameters**: If a class constructor has parameters it gets but does persist as an instance attribute, 
    it is not `jsonic type` even if it meets all other conditions.
    This is because when deserializing a `jsonic representation` an instance of the given type is created.
    We need to pass to the constructor the corresponding instance attributes. Therefore if there are parameters it gets and are not 
    being persisted into an instance attribute we won't be able to pass them when creating the instance.
        - Example: A class gets in it's construction some service class instance, and in it's instance construction
        it calls a method of that service, but does not persist this service instance. 
        `Jsonic` won't be able to deserialize this class properly.     
    - **constructor with positional-only parameters**: If a class constructor method has parameters which are `positional-only` parameters, it is not `jsonic type` even if it meets all other conditions.
    This is because when deserializing a `jsonic representation` an instance of the given type is created.
    We need to pass to the constructor the corresponding attributes. We can pass only keyword arguments which correspond to 
    an instance attribute.
    - **constructor with `*args` and `**kwargs`**: if a class constructor method accepts *args or **kwargs, in many cases `Jsonic` won't be able to
    deserialize it properly
    - **constructor with side effects**: When deserializing `jsonic representaion` an instance of the given type is created.
        We don't have the original values that were passed to the constructor, so we pass the corresponding instance attributes instead. 
        so if the constructor has side effects that depend on the parameters it gets we might get unexpected results when deserializng.
