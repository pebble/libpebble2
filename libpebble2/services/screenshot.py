from __future__ import absolute_import, division
__author__ = 'katharine'

from array import array

from libpebble2.exceptions import PebbleError
from libpebble2.events import EventSourceMixin
from libpebble2.protocol.screenshots import *


class ScreenshotError(PebbleError):
    pass


class Screenshot(EventSourceMixin):
    def __init__(self, pebble, event_class):
        self._pebble = pebble
        super(Screenshot, self).__init__(event_class)

    def grab_image(self):
        self._pebble.send_packet(ScreenshotRequest())
        return self._read_screenshot()

    def _read_screenshot(self):
        data = self._pebble.read_from_endpoint(ScreenshotResponse).data
        header = ScreenshotHeader.parse(data)[0]
        if header.response_code != ScreenshotHeader.ResponseCode.OK:
            raise ScreenshotError("Screenshot failed: {!s}".format(header.response_code))
        data = header.data
        expected_size = self._get_expected_bytes(header)
        queue = self._pebble.get_endpoint_queue(ScreenshotResponse)
        while len(data) < expected_size:
            data += queue.get().data
            self._broadcast_event("progress", len(data), expected_size)
        queue.close()
        return self._decode_image(header, data)

    @classmethod
    def _get_expected_bytes(cls, header):
        if header.version == 1:
            return (header.width * header.height) // 8
        elif header.version == 2:
            return header.width * header.height
        else:
            raise ScreenshotError("Unknown screenshot version: {}".format(header.version))

    @classmethod
    def _decode_image(cls, header, data):
        if header.version == 1:
            return cls._decode_1bit(header, data)
        elif header.version == 2:
            return cls._decode_8bit(header, data)

    @classmethod
    def _decode_1bit(cls, header, data):
        output = []
        row_bytes = header.width // 8
        for row in xrange(header.height):
            row_values = []
            for column in xrange(header.width):
                pixel = (data[row*row_bytes + column//8] >> (7 - (column % 8))) & 1
                row_values.extend([pixel * 255] * 3)
            output.append(array('B', row_values))
        return output

    @classmethod
    def _decode_8bit(cls, header, data):
        output = []
        for row in xrange(header.height):
            row_values = []
            for column in xrange(header.width):
                pixel = data[row*header.width + column]
                row_values.extend([
                    ((pixel >> 4) & 0b11) * 85,
                    ((pixel >> 2) & 0b11) * 85,
                    ((pixel >> 0) & 0b11) * 85,
                ])
            output.append(array('B', row_values))
        return output
