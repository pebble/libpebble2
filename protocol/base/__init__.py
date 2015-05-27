__author__ = 'katharine'

import collections
import struct
from types import Field

_PacketRegistry = {}


class PacketType(type):
    def __new__(mcs, name, bases, dct):
        mapping = []
        if 'Meta' in dct:
            dct['_Meta'] = dct['Meta'].__dict__
            del dct['Meta']
        for k, v in dct.items():
            if not isinstance(v, Field):
                continue
            v._name = k
            mapping.append((k, v))
            dct[k] = None
        dct['_type_mapping'] = collections.OrderedDict(sorted(mapping, key=lambda x: x[1].field_id))
        print dct['_type_mapping']
        return super(PacketType, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, name, bases, dct):
        if hasattr(cls, '_Meta'):
            if 'endpoint' in cls._Meta:
                _PacketRegistry[cls._Meta['endpoint']] = cls
                print "Registered packet type %s" % name
        for k, v in cls._type_mapping.iteritems():
            v._parent = cls
        super(PacketType, cls).__init__(name, bases, dct)


class PebblePacket(object):
    __metaclass__ = PacketType

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            if k.startswith('_'):
                raise AttributeError("You cannot set internal properties during construction.")
            getattr(self, k)  # Throws an exception if ir doesn't exist.
            setattr(self, k, v)

    def serialise(self):
        # If we have metadata, it means this is a root packed and we should therefore serialise the whole thing.
        include_header = False
        message = ''
        for k, v in self._type_mapping.iteritems():
            v.prepare(self, getattr(self, k))
        if hasattr(self, '_Meta'):
            include_header = True
            message = struct.pack('!H', self._Meta['endpoint'])
        for k, v in self._type_mapping.iteritems():
            message += v.value_to_bytes(self, getattr(self, k))
        if include_header:
            length = len(message) + 2
            message = struct.pack('!H', length) + message
        return message

    @classmethod
    def parse_message(cls, message):
        length, = struct.unpack_from('!H', message, 0)
        command, = struct.unpack_from('!H', message, 2)
        if command in _PacketRegistry:
            return _PacketRegistry[command].parse(message[4:length])[0], length
        else:
            return None, length

    @classmethod
    def parse(cls, message):
        obj = cls()
        offset = 0
        for k, v in cls._type_mapping.iteritems():
            value, length = v.buffer_to_value(obj, message, offset)
            offset += length
            setattr(obj, k, value)
        return obj, offset

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, ', '.join('%s=%s' % (k, getattr(self, k)) for k in self._type_mapping.keys()))