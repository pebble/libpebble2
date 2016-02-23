# encoding: utf-8
from __future__ import absolute_import, unicode_literals
__author__ = 'katharine'

from six import PY3
import pytest

from enum import IntEnum, Enum
import uuid

from libpebble2.exceptions import PacketDecodeError, PacketEncodeError
from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.base.types import *

def unhex(string):
    if PY3:
        return bytes.fromhex(string)
    else:
        return string.decode('hex')

class TestPacket(PebblePacket):
    command = Uint8()
    length = Uint8()
    count = Uint8()

@pytest.fixture
def packet():
    return TestPacket()


def do_serialise_test(packet, field, tuples):
    for endianness, input, output in tuples:
        assert field.value_to_bytes(packet, input, default_endianness=str(endianness)) == output


def test_int8_serialise(packet):
    do_serialise_test(packet, Int8(), [
        ('<', 0, b'\x00'),
        ('>', 127, b'\x7f'),
        ('!', -128, b'\x80'),
        ('!', -1, b'\xff'),
    ])


def test_uint8_serialise(packet):
    do_serialise_test(packet, Uint8(), [
        ('<', 0, b'\x00'),
        ('>', 255, b'\xff'),
    ])


def test_int16_serialise(packet):
    do_serialise_test(packet, Int16(), [
        ('>', 32767, b'\x7F\xFF'),
        ('<', 32767, b'\xFF\x7F'),
        ('<', -32768, b'\x00\x80'),
    ])

    do_serialise_test(packet, Int16(endianness='<'), [
        ('>', 32767, b'\xFF\x7F'),
        ('<', 32767, b'\xFF\x7F'),
        ('<', -32768, b'\x00\x80'),
    ])


def test_uint16_serialise(packet):
    do_serialise_test(packet, Uint16(), [
        ('>', 65534, b'\xFF\xFE'),
        ('<', 65534, b'\xFE\xFF'),
        ('<', 0, b'\x00\x00'),
    ])

    do_serialise_test(packet, Uint16(endianness='<'), [
        ('>', 65534, b'\xFE\xFF'),
        ('<', 65534, b'\xFE\xFF'),
        ('<', 0, b'\x00\x00'),
    ])

def test_uint8_enum_deserialise(packet):
    class TestEnum(Enum):
        Foo = 0x01
        Bar = 0x02

    field = Uint8(enum=TestEnum)
    assert field.buffer_to_value(packet, b'\x01', 0) == (TestEnum.Foo, 1)

def test_uint8_enum_deserialise_error(packet):
    class TestEnum(Enum):
        Foo = 0x01
        Bar = 0x02

    field = Uint8(enum=TestEnum)
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'\x03', 0)

def test_bool_serialise(packet):
    field = Boolean()
    assert field.value_to_bytes(packet, True) == b'\x01'
    assert field.value_to_bytes(packet, False) == b'\x00'

def test_bool_deserialise(packet):
    field = Boolean()
    assert field.buffer_to_value(packet, b'\x00', 0) == (False, 1)
    assert field.buffer_to_value(packet, b'\x01', 0) == (True, 1)

def test_bool_deserialise_offset(packet):
    field = Boolean()
    assert field.buffer_to_value(packet, b'\x00\x00\x00\x01', 3) == (True, 1)
    assert field.buffer_to_value(packet, b'\x01\x01\x01\x00', 3) == (False, 1)

def test_bool_deserialise_nothing(packet):
    field = Boolean()
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'', 0)
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'\x01\x02', 2)

def test_int16_deserialise(packet):
    field = Int16()
    assert field.buffer_to_value(packet, b'\x00\x06', 0) == (6, 2)
    assert field.buffer_to_value(packet, b'\xff\xff', 0) == (-1, 2)
    assert field.buffer_to_value(packet, b'\xfe\xff', 0, default_endianness='<') == (-2, 2)

def test_int16_deserialised_override_endianness(packet):
    field = Int16(endianness='<')
    assert field.buffer_to_value(packet, b'\x06\x00', 0) == (6, 2)
    assert field.buffer_to_value(packet, b'\xff\xff', 0) == (-1, 2)
    assert field.buffer_to_value(packet, b'\xfe\xff', 0, default_endianness='<') == (-2, 2)

def test_int16_deserialise_offset(packet):
    field = Int16()
    assert field.buffer_to_value(packet, b'\xff\xff\x01\x00', 2) == (0x100, 2)

def test_int16_dserialise_nothing(packet):
    field = Int16()
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'', 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'\xff', 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'\x00\xff\xff', 2)

def test_uuid_serialise(packet):
    field = UUID()
    some_uuid = uuid.UUID("012345678-1234-1234-1234-123456789ab")
    assert field.value_to_bytes(packet, some_uuid) == unhex("012345678123412341234123456789ab")

def test_uuid_deserialise(packet):
    field = UUID()
    some_uuid = uuid.UUID("012345678-1234-1234-1234-123456789ab")
    assert field.buffer_to_value(packet, unhex("012345678123412341234123456789ab"), 0) == (some_uuid, 16)
    assert field.buffer_to_value(packet, unhex("000000012345678123412341234123456789ab"), 3) == (some_uuid, 16)

def test_uuid_deserialise_nothing(packet):
    field = UUID()
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, unhex(""), 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, unhex("00000000"), 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, unhex("0000000000000000"), 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, unhex("ffff012345678123412341234123456789"), 2)

def test_padding_serialise(packet):
    field = Padding(5)
    assert len(field.value_to_bytes(packet, None)) == 5

def test_padding_deserialise(packet):
    field = Padding(2)
    assert field.buffer_to_value(packet, b"\x00\x01\x02", 0) == (None, 2)
    assert field.buffer_to_value(packet, b"\x00\x01\x02", 1) == (None, 2)

def test_pascal_string_serialise(packet):
    field = PascalString()

    assert field.value_to_bytes(packet, "testing") == b"\x07testing"
    assert field.value_to_bytes(packet, "") == b"\x00"
    assert field.value_to_bytes(packet, "éclair") == b"\x07\xc3\xa9clair"

    # PascalString truncates strings that are too long.
    assert field.value_to_bytes(packet, "h"*256) == b"\xff" + (b"h" * 255)

def test_pascal_string_null_terminated_serialise(packet):
    field = PascalString(null_terminated=True)

    assert field.value_to_bytes(packet, "testing") == b"\x08testing\x00"
    assert field.value_to_bytes(packet, "") == b"\x01\x00"
    assert field.value_to_bytes(packet, "h"*255) == b"\xff" + (b"h" * 254) + b"\x00"
    assert field.value_to_bytes(packet, "h"*256) == b"\xff" + (b"h" * 254) + b"\x00"
    assert field.value_to_bytes(packet, "éclair") == b"\x08\xc3\xa9clair\x00"

def test_pascal_string_null_terminated_not_counted_serialise(packet):
    field = PascalString(null_terminated=True, count_null_terminator=False)

    assert field.value_to_bytes(packet, "testing") == b"\x07testing\x00"
    assert field.value_to_bytes(packet, "") == b"\x00\x00"
    assert field.value_to_bytes(packet, "h"*255) == b"\xff" + (b"h" * 255) + b"\x00"
    assert field.value_to_bytes(packet, "h"*256) == b"\xff" + (b"h" * 255) + b"\x00"
    assert field.value_to_bytes(packet, "éclair") == b"\x07\xc3\xa9clair\x00"

def test_pascal_string_deserialise(packet):
    field = PascalString()

    assert field.buffer_to_value(packet, b"\x07testing", 0) == ("testing", 8)
    assert field.buffer_to_value(packet, b"hello\x07testingfoo", 5) == ("testing", 8)
    assert field.buffer_to_value(packet, b"\x00yes", 0) == ("", 1)

def test_pascal_string_null_terminated_deserialise(packet):
    field = PascalString(null_terminated=True)

    assert field.buffer_to_value(packet, b"\x08testing\x00yes", 0) == ("testing", 9)
    assert field.buffer_to_value(packet, b"\x01\x00yes", 0) == ("", 2)

def test_pascal_string_null_terminated_not_counted(packet):
    field = PascalString(null_terminated=True, count_null_terminator=False)

    assert field.buffer_to_value(packet, b"\x07testing\x00yes", 0) == ("testing", 9)
    assert field.buffer_to_value(packet, b"\x00\x00hi", 0) == ("", 2)
    assert field.buffer_to_value(packet, b"\xff\x00\x00hi", 1) == ("", 2)

def test_pascal_string_deserialise_nothing(packet):
    field = PascalString()

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"", 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\x02!", 0)

def test_null_terminated_string_serialise(packet):
    field = NullTerminatedString()

    assert field.value_to_bytes(packet, "hello") == b"hello\x00"
    assert field.value_to_bytes(packet, "") == b"\x00"
    assert field.value_to_bytes(packet, "éclair") == b"\xc3\xa9clair\x00"

def test_null_terminated_string_deserialise(packet):
    field = NullTerminatedString()

    assert field.buffer_to_value(packet, b"hello\x00world\x00thing", 0) == ("hello", 6)
    assert field.buffer_to_value(packet, b"\x00world", 0) == ("", 1)
    assert field.buffer_to_value(packet, b"\x00", 0) == ("", 1)
    assert field.buffer_to_value(packet, b"foobar\x00", 3) == ("bar", 4)
    assert field.buffer_to_value(packet, b"\xc3\xa9clair\x00\x00", 0) == ("éclair", 8)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"hello", 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"", 0)

def test_fixed_string_no_length_serialise(packet):
    field = FixedString()

    assert field.value_to_bytes(packet, "hello") == b"hello"
    assert field.value_to_bytes(packet, "éclair") == b"\xc3\xa9clair"

def test_fixed_string_no_length_deserialise(packet):
    field = FixedString()

    assert field.buffer_to_value(packet, b"hello", 0) == ("hello", 5)
    assert field.buffer_to_value(packet, b"123\x00567\x009", 0) == ("123", 9)
    assert field.buffer_to_value(packet, b"foobarbaz", 3) == ("barbaz", 6)
    assert field.buffer_to_value(packet, b"\xc3\xa9clair", 0) == ("éclair", 7)
    assert field.buffer_to_value(packet, b"\x00\x00\x00hi", 0) == ("", 5)

def test_fixed_string_constant_length_serialise(packet):
    field = FixedString(6)

    assert field.value_to_bytes(packet, "foo") == b"foo\x00\x00\x00"
    assert field.value_to_bytes(packet, "foobar") == b"foobar"
    assert field.value_to_bytes(packet, "foobarbaz") == b"foobar"
    assert field.value_to_bytes(packet, "éclair") == b"\xc3\xa9clai"
    assert field.value_to_bytes(packet, "") == b"\x00\x00\x00\x00\x00\x00"

def test_fixed_string_constant_length_deserialise(packet):
    field = FixedString(6)

    assert field.buffer_to_value(packet, b"foobarbaz", 0) == ("foobar", 6)
    assert field.buffer_to_value(packet, b"foobarbaz", 3) == ("barbaz", 6)
    assert field.buffer_to_value(packet, b"foo\x00ba", 0) == ("foo", 6)
    assert field.buffer_to_value(packet, b"\x00\x00\x00\x00\x00\x00", 0) == ("", 6)
    assert field.buffer_to_value(packet, b"\xc3\xa9clair", 0) == ("éclai", 6)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"short", 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"foobar", 1)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"", 0)

# Defining fields outside of their associated packet doesn't normally work; the associated fields
# no longer exist by the time the packet definition is formed. This digs the required Field out
# of the internal implementation so you can do it anyway. If this is needed outside of unit testing,
# something better should be devised.
def packet_field(packet, field):
    return packet._type_mapping[field]

def test_fixed_string_variable_length_serialise(packet):
    field = FixedString(packet_field(packet, 'length'))

    field.prepare(packet, "foo")
    assert packet.length == 3
    assert field.value_to_bytes(packet, "foo") == b"foo"
    field.prepare(packet, "foobar")
    assert packet.length == 6
    assert field.value_to_bytes(packet, "foobar") == b"foobar"
    field.prepare(packet, "foobarbaz")
    assert packet.length == 9
    assert field.value_to_bytes(packet, "foobarbaz") == b"foobarbaz"
    field.prepare(packet, "éclair")
    assert packet.length == 7
    assert field.value_to_bytes(packet, "éclair") == b"\xc3\xa9clair"
    field.prepare(packet, "")
    assert packet.length == 0
    assert field.value_to_bytes(packet, "") == b""

def test_fixed_string_variable_length_deserialise(packet):
    field = FixedString(packet_field(packet, 'length'))
    packet.length = 6

    assert field.buffer_to_value(packet, b"foobarbaz", 0) == ("foobar", 6)
    assert field.buffer_to_value(packet, b"foobarbaz", 3) == ("barbaz", 6)
    assert field.buffer_to_value(packet, b"foo\x00ba", 0) == ("foo", 6)
    assert field.buffer_to_value(packet, b"\x00\x00\x00\x00\x00\x00", 0) == ("", 6)
    assert field.buffer_to_value(packet, b"\xc3\xa9clair", 0) == ("éclai", 6)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"short", 0)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"foobar", 1)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"", 0)

def test_pascal_list_no_count_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()
        bar = FixedString(default="")

    field = PascalList(Foo)

    assert field.value_to_bytes(packet, []) == b""
    assert field.value_to_bytes(packet, [Foo(foo=0xFFFF)]) == b"\x02\xFF\xFF"
    assert field.value_to_bytes(packet, [Foo(foo=0x00FF)]) == b"\x02\x00\xFF"
    assert field.value_to_bytes(packet, [Foo(foo=0x00FF), Foo(foo=0x00EE)]) == b"\x02\x00\xFF\x02\x00\xEE"
    assert field.value_to_bytes(packet, [Foo(foo=0x00FF, bar="bar"), Foo(foo=0x00EE)]) == b"\x05\x00\xFFbar\x02\x00\xEE"

    assert field.value_to_bytes(packet, [Foo(foo=0x00FF)], default_endianness='<') == b"\x02\xFF\x00"

def test_pascal_list_no_count_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()
        bar = FixedString(default="")

    field = PascalList(Foo)

    assert field.buffer_to_value(packet, b"eep", 3) == ([], 0)
    assert field.buffer_to_value(packet, b"", 0) == ([], 0)
    assert field.buffer_to_value(packet, b"\x02\xFF\xFF", 0) == ([Foo(foo=0xFFFF)], 3)
    assert field.buffer_to_value(packet, b"12345\x02\x00\xFF", 5) == ([Foo(foo=0x00FF)], 3)
    assert field.buffer_to_value(packet, b"\x02\x00\xFF\x02\x00\xEE", 0) == ([Foo(foo=0x00FF), Foo(foo=0x00EE)], 6)
    assert field.buffer_to_value(packet, b"\x05\x00\xFFbar\x02\x00\xEE", 0) == ([Foo(foo=0x00FF, bar="bar"),
                                                                                 Foo(foo=0x00EE)], 9)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\x02\xFF", 0)

def test_pascal_list_count_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint8()

    field = PascalList(Foo, count=packet_field(packet, 'count'))

    field.prepare(packet, [Foo(foo=1)])
    assert packet.count == 1
    field.value_to_bytes(packet, [Foo(foo=1)]) == b"\x01\x01"

    field.prepare(packet, [Foo(foo=1), Foo(foo=2)])
    assert packet.count == 2
    field.value_to_bytes(packet, [Foo(foo=1), Foo(foo=2)]) == b"\x01\x01\x01\x02"

def test_pascal_list_count_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint8()

    field = PascalList(Foo, count=packet_field(packet, 'count'))

    packet.count = 0
    assert field.buffer_to_value(packet, b"eep", 0) == ([], 0)

    packet.count = 1
    assert field.buffer_to_value(packet, b"foo\x01\x01nothing", 3) == ([Foo(foo=1)], 2)

    packet.count = 2
    assert field.buffer_to_value(packet, b"foo\x01\x01\x01\x02nothing", 3) == ([Foo(foo=1), Foo(foo=2)], 4)

def test_fixed_list_packet_plain_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = FixedList(Foo)

    assert field.value_to_bytes(packet, []) == b''
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB)]) == b'\xaa\xbb'
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_fixed_list_packet_plain_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = FixedList(Foo)

    assert field.buffer_to_value(packet, b"", 0) == ([], 0)
    assert field.buffer_to_value(packet, b"foo", 3) == ([], 0)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0) == ([Foo(foo=0xAABB)], 2)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0, default_endianness='<') == ([Foo(foo=0xBBAA)], 2)
    assert field.buffer_to_value(packet, b"\xaa\xbb\xcc\xdd", 0) == ([Foo(foo=0xAABB), Foo(foo=0xCCDD)], 4)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\xaa\xbb", 1)

def test_fixed_list_field_plain_serialise(packet):
    field = FixedList(Uint16())

    assert field.value_to_bytes(packet, []) == b''
    assert field.value_to_bytes(packet, [0xAABB]) == b'\xaa\xbb'
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_fixed_list_field_plain_deserialise(packet):
    field = FixedList(Uint16())

    assert field.buffer_to_value(packet, b"", 0) == ([], 0)
    assert field.buffer_to_value(packet, b"foo", 3) == ([], 0)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0) == ([0xAABB], 2)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0, default_endianness='<') == ([0xBBAA], 2)
    assert field.buffer_to_value(packet, b"\xaa\xbb\xcc\xdd", 0) == ([0xAABB, 0xCCDD], 4)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\xaa\xbb", 1)

def test_fixed_list_field_length_serialise(packet):
    field = FixedList(Uint16(), length=packet_field(packet, 'length'))

    field.prepare(packet, [])
    assert packet.length == 0
    assert field.value_to_bytes(packet, []) == b''
    field.prepare(packet, [0xAABB])
    assert packet.length == 2
    assert field.value_to_bytes(packet, [0xAABB]) == b'\xaa\xbb'
    field.prepare(packet, [0xAABB, 0xCCDD])
    assert packet.length == 6  # Because it adds on from the previous serialisation
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_fixed_list_field_length_deserialise(packet):
    field = FixedList(Uint16(), length=packet_field(packet, 'length'))

    packet.length = 0
    assert field.buffer_to_value(packet, b"", 0) == ([], 0)
    assert field.buffer_to_value(packet, b"foo", 3) == ([], 0)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0) == ([], 0)
    packet.length = 2
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0, default_endianness='<') == ([0xBBAA], 2)
    packet.length = 4
    assert field.buffer_to_value(packet, b"\xaa\xbb\xcc\xdd", 0) == ([0xAABB, 0xCCDD], 4)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\xaa\xbb", 1)

def test_fixed_list_packet_length_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = FixedList(Foo(), length=packet_field(packet, 'length'))

    field.prepare(packet, [])
    assert packet.length == 0
    assert field.value_to_bytes(packet, []) == b''
    field.prepare(packet, [Foo(foo=0xAABB)])
    assert packet.length == 2
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB)]) == b'\xaa\xbb'
    field.prepare(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)])
    assert packet.length == 6  # Because it adds on from the previous serialisation
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_fixed_list_packet_length_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = FixedList(Foo(), length=packet_field(packet, 'length'))

    packet.length = 0
    assert field.buffer_to_value(packet, b"", 0) == ([], 0)
    assert field.buffer_to_value(packet, b"foo", 3) == ([], 0)
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0) == ([], 0)
    packet.length = 2
    assert field.buffer_to_value(packet, b"\xaa\xbb", 0, default_endianness='<') == ([Foo(foo=0xBBAA)], 2)
    packet.length = 4
    assert field.buffer_to_value(packet, b"\xaa\xbb\xcc\xdd", 0) == ([Foo(foo=0xAABB), Foo(foo=0xCCDD)], 4)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b"\xaa\xbb", 1)

def test_fixed_list_field_count_deserialise(packet):
    field = FixedList(Uint16(), count=packet_field(packet, 'count'))

    field.prepare(packet, [])
    assert packet.count == 0
    assert field.value_to_bytes(packet, []) == b''
    field.prepare(packet, [0xAABB])
    assert packet.count == 1
    assert field.value_to_bytes(packet, [0xAABB]) == b'\xaa\xbb'
    field.prepare(packet, [0xAABB, 0xCCDD])
    assert packet.count == 2
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [0xAABB, 0xCCDD], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_fixed_list_packet_count_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = FixedList(Foo(), count=packet_field(packet, 'count'))

    field.prepare(packet, [])
    assert packet.count == 0
    assert field.value_to_bytes(packet, []) == b''
    field.prepare(packet, [Foo(foo=0xAABB)])
    assert packet.count == 1
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB)]) == b'\xaa\xbb'
    field.prepare(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)])
    assert packet.count == 2
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)]) == b'\xaa\xbb\xcc\xdd'
    assert field.value_to_bytes(packet, [Foo(foo=0xAABB), Foo(foo=0xCCDD)], default_endianness='<') == b'\xbb\xaa\xdd\xcc'

def test_binary_array_serialise(packet):
    field = BinaryArray()

    assert field.value_to_bytes(packet, b'foobarbaz') == b'foobarbaz'
    assert field.value_to_bytes(packet, b'foo\x00barbaz') == b'foo\x00barbaz'
    assert field.value_to_bytes(packet, b'') == b''

def test_binary_array_deserialise(packet):
    field = BinaryArray()

    assert field.buffer_to_value(packet, b'', 0) == (b'', 0)
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 0) == (b'foobar\x00baz\x00', 11)
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 3) == (b'bar\x00baz\x00', 8)

def test_binary_array_variable_ength_serialise(packet):
    field = BinaryArray(length=packet_field(packet, 'length'))

    field.prepare(packet, b'foobarbaz')
    assert packet.length == 9
    assert field.value_to_bytes(packet, b'foobarbaz') == b'foobarbaz'

    field.prepare(packet, b'foo\x00barbaz')
    assert packet.length == 10
    assert field.value_to_bytes(packet, b'foo\x00barbaz') == b'foo\x00barbaz'

    field.prepare(packet, b'')
    assert packet.length == 0
    assert field.value_to_bytes(packet, b'') == b''

def test_binary_array_variable_length_deserialise(packet):
    field = BinaryArray(length=packet_field(packet, 'length'))

    field.length = 2
    assert field.buffer_to_value(packet, b'foobar', 0) == (b'fo', 2)
    field.length = 7
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 0) == (b'foobar\x00', 7)
    field.length = 8
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 3) == (b'bar\x00baz\x00', 8)

    with pytest.raises(PacketDecodeError):
        field.length = 2
        field.buffer_to_value(packet, b'hi', 1)

def test_binary_array_fixed_length_serialise(packet):
    field = BinaryArray(length=6)

    assert field.value_to_bytes(packet, b'foobar') == b'foobar'
    assert field.value_to_bytes(packet, b'foobarbaz') == b'foobar'
    assert field.value_to_bytes(packet, b'foo\x00barbaz') == b'foo\x00ba'
    assert field.value_to_bytes(packet, b'foo') == b'foo\x00\x00\x00'

def test_binary_array_fixed_length_deserialise(packet):
    field = BinaryArray(length=6)

    assert field.buffer_to_value(packet, b'foobar', 0) == (b'foobar', 6)
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 0) == (b'foobar', 6)
    assert field.buffer_to_value(packet, b'foobar\x00baz\x00', 3) == (b'bar\x00ba', 6)

    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'fooba', 0)

def test_optional_serialise(packet):
    field = Optional(BinaryArray(length=packet_field(packet, 'length')))

    field.prepare(packet, b'A')
    assert packet.length == 1
    assert field.value_to_bytes(packet, b'A') == b'A'

def test_optional_deserialise(packet):
    field = Optional(BinaryArray(length=packet_field(packet, 'length')))

    packet.length = 1
    assert field.buffer_to_value(packet, b'ABC', 0) == (b'A', 1)
    assert field.buffer_to_value(packet, b'ABC', 1) == (b'B', 1)
    assert field.buffer_to_value(packet, b'ABC', 2) == (b'C', 1)
    assert field.buffer_to_value(packet, b'ABC', 3) == (None, 0)

def test_embed_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = Embed(Foo)
    assert field.value_to_bytes(packet, Foo(foo=0xAABB)) == b'\xAA\xBB'
    assert field.value_to_bytes(packet, Foo(foo=0xAABB), default_endianness='<') == b'\xBB\xAA'

def test_embed_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    field = Embed(Foo)
    assert field.buffer_to_value(packet, b'foo\xAA\xBBfoo', 3) == (Foo(foo=0xAABB), 2)
    assert field.buffer_to_value(packet, b'foo\xAA\xBBfoo', 3, default_endianness='<') == (Foo(foo=0xBBAA), 2)

def test_union_serialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    class Bar(PebblePacket):
        bar = FixedString(1)

    field = Union(packet_field(packet, 'command'), {
        1: Foo,
        2: Bar
    })

    field.prepare(packet, Foo(foo=0x4243))
    assert packet.command == 1
    assert field.value_to_bytes(packet, Foo(foo=0x4243)) == b'\x42\x43'
    assert field.value_to_bytes(packet, Foo(foo=0x4243), default_endianness='<') == b'\x43\x42'

    field.prepare(packet, Bar())

def test_union_deserialise(packet):
    class Foo(PebblePacket):
        foo = Uint16()

    class Bar(PebblePacket):
        bar = FixedString(1)

    field = Union(packet_field(packet, 'command'), {
        1: Foo,
        2: Bar
    })

    packet.command = 1
    assert field.buffer_to_value(packet, b'\xAA\xBB', 0) == (Foo(foo=0xAABB), 2)
    assert field.buffer_to_value(packet, b'foo\xAA\xBB', 3, default_endianness='<') == (Foo(foo=0xBBAA), 2)
    packet.command = 2
    assert field.buffer_to_value(packet, b'!', 0) == (Bar(bar='!'), 1)

    packet.command = 3
    with pytest.raises(PacketDecodeError):
        field.buffer_to_value(packet, b'!', 0)
    field.accept_missing = True
    assert field.buffer_to_value(packet, b'magic!', 2) == (None, 4)


def test_embedded_fixedlist():
    class Foo(PebblePacket):
        foo = Uint8()

    class ListOfFoo(PebblePacket):
        length = Uint8()
        foos = FixedList(Foo, length=length)

    class EmbeddedListOfFoo(PebblePacket):
        length = Uint8()
        list_of_foo = Embed(ListOfFoo, length=length)

    thing = EmbeddedListOfFoo(list_of_foo=ListOfFoo(foos=[Foo(foo=1), Foo(foo=2)]))
    thing.serialise()
    assert thing.length == 3
    assert thing.list_of_foo.length == 2

def test_embed_length_too_short():
    class Embedded(PebblePacket):
        foo = Padding(10)

    class Embedder(PebblePacket):
        embedded = Embed(Embedded, length=5)

    with pytest.raises(PacketEncodeError):
        Embedder(embedded=Embedded()).serialise()


def test_decode_embed_with_length_field():
    class Foo(PebblePacket):
        foo = Uint8(1)

    class EmbeddedListOfFoo(PebblePacket):
        length = Uint8()
        foo = Embed(Foo, length=length)
        bar = Uint8()

    result, length = EmbeddedListOfFoo.parse(b'\x01\x05\x10')
    assert result == EmbeddedListOfFoo(length=1, foo=Foo(foo=5), bar=0x10)
    assert length == 3


def test_decode_embed_with_length_constant():
    class Foo(PebblePacket):
        foo = Uint8(1)

    class EmbeddedListOfFoo(PebblePacket):
        foo = Embed(Foo, length=1)
        bar = Uint8()

    result, length = EmbeddedListOfFoo.parse(b'\x05\x10')
    assert result == EmbeddedListOfFoo(foo=Foo(foo=5), bar=0x10)
    assert length == 2


def test_fixed_length_array():
    class Foo(PebblePacket):
        array = BinaryArray(length=2)

    result = Foo(array=b'hi').serialise()
    assert result == b'hi'


def test_unbounded_length_array():
    class Foo(PebblePacket):
        array = BinaryArray()

    result = Foo(array=b'hello world').serialise()
    assert result == b'hello world'


def test_serialise_bitfield():
    class Foo(PebblePacket):
        class Meta:
            endianness = '<'

        a = Bitfield(Uint32(), 6)
        b = Bitfield(Uint32(), 11)
        c = Bitfield(Uint32(), 7)

    assert Foo(a=0,  b=0,    c=0  ).serialise() == b'\x00\x00\x00'
    assert Foo(a=0,  b=0,    c=64 ).serialise() == b'\x00\x00\x80'
    assert Foo(a=0,  b=0,    c=127).serialise() == b'\x00\x00\xfe'
    assert Foo(a=0,  b=0,    c=1  ).serialise() == b'\x00\x00\x02'
    assert Foo(a=0,  b=1024, c=0  ).serialise() == b'\x00\x00\x01'
    assert Foo(a=0,  b=1,    c=0  ).serialise() == b'\x40\x00\x00'
    assert Foo(a=0,  b=2047, c=0  ).serialise() == b'\xc0\xff\x01'
    assert Foo(a=32, b=0,    c=0  ).serialise() == b'\x20\x00\x00'
    assert Foo(a=1,  b=0,    c=0  ).serialise() == b'\x01\x00\x00'
    assert Foo(a=63, b=0,    c=0  ).serialise() == b'\x3f\x00\x00'
    assert Foo(a=63, b=2047, c=127).serialise() == b'\xff\xff\xff'
    assert Foo(a=1,  b=1,    c=1  ).serialise() == b'\x41\x00\x02'


def test_serialise_middle_bitfield():
    class Foo(PebblePacket):
        class Meta:
            endianness = '<'

        a = Bitfield(Uint8(), 2)
        b = Bitfield(Uint8(), 4)
        c = Bitfield(Uint8(), 2)

    assert Foo(a=2, b=8, c=2).serialise() == b'\xa2'
    assert Foo(a=1, b=1, c=1).serialise() == b'\x45'


def test_deserialise_middle_bitfield():
    class Foo(PebblePacket):
        class Meta:
            endianness = '<'

        a = Bitfield(Uint8(), 2)
        b = Bitfield(Uint8(), 4)
        c = Bitfield(Uint8(), 2)

    assert Foo.parse(b'\xa2') == (Foo(a=2, b=8, c=2), 1)
    assert Foo.parse(b'\x45') == (Foo(a=1, b=1, c=1), 1)


def test_deserialise_bitfield():
    class Foo(PebblePacket):
        class Meta:
            endianness = '<'

        a = Bitfield(Uint32(), 6)
        b = Bitfield(Uint32(), 11)
        c = Bitfield(Uint32(), 7)

    assert Foo.parse(b'\x00\x00\x00') == (Foo(a=0,  b=0,    c=0  ), 3)
    assert Foo.parse(b'\x00\x00\x80') == (Foo(a=0,  b=0,    c=64 ), 3)
    assert Foo.parse(b'\x00\x00\xfe') == (Foo(a=0,  b=0,    c=127), 3)
    assert Foo.parse(b'\x00\x00\x02') == (Foo(a=0,  b=0,    c=1  ), 3)
    assert Foo.parse(b'\x00\x00\x01') == (Foo(a=0,  b=1024, c=0  ), 3)
    assert Foo.parse(b'\x40\x00\x00') == (Foo(a=0,  b=1,    c=0  ), 3)
    assert Foo.parse(b'\xc0\xff\x01') == (Foo(a=0,  b=2047, c=0  ), 3)
    assert Foo.parse(b'\x20\x00\x00') == (Foo(a=32, b=0,    c=0  ), 3)
    assert Foo.parse(b'\x01\x00\x00') == (Foo(a=1,  b=0,    c=0  ), 3)
    assert Foo.parse(b'\x3f\x00\x00') == (Foo(a=63, b=0,    c=0  ), 3)
    assert Foo.parse(b'\xff\xff\xff') == (Foo(a=63, b=2047, c=127), 3)
    assert Foo.parse(b'\x41\x00\x02') == (Foo(a=1,  b=1,    c=1  ), 3)
