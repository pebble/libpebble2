from __future__ import division

from six.moves import range

import array

CRC_POLY = 0x04C11DB7


def process_word(data, crc=0xffffffff):
    if len(data) < 4:
        d_array = array.array('B', data)
        for x in range(0, 4 - len(data)):
            d_array.insert(0, 0)
        d_array.reverse()
        data = d_array.tostring()

    d = array.array('I', data)[0]
    crc = crc ^ d

    for i in range(0, 32):
        if (crc & 0x80000000) != 0:
            crc = (crc << 1) ^ CRC_POLY
        else:
            crc = (crc << 1)

    result = crc & 0xffffffff
    return result


def process_buffer(buf, c=0xffffffff):
    word_count = len(buf) // 4
    if len(buf) % 4 != 0:
        word_count += 1

    crc = c
    for i in range(0, word_count):
        crc = process_word(buf[i * 4:(i + 1) * 4], crc)
    return crc


def crc32(data):
    return process_buffer(data)


def crc8(data):
    lookup_table = [0, 47, 94, 113, 188, 147, 226, 205, 87, 120, 9, 38, 235, 196, 181, 154]

    crc = 0
    data = bytearray(data)
    data_len = len(data)
    for i in range(0, data_len * 2):
        nibble = data[data_len - (i // 2) - 1]
        if i % 2 == 0:
            nibble >>= 4
        index = nibble ^ (crc >> 4)
        crc = lookup_table[index & 0xf] ^ ((crc << 4) & 0xf0)

    return crc
