from __future__ import absolute_import, division
__author__ = 'katharine'

from six import indexbytes
from six.moves import range

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.exceptions import ScreenshotError
from libpebble2.protocol.screenshots import *


class Screenshot(EventSourceMixin):
    """
    Takes a screenshot from the watch.

    :param pebble: The pebble of which to take a screenshot.
    :type pebble: .PebbleConnection
    """
    def __init__(self, pebble):
        self._pebble = pebble
        super(Screenshot, self).__init__()

    def grab_image(self):
        """
        Takes a screenshot. Blocks until completion, or raises a :exc:`.ScreenshotError` on failure.

        While this method is executing, "progress" events will periodically be emitted with the following signature: ::

           (downloaded_so_far, total_size)

        :return: A list of bytearrays in RGB8 format, where each bytearray is one row of the image.
        """
        # We have to open this queue before we make the request, to ensure we don't miss the response.
        queue = self._pebble.get_endpoint_queue(ScreenshotResponse)
        self._pebble.send_packet(ScreenshotRequest())
        return self._read_screenshot(queue)

    def _read_screenshot(self, queue):
        data = queue.get().data
        header = ScreenshotHeader.parse(data)[0]
        if header.response_code != ScreenshotHeader.ResponseCode.OK:
            queue.close()
            raise ScreenshotError("Screenshot failed: {!s}".format(header.response_code))
        data = header.data
        expected_size = self._get_expected_bytes(header)
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
        for row in range(header.height):
            row_values = []
            for column in range(header.width):
                pixel = (indexbytes(data, row*row_bytes + column//8) >> (column % 8)) & 1
                row_values.extend([pixel * 255] * 3)
            output.append(bytearray(row_values))
        return output

    @classmethod
    def _decode_8bit(cls, header, data):
        output = []
        for row in range(header.height):
            row_values = []
            for column in range(header.width):
                pixel = indexbytes(data, row*header.width + column)
                row_values.extend([
                    ((pixel >> 4) & 0b11) * 85,
                    ((pixel >> 2) & 0b11) * 85,
                    ((pixel >> 0) & 0b11) * 85,
                ])
            output.append(bytearray(row_values))
        return output
