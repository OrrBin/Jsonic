# Jsonic: pythonic utility for JSON Serialization

`Jsonic` is a lightweight utility for serializing/deserializing python objects to/from JSON.

`Jsonic` targets mainly serialization of `data classes`, and aims to make serialization of such classes smooth and painless process.
As a serialization layer on top of your DB layer, or serialization layer for your custom communication protocol
between python micro-services it can do magics

Nevertheless, Jsonic might not be the right tool for serializing your super complex (and awesome) custom data structure to json 
(although you could probably do it with some extra work)

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
    declare instance attributes as transient, so they won't take place in the serialization process
    - You could create your own custom serializer for a specific type using `@jsonic_serializer` decorator
    - You can choose to serialize to `python generic dict` or to `JSON string`
    - You can choose to leave private attributes out of the serialization process  
- deserialize `jsonic representation` to `jsonic type` instance
    - For classes that extends `Serializable` or are registered using `register_serializable_type` you could 
    create mapping from `__init__` parameter name to it's corresponding instance attribute name. 
    If not mapped, it is assumed `__init__` parameter has instance attribute with the same name
    - You could deserialize any `Jsonic representation` whether it is `python generic dict` or `JSON string`
    - You could pass the expected deserialized instance type to `deserialize` function for type safety. 
    if the serialized instance was of another type, an error will be thrown
    - You can choose to leave private attributes out of the deserialization process  
    
## Jsonic components

### Serializable class
Classes extending `Serializable` can be serialized into json dict/string representing the object,
and deserialized back to class instance.
Extending classes can declare some attributes as transient. To do so they should have
class attribute:

    transient_attributes: List[str]
    
which should be a list of attributes names that would be transient (won't be serialized and deserialized)

Classes that has `__init__` parameter with a different name than it's corresponding instance attribute should have class attribute:

    init_parameters_mapping: Dict[str, str]
    
which should be a dictionary mapping from `__init__` parameter name to the corresponding instance attribute name.
When deserializing class instance, the corresponding instance attribute will be passed to the `__init__` function.
For `__init__` parameter which has no mapping defined, it is assumed that the corresponding instance variable has
the same name as the parameter.


#### Note:
Any nested object in such class must be of `jsonic type`

### register_serializable_type function
Used to register classes that don't extend the `Serializable` class, and are not `data class`,
therefore optional meta-data is required for them.

This is equivalent to extending `Serializable`, but extending `Serializable` is preferred when possible. 
Most common usage is for classes from external source that you want to serialize, but is a `jsonic type`

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
of serialization work in general.

- Most obvious limitation is that only instances of `jsonic type`'s can be serialized.
This means there are classes that cannot be serialized and deserialized using Jsonic
- Jsonic is meant mostly to serialize `data classes`, and have some technical limitations:
    - If a class `__init__` method has parameters it gets but not persisting as an attribute, it is not `jsonic type` even if it meets
     all there conditions.
     This is because when deserializing a `jsonic representation` an instance of the given type must be created.
     We need to pass to the constructor the corresponding attributes. Therefore if there are parameters it gets and are not 
     being persisted into an instance attribute we won't be able to pass them when creating the instance.
        - Example: A class gets in it's construction some service class instance, and in it's instance construction
        it calls a method of that service, but does not persist this service instance. 
        `Jsonic` won't be able to deserialize this class properly.     
    - If a class `__init__` method has parameters which are `positional-only` parameters, it is not `jsonic type` even if it meets
    all other conditions.
    This is because when deserializing a `jsonic representation` an instance of the given type must be created.
    We need to pass to the constructor the corresponding attributes. We can pass only keyword arguments which correspond to 
    an instance attribute.
    - `*args and **kwargs`: if a class `__init__` method accepts *args or **kwargs, in many cases `Jsonic` won't be able to
     deserialize it properly
