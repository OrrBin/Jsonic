def full_type_name(o):
    module = o.__module__
    if module is None or module == str.__class__.__module__:
        return o.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__name__


def is_private_attribute(attr_name):
    return attr_name.startswith('_')
