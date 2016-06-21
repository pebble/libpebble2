from __future__ import absolute_import
__author__ = "katharine"

from six import iteritems

import struct
import uuid

from libpebble2.exceptions import PacketDecodeError, PacketEncodeError

__all__ = ["DEFAULT_ENDIANNESS", "Field", "Int8", "Uint8", "Int16", "Uint16", "Int32", "Uint32",
           "Int64", "Uint64", "Boolean", "UUID", "Union", "Embed", "Padding", "PascalString", "NullTerminatedString",
           "FixedString", "PascalList", "FixedList", "BinaryArray", "Optional"]

DEFAULT_ENDIANNESS = '!'


class Field(object):
    """
    Base class for Pebble Protocol fields. This class does nothing; only subclasses are useful.

    :param default: The default value of the field, if nothing else is specified.
    :param endianness: The endianness of the field. By default, inherits from packet, or its parent packet, etc.
                       Use ``"<"`` for little endian or ``">"`` for big endian.
    :type endianness: str
    :param enum: An :class:`~enum.Enum` that represents the possible values of the field.
    :type enum: ~enum.Enum
    """
    #: A format code for use in :meth:`struct.pack`, if using the default implementation of :meth:`buffer_to_value`
    #: and :meth:`value_to_bytes`
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
        """
        Converts the bytes in ``buffer`` at ``offset`` to a native Python value. Returns that value and the number of
        bytes consumed to create it.

        :param obj: The parent :class:`.PebblePacket` of this field
        :type obj: .PebblePacket
        :param buffer: The buffer from which to extract a value.
        :type buffer: bytes
        :param offset: The offset in the buffer to start at.
        :type offset: int
        :param default_endianness: The default endianness of the value. Used if ``endianness`` was not passed to the
                                   :class:`Field` constructor.
        :type default_endianness: str
        :return: (value, length)
        :rtype: (:class:`object`, :any:`int`)
        """
        try:
            value, length = struct.unpack_from(str(self.endianness or default_endianness)
                                      + self.struct_format, buffer, offset)[0], struct.calcsize(self.struct_format)
            if self._enum is not None:
                try:
                    return self._enum(value), length
                except ValueError as e:
                    raise PacketDecodeError("{}: {}".format(self.type, e))
            else:
                return value, length
        except struct.error as e:
            raise PacketDecodeError("{}: {}".format(self.type, e))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        """
        Converts the given value to an appropriately encoded string of bytes that represents it.

        :param obj: The parent :class:`.PebblePacket` of this field
        :type obj: .PebblePacket
        :param value: The python value to serialise.
        :param default_endianness: The default endianness of the value. Used if ``endianness`` was not passed to the
                                   :class:`Field` constructor.
        :type default_endianness: str
        :return: The serialised value
        :rtype: bytes
        """
        return struct.pack(str(self.endianness or default_endianness) + self.struct_format, value)

    def prepare(self, obj, value):
        pass

    def dependent_fields(self):
        return []

#: Used internally by :class:`PebblePacket` to sort fields into the right order.
Field.next_id = 0


class Int8(Field):
    """
    Represents an ``int8_t``.
    """
    struct_format = 'b'


class Uint8(Field):
    """
    Represents a ``uint8_t``.
    """
    struct_format = 'B'


class Int16(Field):
    """
    Represents an ``int16_t``.
    """
    struct_format = 'h'


class Uint16(Field):
    """
    Represents a ``uint16_t``.
    """
    struct_format = 'H'


class Int32(Field):
    """
    Represents an ``int32_t``.
    """
    struct_format = 'i'


class Uint32(Field):
    """
    Represents a ``uint32_t``.
    """
    struct_format = 'I'


class Int64(Field):
    """
    Represents an ``int64_t``.
    """
    struct_format = 'q'


class Uint64(Field):
    """
    Represents a ``uint64_t``.
    """
    struct_format = 'Q'


class Boolean(Field):
    """
    Represents a ``bool``.
    """
    struct_format = '?'


class UUID(Field):
    """
    Represents a UUID, represented as a 16-byte array (``uint8_t[16]``). The Python representation is a
    :class:`~uuid.UUID`. Endianness is ignored.
    """
    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        try:
            return uuid.UUID(bytes=buffer[offset:offset+16]), 16
        except ValueError as e:
            raise PacketDecodeError("{}: failed to decode UUID: {}".format(self.type, e))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        assert isinstance(value, uuid.UUID)
        return value.bytes


class Union(Field):
    """
    Represents a union of some other set of fields or packets, determined by some other field (``determinant``).

    Example usage: ::

       command = Uint8()
       data = Union(command, {
           0: SomePacket,
           1: SomeOtherPacket,
           2: AnotherPacket
       })

    :param determinant: The field that is used to determine which possible entry to use.
    :type determinant: Field
    :param contents: A :class:`dict` mapping values of ``determinant`` to either :class:`Field`\ s or
                     :class:`PebblePacket`\ s
                     that this :class:`Union` can represent. This dictionary is inverted for use in serialisation, so it
                     should be a one-to-one mapping.
    :type contents: dict
    :param accept_missing: If ``True``, the :class:`Union` will tolerate receiving unknown values, considering them to
                           be ``None``.
    :type accept_missing: bool
    :param length: An optional :class:`Field` that should contain the length of the :class:`Union`. If provided, the
                   field will be filled in on serialisation, and taken as a *maximum* length during deserialisation.
    :type length: int
    """
    def __init__(self, determinant, contents, accept_missing=False, length=None):
        self.determinant = determinant
        self.contents = contents
        self.type_map = {v: k for k, v in iteritems(self.contents)}
        self.accept_missing = accept_missing
        self.length = length
        super(Union, self).__init__()

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if value is not None:
            return value.serialise(default_endianness=default_endianness)
        elif self.accept_missing:
            return b''
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
            else:
                return None, length

    def dependent_fields(self):
        if not self.accept_missing:
            return [self.determinant]
        else:
            return []


class Embed(Field):
    """
    Embeds another :class:`.PebblePacket`. Useful for implementing repetitive packets.

    :param packet: The packet to embed.
    :type packet: .PebblePacket
    """
    def __init__(self, packet, length=None):
        self.packet = packet
        self.length = length
        super(Embed, self).__init__()

    def prepare(self, obj, value):
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value.serialise()))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        v = value.serialise(default_endianness=default_endianness)
        if isinstance(self.length, Field):
            max_len = getattr(obj, self.length._name)
        else:
            max_len = self.length
        if max_len is not None and len(v) > max_len:
            raise PacketEncodeError("Embedded field with max length {} is actually {} bytes long."
                                    .format(self.length, len(v)))
        return v

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if self.length is None:
            return self.packet.parse(buffer[offset:], default_endianness=default_endianness)
        else:
            if isinstance(self.length, Field):
                max_length = getattr(obj, self.length._name)
            else:
                max_length = self.length
            return self.packet.parse(buffer[offset:offset+max_length], default_endianness=default_endianness)

    def dependent_fields(self):
        if isinstance(self.length, Field):
            return [self.length]
        else:
            return []


class Padding(Field):
    """
    Represents some unused bytes. During deserialisation, ``length`` bytes are skipped; during serialisation,
    ``length`` 0x00 bytes are added.

    :param length: The number of bytes of padding.
    :type length: int
    """
    def __init__(self, length):
        self.length = length
        super(Padding, self).__init__()

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        return None, self.length

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return b'\x00' * self.length


class PascalString(Field):
    """
    Represents a UTF-8-encoded string that is prefixed with a length byte.

    :param null_terminated: If ``True``, a zero byte is appended to the string and included in the length during
                            serialisation. The string is always terminated at the first zero byte during
                            deserialisation, regardless of the value of this argument.
    :type null_terminated: bool
    :param count_null_terminator: If ``True``, any appended zero byte is not counted in the length of the string.
                            This actually comes up.
    :type count_null_terminator: bool
    """
    def __init__(self, null_terminated=False, count_null_terminator=True, *args, **kwargs):
        self.null_terminated = null_terminated
        self.count_null_terminator = count_null_terminator
        super(PascalString, self).__init__(*args, **kwargs)

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        try:
            length, = struct.unpack_from('B', buffer, offset)
        except struct.error as e:
            raise PacketDecodeError("{}: {}".format(self.type, str(e)))
        extra_bytes = 1
        if self.null_terminated and not self.count_null_terminator:
            extra_bytes += 1
        if len(buffer) < offset + length + extra_bytes:
            raise PacketDecodeError("{}: Expected {} bytes, but only had {}".format(
                self.type, length + extra_bytes, len(buffer) - offset))
        return buffer[offset+1:offset+1+length].split(b'\x00')[0].decode('utf-8'), length + extra_bytes

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        value = value[:255].encode('utf-8')
        if self.null_terminated:
            if self.count_null_terminator:
                value = value[:254] + b'\x00'
                length = len(value)
            else:
                value = value[:255] + b'\x00'
                length = len(value) - 1
        else:
            length = len(value)
        return struct.pack('B', length) + value


class NullTerminatedString(Field):
    """
    Represents a null-terminated, UTF-8 encoded string (i.e. a C string).
    """
    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        end = offset
        if end >= len(buffer):
            raise PacketDecodeError("{}: No bytes available.")
        while buffer[end] != b'\x00'[0]:
            print(buffer[end])
            end += 1
            if end >= len(buffer):
                raise PacketDecodeError("{}: Reached end of buffer without terminating.".format(self.type))
        return buffer[offset:end].split(b'\x00')[0].decode('utf-8'), end - offset + 1

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        return value.encode('utf-8') + b'\x00'


class FixedString(Field):
    """
    Represents a "fixed-length" string. "Fixed-length" here has one of three possible meanings:

    * The length is determined by another :class:`Field` in the :class:`PebblePacket`. For this effect, pass in a
      :class:`Field` for ``length``. To deserialise correctly, this field *must* appear before the :class:`FixedString`.
    * The length is fixed by the protocol. For this effect, pass in an :any:`int` for ``length``.
    * The string uses the entire remainder of the packet. For this effect, omit ``length`` (or pass ``None``).

    :param length: The length of the string.
    :type length: :class:`Field` | :any:`int`
    """
    def __init__(self, length=None, **kwargs):
        self.length = length
        super(FixedString, self).__init__(**kwargs)

    def prepare(self, obj, value):
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value.encode('utf-8')))

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        elif self.length is not None:
            length = self.length
        else:
            length = len(buffer) - offset
        try:
            return struct.unpack_from('%ds' % length, buffer, offset)[0].split(b'\x00')[0].decode('utf-8'), length
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

    def dependent_fields(self):
        if isinstance(self.length, Field):
            return [self.length]
        else:
            return []


class PascalList(Field):
    """
    Represents a list of :class:`.PebblePacket`\ s, each of which is prefixed with a byte indicating its length.

    :param member_type: The type of :class:`.PebblePacket` in the list.
    :type member_type: ~builtins.type
    :param count: If specified, the a :class:`Field` that contains the number of entries in the list. On serialisation,
                  the count is filled in with the number of entries. On deserialisation, it is interpreted as a
                  maximum; it is not an error for the packet to end prematurely.
    :type count: Field
    """
    def __init__(self, member_type, count=None):
        self.member_type = member_type
        self.count = count
        super(PascalList, self).__init__()

    def prepare(self, obj, value):
        if isinstance(self.count, Field):
            setattr(obj, self.count._name, len(value))

    def value_to_bytes(self, obj, values, default_endianness=DEFAULT_ENDIANNESS):
        result = b''
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

    def dependent_fields(self):
        if isinstance(self.count, Field):
            return [self.count]
        else:
            return []


class FixedList(Field):
    """
    Represents a list of either :class:`PebblePacket`\ s or :class:`Field`\ s with either a fixed number of entries,
    a fixed length (in bytes), or both. There are no dividers between entries; the members must be fixed-length.

    If neither ``count`` nor ``length`` is set, members will be read until the end of the buffer.

    :param member_type: Either a :class:`Field` instance or a :class:`PebblePacket` subclass that represents the
                        members of the list.
    :param count: A :class:`Field` containing the number of elements in the list. On serialisation, will be set to the
                  number of members. On deserialisation, is treated as a maximum.
    :param length: A :class:`Field` containing the number of bytes in the list. On serialisation, will be set to the
                   length of the serialised list. On deserialisation, is treated as a maximum.
    """
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
            if isinstance(self.member_type, Field):
                total_length = sum(len(self.member_type.value_to_bytes(obj, x)) for x in value)
            else:
                total_length = sum(len(x.serialise()) for x in value)
            setattr(obj, self.length._name, current + total_length)

    def value_to_bytes(self, obj, values, default_endianness=DEFAULT_ENDIANNESS):
        result = b''
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
        max_length = None

        if isinstance(self.count, Field):
            max_count = getattr(obj, self.count._name)

        if isinstance(self.length, Field):
            max_length = getattr(obj, self.length._name)

        i = 0
        while (offset + length < len(buffer) and (max_count is None or i < max_count)
               and (max_length is None or length < max_length)):
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

    def dependent_fields(self):
        fields = []
        if isinstance(self.count, Field):
            fields.append(self.count)
        if isinstance(self.length, Field):
            fields.append(self.length)
        return fields


class BinaryArray(Field):
    """
    An array of arbitrary bytes, represented as a Python :class:`bytes` object. The ``length`` can be either a
    :class:`Field`, an :any:`int`, or omitted.

    :param length: The length of the array:

                   * If it's a :class:`Field`, the value of that field is read during deserialisation and written
                     during seiralisation.
                   * If it's an :any:`int`, that many bytes are always read.
                   * If it is ``None``, bytes are read until the end of the message.
    :type length: Field | int
    """
    def __init__(self, length=None, **kwargs):
        self.length = length
        super(BinaryArray, self).__init__(**kwargs)

    def prepare(self, obj, value):
        if isinstance(self.length, Field):
            setattr(obj, self.length._name, len(value))

    def value_to_bytes(self, obj, value, default_endianness=DEFAULT_ENDIANNESS):
        if not isinstance(value, bytes):
            raise TypeError("BinaryArrays must receive 'bytes'; got '{}'".format(value))

        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        elif self.length is not None:
            length = self.length
        else:
            return value
        value = value[:length]
        value += b'\x00' * (length - len(value))
        return value

    def buffer_to_value(self, obj, buffer, offset, default_endianness=DEFAULT_ENDIANNESS):
        if isinstance(self.length, Field):
            length = getattr(obj, self.length._name)
        elif self.length is None:
            length = len(buffer) - offset
        else:
            length = self.length
        if len(buffer) - offset < length:
            raise PacketDecodeError("{}: Expected more bytes (wanted {}; got {}).".format(self.type, length,
                                                                                          len(buffer) - offset))
        return buffer[offset:offset+length], length

    def dependent_fields(self):
        if isinstance(self.length, Field):
            return [self.length]
        else:
            return []


class Optional(Field):
    """
    Represents an optional field. It is usually an error during deserialisation for fields to be omitted. If that
    field is :class:`Optional`, it will be left at its default value and ignored.

    :param actual_field: The field that is being made optional.
    :type actual_field: Field
    """
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

    def dependent_fields(self):
        return self.field.dependent_fields()
