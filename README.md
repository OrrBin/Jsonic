# Jsonic: pythonic utility for JSON Serialization

Jsonic is a lightweight utility for serializing/deserializing python objects to/from JSON.

## Jsonic components

##### Definition: `jsonic type`  
`jsonic type` is one of the following :
1. `int` `float` `str` `bool`
1. Class extending ``Serializable``
2. Class registered using ``register_serializable_type`` 
3. Class that a custom `@serializer` and `@deserializer` was registered for
4. `dict` with `str` keys that all it's nested values are of `jsonic type`
4. `list` with which all it's elements are of `jsonic type`  


##### Definition: `jsonic representation`
`jsonic representation` is an output of a successful call of `serialize` function on `jsonic type` instance


### Serializable class
Classes extending `Serializable` can be serialized into json dict/string representing the object,
and deserialized back to class instance.
Extending classes that needs to declare some attributes as transient, should have
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
If nested objects exists in such class, their type should be one of the following:
1. Implement Serializable
2. Be registered using the register_serializable_type function
3. Have registered `@serializer` and `@deserializer` for the nested object type

### register_serializable_type function
Used to register classes that don't extend the `Serializable` class.

This is equivalent to extending `Serializable`, but extending `Serializable` is preferred when possible. 
Most common usage is for classes from external source that you want to serialize, but don't extend `Serializable`

### serialize function
Serializes ``class instance`` / ``dict`` / ``list`` / ``other python type`` into ``dictionary`` / ``json string`` representing the input

#### Note:
Only ``jsonic type`` can be serialized using this function

### deserialize function
Deserializes `python dict` / `JSON string`, which is `jsonic representation`

#### Note:
Only ``jsonic representation`` can be deserialized using this function

### @serializer Decorator
Used to register custom serializer for specific type.

These custom serializers are used in the process of serializing `jsonic type`   

### @deserializer Decorator
Used to register custom deserializer for specific type.

These custom deserializers are used in the process of deserializing `jsonic representation`

## Jsonic current limitations
There are few obvious limitations to `Jsonic` and a few more subtle ones.
The main source of those limitations is the nature of serialization process in general.
The main focus of `Jsonic` is serialization of `data classes`, which represents big chunk 
of serialization work in general.

- Most obvious limitation is that only instances of `jsonic type`'s can be serialized.
The immediate effect is that when we want to serialize an instance of class from external source we need to manually register it and all its
nested object types.
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
