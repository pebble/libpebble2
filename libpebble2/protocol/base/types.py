from __future__ import absolute_import
__author__ = "katharine"

import array
import struct
import uuid

from libpebble2.exceptions import PacketDecodeError

__all__ = ["DEFAULT_ENDIANNESS", "PacketDecodeError", "Field", "Int8", "Uint8", "Int16", "Uint16", "Int32", "Uint32",
           "Int64", "Uint64", "Boolean", "UUID", "Union", "Embed", "Padding", "PascalString", "NullTerminatedString",
           "FixedString", "PascalList", "FixedList", "BinaryArray", "Optional"]

DEFAULT_ENDIANNESS = '!'


class Field(object):
    struct_format = None

    def __init__(self, default=None, endianness=None, enum=None):
        self.type = type(self).__name__
        self._name = None
        self._parent = None
        self._default = default
        self._enum = enum
        self.field_id = Field.next_id
        self.endianness = endianness
        Field.next_id += 1

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        try:
            value, length = struct.unpack_from((self.endianness or default_endianness)
                                      + self.struct_format, buffer, offset)[0], struct.calcsize(self.struct_format)
            if self._enum is not None:
                return self._enum(value), length
            else:
                return value, length
        except struct.error as e:
            raise PacketDecodeError("{}: {}".format(self.type, e))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return struct.pack((self.endianness or default_endianness) + self.struct_format, value)

    def prepare(self, obj, value):
        pass

Field.next_id = 0


class Int8(Field):
    struct_format = 'b'


class Uint8(Field):
    struct_format = 'B'


class Int16(Field):
    struct_format = 'h'


class Uint16(Field):
    struct_format = 'H'


class Int32(Field):
    struct_format = 'i'


class Uint32(Field):
    struct_format = 'I'


class Int64(Field):
    struct_format = 'q'


class Uint64(Field):
    struct_format = 'Q'


class Boolean(Field):
    struct_format = '?'


class UUID(Field):
    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        try:
            return uuid.UUID(bytes=buffer[offset:offset+16]), 16
        except ValueError as e:
            raise PacketDecodeError("{}: failed to decode UUID: {}".format(self.type, e))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        assert isinstance(value, uuid.UUID)
        return value.bytes


class Union(Field):
    def __init__(self, determinant, contents, accept_missing=False, length=None):
        self.determinant = determinant
        self.contents = contents
        self.type_map = {v: k for k, v in self.contents.iteritems()}
        self.accept_missing = accept_missing
        self.length = length
        super(Union, self).__init__()

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if value is not None:
            return value.serialise(default_endianness=default_endianness)
        elif self.accept_missing:
            return ''
        else:
            raise Exception("???")

    def prepare(self, obj, value):
        try:
            setattr(obj, self.determinant._name, self.type_map[type(value)])
        except KeyError:
            if not self.accept_missing:
                raise
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value.serialise()))

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        else:
            length = len(buffer) - offset
        k = getattr(obj, self.determinant._name)
        try:
            return self.contents[k].parse(buffer[offset:offset+length], default_endianness=default_endianness)
        except KeyError:
            if not self.accept_missing:
                raise PacketDecodeError("{}: unrecognised value for union: {}".format(self.type, k))


class Embed(Field):
    def __init__(self, packet):
        self.packet = packet
        super(Embed, self).__init__()

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return value.serialise(default_endianness=default_endianness)

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        return self.packet.parse(buffer[offset:], default_endianness=default_endianness)


class Padding(Field):
    def __init__(self, length):
        self.length = length
        super(Padding, self).__init__()

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        return None, self.length

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return '\x00' * self.length


class PascalString(Field):
    def __init__(self, null_terminated=False, *args, **kwargs):
        self.null_terminated = null_terminated
        super(PascalString, self).__init__(*args, **kwargs)

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        length, = struct.unpack_from('B', buffer, offset)
        return buffer[offset+1:offset+1+length].split('\x00')[0], length + 1

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        value = value[:255].encode('utf-8')
        if self.null_terminated:
            value = value[:254] + '\x00'
        return struct.pack('B', len(value)) + value


class NullTerminatedString(Field):
    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        end = offset
        while buffer[end] != '\x00':
            end += 1
            if end >= len(buffer):
                raise PacketDecodeError("{}: Reached end of buffer without terminating.".format(self.type))
        return buffer[offset:end].split('\x00')[0], end - offset + 1

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return value.encode('utf-8') + '\x00'


class FixedString(Field):
    def __init__(self, length, **kwargs):
        self.length = length
        super(FixedString, self).__init__(**kwargs)

    def prepare(self, obj, value):
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value))

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        elif self.length is not None:
            length = self.length
        else:
            length = len(buffer) - offset
        try:
            return struct.unpack_from('%ds' % length, buffer, offset)[0].split('\x00')[0], length
        except struct.error:
            raise PacketDecodeError("{}: string not long enough (wanted {} bytes)".format(self.type, length))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        value = value.encode('utf-8')
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        elif self.length is not None:
            length = self.length
        else:
            length = len(value)
        return struct.pack('%ds' % length, value)


class PascalList(Field):
    def __init__(self, member_type, count=None):
        self.member_type = member_type
        self.count = count
        super(PascalList, self).__init__()

    def prepare(self, obj, value):
        if isinstance(self.count, Field):
            setattr(obj, self.count._name, len(value))

    def value_to_bytes(self, obj, values, default_endianness=DEFAULT_ENDIANNESS):
        result = ''
        for value in values:
            serialised = value.serialise(default_endianness=default_endianness)
            result += struct.pack('B', len(serialised)) + serialised
        return result

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        results = []
        length = 0
        max_count = None

        if isinstance(self.count, Field):
            max_count = getattr(obj, self.count._name)

        i = 0
        while offset + length < len(buffer) and (max_count is None or i < max_count):
            try:
                item_length, = struct.unpack_from('B', buffer, offset + length)
            except struct.error as e:
                raise PacketDecodeError("{}: couldn't parse entry length: {}".format(self.type, e))
            length += 1
            results.append(self.member_type.parse(buffer[offset+length:offset+length+item_length],
                                                  default_endianness=default_endianness)[0])
            length += item_length
            i += 1
        return results, length


class FixedList(Field):
    def __init__(self, member_type, count=None, length=None):
        self.member_type = member_type
        self.count = count
        self.length = length
        super(FixedList, self).__init__()

    def prepare(self, obj, value):
        if isinstance(self.count, Field):
            setattr(obj, self.count._name, len(value))

        if isinstance(self.length, Field):
            current = getattr(obj, self.length._name) or 0
            setattr(obj, self.length._name, current + sum(len(x.serialise()) for x in value))


    def value_to_bytes(self, obj, values, default_endianness=DEFAULT_ENDIANNESS):
        result = ''
        for value in values:
            if isinstance(self.member_type, Field):
                result += self.member_type.value_to_bytes(obj, value, default_endianness=default_endianness)
            else:
                result += value.serialise(default_endianness=default_endianness)
        return result

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        results = []
        length = 0
        max_count = None

        if isinstance(self.count, Field):
            max_count = getattr(obj, self.count._name)

        i = 0
        while offset + length < len(buffer) and (max_count is None or i < max_count):
            if isinstance(self.member_type, Field):
                value, item_length = self.member_type.buffer_to_value(obj, buffer, offset+length,
                                                                      default_endianness=default_endianness)
            else:
                value, item_length = self.member_type.parse(buffer[offset+length:],
                                                            default_endianness=default_endianness)
            results.append(value)
            length += item_length
            i += 1
        return results, length


class BinaryArray(Field):
    def __init__(self, length=None, **kwargs):
        self.length = length
        super(BinaryArray, self).__init__(**kwargs)

    def prepare(self, obj, value):
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if not isinstance(value, array.array):
            value = array.array('B', value)
        return value.tostring()

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
            return array.array('B', buffer[offset:offset+length]), length
        elif self.length is None:
            length = len(buffer) - offset
            return array.array('B', buffer[offset:]), length
        else:
            return array.array('B', buffer[offset:offset+self.length]), self.length


class Optional(Field):
    def __init__(self, actual_field, **kwargs):
        self.field = actual_field
        super(Optional, self).__init__(**kwargs)

    def prepare(self, *args):
        self.field.prepare(*args)

    def value_to_bytes(self, *args, **kwargs):
        return self.field.value_to_bytes(*args, **kwargs)

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if len(buffer) <= offset:
            return None, 0
        else:
            return self.field.buffer_to_value(obj, buffer, offset, default_endianness=default_endianness)
