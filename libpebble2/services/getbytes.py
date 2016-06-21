from __future__ import absolute_import
__author__ = 'katharine'

from array import array
from six.moves import range

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.exceptions import GetBytesError
from libpebble2.protocol.transfers import *

__all__ = ["GetBytesService"]


class GetBytesService(EventSourceMixin):
    """
    Synchronously retrieves data from the watch over GetBytes.

    :param pebble: The Pebble to send data to.
    :type pebble: .PebbleConnection
    """
    def __init__(self, pebble):
        self._pebble = pebble
        self._txid = 0
        super(GetBytesService, self).__init__()

    def get_coredump(self, require_fresh=False):
        """
        Retrieves a coredump, if one exists. Raises :exc:`.GetBytesError` on failure.

        :param require_fresh: If true, coredumps that have already been read are considered to not exist.
        :type require_fresh: bool
        :return: The retrieved coredump
        :rtype: bytes
        """
        return self._get(GetBytesUnreadCoredumpRequest() if require_fresh else GetBytesCoredumpRequest())

    def get_file(self, filename):
        """
        Retrieves a PFS file from the watch. This only works on watches running non-release firmware.
        Raises :exc:`.GetBytesError` on failure.

        :return: The retrieved file
        :rtype: bytes
        """
        return self._get(GetBytesFileRequest(filename=filename))

    def get_flash_region(self, offset, length):
        """
        Retrieves the contents of a region of flash from the watch. This only works on watches running
        non-release firmware.
        Raises :exc:`.GetBytesError` on failure.

        :return: The retrieved data
        :rtype: bytes
        """
        return self._get(GetBytesFlashRequest(offset=offset, length=length))

    def _get(self, message):
        self._txid = txid = self._txid + 1

        queue = self._pebble.get_endpoint_queue(GetBytes)
        try:
            self._pebble.send_packet(GetBytes(transaction_id=txid, message=message))
            info = queue.get().message
            assert isinstance(info, GetBytesInfoResponse)

            if info.error_code != GetBytesInfoResponse.ErrorCode.Success:
                raise GetBytesError(info.error_code)

            # Allocate a mutable array large enough to contain the data
            data = array('B', (0 for _ in range(info.num_bytes)))

            bytes_received = 0
            while bytes_received < info.num_bytes:
                part = queue.get().message
                assert isinstance(part, GetBytesDataResponse)
                bytes_received += len(part.data)

                # Insert the received chunk into our array.
                data[part.offset:part.offset+len(part.data)] = array('B', part.data)

            # Return the data as a more standard bytearray.
            return data.tostring()
        finally:
            queue.close()
