__author__ = "katharine"

import array
import struct
import uuid


DEFAULT_ENDIANNESS = '!'


class Field(object):
    struct_format = None

    def __init__(self, default=None, endianness=None):
        self.type = type(self).__name__
        self._name = None
        self._parent = None
        self._default = default
        self.field_id = Field.next_id
        self.endianness = endianness
        Field.next_id += 1

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        return struct.unpack_from((self.endianness or default_endianness)
                                  + self.struct_format, buffer, offset)[0], struct.calcsize(self.struct_format)

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
        return uuid.UUID(bytes=buffer[offset:offset+16]), 16

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        assert isinstance(value, uuid.UUID)
        return value.bytes


class Union(Field):
    def __init__(self, determinant, contents, accept_missing=False):
        self.determinant = determinant
        self.contents = contents
        self.type_map = {v: k for k, v in self.contents.iteritems()}
        self.accept_missing = accept_missing
        print self.contents, self.type_map
        super(Union, self).__init__()

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if self.accept_missing and value is not None:
            return value.serialise(default_endianness=default_endianness)
        else:
            return ''

    def prepare(self, obj, value):
        try:
            setattr(obj, self.determinant._name, self.type_map[type(value)])
        except KeyError:
            if not self.accept_missing:
                raise

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        k = getattr(obj, self.determinant._name)
        try:
            return self.contents[k].parse(buffer[offset:], default_endianness=DEFAULT_ENDIANNESS)
        except KeyError:
            if not self.accept_missing:
                raise


class Padding(Field):
    def __init__(self, length):
        self.length = length
        super(Padding).__init__()

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        return None, self.length

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return '\x00' * self.length


class PascalString(Field):
    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        length, = struct.unpack_from('B', buffer, offset)
        return buffer[offset+1:offset+1+length].split('\x00')[0], length + 1

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        print obj, value
        if len(value) > 254:
            value = value[:254]
        value += '\x00'
        return struct.pack('B', len(value)) + value


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
        else:
            length = self.length
        return struct.unpack_from('%ds' % length, buffer, offset)[0].split('\x00')[0], length

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        else:
            length = self.length
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
            item_length, = struct.unpack_from('B', buffer, offset + length)
            length += 1
            print self.member_type
            results.append(self.member_type.parse(buffer[offset+length:offset+length+item_length],
                                                  default_endianness=DEFAULT_ENDIANNESS)[0])
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
        else:
            length = len(buffer) - offset
            return array.array('B', buffer[offset:]), length
