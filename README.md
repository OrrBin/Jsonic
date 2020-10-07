# Jsonic: pythonic utility for JSON Serialization

Jsonic is a lightweight utility for serializing/deserializing python objects to/from JSON.

## Jsonic components

##### Definition: `serializable type`  
`serializable type` is one of the following :
1. `int` `float` `str` `bool`
1. Class extending ``Serializable``
2. Class registered using ``register_serializable_type`` 
3. Class that a custom `@serializer` and `@deserializer` was registered for
4. `dict` with `str` keys that all it's nested values are of `serializable type`
4. `list` with which all it's elements are of `serializable type`  


##### Definition: `representation of serializable type`
`representation of serializable type` is an output of a successful call of `serialize` function on `serializable type` instance


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
Only ``serializable type`` can be serialized using this function

### deserialize function
Deserializes `python dict` / `JSON string`, which is `representation of serializable type`

#### Note:
Only ``representation of serializable type`` can be deserialized using this function

### @serializer Decorator
Used to register custom serializer for specific type.

These custom serializers are used in the process of serializing `serializable type`   

### @deserializer Decorator
Used to register custom deserializer for specific type.

These custom deserializers are used in the process of deserializing `representation of serializable type`
