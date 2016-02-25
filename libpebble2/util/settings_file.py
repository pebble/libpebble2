from __future__ import absolute_import, division, print_function

from six import iteritems

import time

from libpebble2.protocol.base import PebblePacket
from libpebble2.protocol.base.types import *
from libpebble2.exceptions import PacketDecodeError
from .stm32_crc import crc8

__author__ = 'katharine'

SETTINGS_MAGIC = 7628147


class SettingsRecord(PebblePacket):
    class Meta:
        endianness = '<'

    last_modified = Uint32()
    key_hash = Uint8()
    flags = Bitfield(Uint8(), 6, default=0x3f)
    key_length = Bitfield(Uint32(), 7)
    value_length = Bitfield(Uint32(), 11)
    key = BinaryArray(length=key_length)
    value = BinaryArray(length=value_length)


class SettingsHeader(PebblePacket):
    class Meta:
        endianness = '<'

    magic = Uint32(default=SETTINGS_MAGIC)  # 'set\x00'
    version = Uint16()
    flags = Uint16(default=0xFFFF)


def _partially_written(record):
    return record.flags & 1 == 1


def _overwritten(record):
    return (record.flags & 0b10) == 0 and (record.flags & 0b100) == 0


def load(f, key_decoder=None, value_decoder=None):
    """
    Loads a settings file into a :class:`dict` from a file handle.

    :param f: A file-like object to read from.
    :type f: file
    :param key_decoder: Optionally, a function to pass keys through to decode them. If omitted, returns byte strings.
    :param value_decoder: Optionally, a function to pass values through to decode them.
                          If omitted, returns byte strings.
    :return: A dictionary containing the contents of the settings file.
    :rtype dict
    """
    return loads(f.read(), key_decoder=key_decoder, value_decoder=value_decoder)


def loads(buffer, key_decoder=None, value_decoder=None):
    """
    Loads a settings file into a :class:`dict` from a byte string.

    :param buffer: A pebble settings file, as stored in PFS.
    :type buffer: bytes
    :param key_decoder: Optionally, a function to pass keys through to decode them. If omitted, returns byte strings.
    :param value_decoder: Optionally, a function to pass values through to decode them.
                          If omitted, returns byte strings.
    :return: A dictionary containing the contents of the settings file.
    :rtype dict
    """
    header, offset = SettingsHeader.parse(buffer)
    if header.magic != SETTINGS_MAGIC:
        raise PacketDecodeError("Settings file doesn't have the right magic.")

    if header.version != 1:
        raise PacketDecodeError("Unsupported settings file version.")

    contents = {}

    while True:
        # EOF
        if buffer[offset:offset+8] == '\xff' * 8:
            break
        record, record_length = SettingsRecord.parse(buffer[offset:])
        offset += record_length
        if _overwritten(record) or _partially_written(record):
            continue

        key = key_decoder(record.key) if callable(key_decoder) else record.key
        value = value_decoder(record.value) if callable(value_decoder) else record.value
        contents[key] = value

    return contents


def dumps(content, min_length=None, key_encoder=None, value_encoder=None):
    """
    Returns a byte string containing a pebble settings file representing the provided dictionary.

    :param content: A dictionary of values to include in the settings file.
    :type content: dict
    :param key_encoder: Optionally, a function to pass keys through to encode them. If omitted, byte strings must be
                        provided as keys.
    :param value_encoder: Optionally, a function to pass values through to encode them. If omitted, byte strings must be
                          provided as values.
    :return: A byte string containing a settings file.
    :rtype: bytes
    """
    result = [SettingsHeader(version=1).serialise()]

    for k, v in iteritems(content):
        if callable(key_encoder):
            k = key_encoder(k)
        if callable(value_encoder):
            v = value_encoder(v)
        result.append(SettingsRecord(
                last_modified=int(time.time()),
                key_hash=crc8(k),
                key_length=len(k),
                value_length=len(v),
                key=k,
                value=v
        ).serialise())

    result_bytes = b''.join(result)

    return result_bytes + (b'\xff' * max(0, (min_length or 0) - len(result_bytes)))


def dump(content, f, min_length=None, key_encoder=None, value_encoder=None):
    """
    Returns a byte string containing a pebble settings file representing the provided dictionary.

    :param content: A dictionary of values to include in the settings file.
    :type content: dict
    :param f: A file-like object to write to.
    :type f: file
    :param key_encoder: Optionally, a function to pass keys through to encode them. If omitted, byte strings must be
                        provided as keys.
    :param value_encoder: Optionally, a function to pass values through to encode them. If omitted, byte strings must be
                          provided as values.
    """
    f.write(dumps(content, min_length=min_length, key_encoder=key_encoder, value_encoder=value_encoder))
