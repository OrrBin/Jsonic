"""Independent reader/writer process; registrations never come from its parent."""
import argparse
from datetime import datetime, timezone
import json
import sys

import jsonic
from jsonic import deserialize, serialize, register_jsonic_type, jsonic_serializer, jsonic_deserializer
from tests.support.persistence_models import Record, RenamedValue, Color, Permission
from tests.support.persistence_legacy import OldValue


def configure(name, writing=False):
    if name in ('record', 'color', 'flags', 'combined_flags'):
        register_jsonic_type({'record': Record, 'color': Color, 'flags': Permission, 'combined_flags': Permission}[name])
    if name in ('stable', 'alias', 'moved'):
        typ = OldValue if name == 'moved' and writing else RenamedValue
        jsonic_serializer(typ, type_id='testing:persist:v1')(lambda obj: {'value': obj.value})
        jsonic_deserializer(typ, type_id='testing:persist:v1', aliases=('OldValue',))(lambda data: typ(data['value']))


def value_for(name):
    return {
        'primitives': {'items': [1, True, None, '日本語']},
        'tuple': (1, 'x'), 'set': {7},
        'datetime': datetime(2026, 11, 15, 12, 34, 56, 123456, tzinfo=timezone.utc),
        'complex': complex(-3, 4), 'record': Record(7), 'color': Color.RED,
        'flags': Permission.READ, 'combined_flags': Permission.READ | Permission.WRITE,
        'stable': RenamedValue(7), 'alias': RenamedValue(7), 'moved': OldValue(7),
    }[name]


def describe(value):
    if isinstance(value, (Record, RenamedValue, OldValue)):
        return {'type': type(value).__name__, 'value': value.value}
    if isinstance(value, (Color, Permission)):
        return {'type': type(value).__name__, 'name': value.name, 'value': value.value}
    if isinstance(value, datetime): return {'datetime': value.isoformat()}
    if isinstance(value, complex): return {'real': value.real, 'imag': value.imag}
    if isinstance(value, tuple): return {'tuple': list(value)}
    if isinstance(value, set): return {'set': sorted(value)}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['write', 'read'])
    parser.add_argument('name')
    parser.add_argument('--register', action='store_true')
    parser.add_argument('--safe', action='store_true')
    args = parser.parse_args()
    try:
        if args.register:
            configure(args.name, writing=args.action == 'write')
        if args.action == 'write':
            payload = serialize(value_for(args.name))
            if args.name == 'alias': payload['_serialized_type'] = 'OldValue'
            result = {'payload': payload}
        else:
            result = {'value': describe(deserialize(json.load(sys.stdin), safe=args.safe))}
        result['library'] = jsonic.__file__
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
