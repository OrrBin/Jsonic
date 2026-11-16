"""Explicit v2 transport. Node kinds distinguish literal dictionaries from tags."""
import json

from jsonic.exceptions import DeserializationError

TAG = 'jsonic:wire:v2'


class LiteralDict(dict):
    """Internal marker, removed on decoding; never part of the public result."""


def encode(value):
    if isinstance(value, dict):
        kind = 'dict' if isinstance(value, LiteralDict) or '_serialized_type' not in value else 'object'
        normalized = {}
        for key, child in value.items():
            normalized[next(iter(json.loads(json.dumps({key: None}))))] = child
        return [kind, [[key, encode(child)] for key, child in normalized.items()]]
    if isinstance(value, (list, tuple)):
        return ['list', [encode(child) for child in value]]
    return ['value', value]


def envelope(value):
    return {'_serialized_type': TAG, 'version': 2, 'payload': encode(value)}


def unpack(value):
    reject_cycles(value)
    if (type(value) is not dict or set(value) != {'_serialized_type', 'version', 'payload'}
            or value['_serialized_type'] != TAG or type(value['version']) is not int or value['version'] != 2):
        raise DeserializationError('Expected a complete Jsonic v2 envelope', code='invalid_envelope')
    return _node(value['payload'], '')


def _node(node, path):
    def invalid():
        raise DeserializationError('Invalid Jsonic v2 node', path, code='invalid_envelope')
    if type(node) is not list or len(node) != 2 or type(node[0]) is not str:
        invalid()
    kind, data = node
    if kind == 'value':
        if data is not None and type(data) not in (str, bool, int, float):
            invalid()
        return data
    if type(data) is not list:
        invalid()
    if kind == 'list':
        return [_node(child, f'{path}[{i}]') for i, child in enumerate(data)]
    if kind not in ('dict', 'object'):
        invalid()
    result = LiteralDict() if kind == 'dict' else {}
    for pair in data:
        if (type(pair) is not list or len(pair) != 2 or type(pair[0]) is not str
                or pair[0] in result):
            invalid()
        key, child = pair
        result[key] = _node(child, f'{path}.{key}' if path else key)
    if kind == 'object':
        tag = result.get('_serialized_type')
        if not isinstance(tag, str) or not tag:
            invalid()
        if tag in ('tuple', 'set'):
            marker = '_is_' + tag
            if (set(result) != {marker, 'items', '_serialized_type'}
                    or result[marker] is not True or type(result['items']) is not list):
                invalid()
        elif '_is_tuple' in result or '_is_set' in result:
            # No ambiguous marker-first dispatch in the new format.
            invalid()
    return result


def reject_cycles(value):
    """Reject cyclic Python input iteratively, before recursive schema parsing."""
    active = set()
    pending = [(value, False)]
    while pending:
        item, finished = pending.pop()
        if not isinstance(item, (dict, list, tuple, set)):
            continue
        identity = id(item)
        if finished:
            active.remove(identity)
            continue
        if identity in active:
            raise DeserializationError('Circular input is not JSON', code='circular_reference')
        active.add(identity)
        pending.append((item, True))
        children = item.values() if isinstance(item, dict) else item
        pending.extend((child, False) for child in children)
