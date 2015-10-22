from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.exceptions import PutBytesError
from libpebble2.protocol import transfers
from libpebble2.util import stm32_crc

__all__ = ["PutBytes", "PutBytesType"]


class PutBytesType(IntEnum):
    Firmware = 1
    Recovery = 2
    SystemResources = 3
    Resources = 4
    Binary = 5
    File = 6
    Worker = 7


class PutBytes(EventSourceMixin):
    """
    Synchronously sends data to the watch over PutBytes.

    :param pebble: The Pebble to send data to.
    :type pebble: .PebbleConnection
    :param object_type: The type of data being sent.
    :type object_type: .PutBytesType
    :param object: The data to send.
    :type object: bytes
    :param bank: The bank to install the data to, if applicable.
    :type bank: int
    :param filename: The filename of the data, if applicable
    :type filename: str
    :param app_install_id: This is used during app installations on 3.x. It is mutually exclusive with ``bank`` and
        ``filename``.
    :type app_install_id: int
    """
    def __init__(self, pebble, object_type, object, bank=None, filename="", app_install_id=None):
        self._pebble = pebble
        self._object_type = object_type
        self._object = object
        self._bank = bank
        self._filename = filename
        self._app_install_id = app_install_id
        if app_install_id is not None:
            self._object_type |= (1 << 7)
        EventSourceMixin.__init__(self)

    def send(self):
        """
        Sends the object to the watch. Block until completion, or raises :exc:`.PutBytesError` on failure.

        During transmission, a "progress" event will be periodically emitted with the following signature: ::

           (sent_this_interval, sent_so_far, total_object_size)
        """
        # Prepare the watch to receive something.
        cookie = self._prepare()

        # Send it.
        self._send_object(cookie)

        # Commit it.
        self._commit(cookie)

        # Install it.
        self._install(cookie)

    def _assert_success(self, result):
        if result.result == transfers.PutBytesResponse.Result.NACK:
            raise PutBytesError("Watch NACKed PutBytes request.")

    def _prepare(self):
        if self._app_install_id is not None:
            packet = transfers.PutBytesApp(data=transfers.PutBytesAppInit(
                object_size=len(self._object), object_type=self._object_type, app_id=self._app_install_id))
        else:
            packet = transfers.PutBytes(data=transfers.PutBytesInit(
                object_size=len(self._object), object_type=self._object_type, bank=self._bank, filename=self._filename))
        result = self._pebble.send_and_read(packet, transfers.PutBytesResponse)
        self._assert_success(result)
        return result.cookie

    def _send_object(self, cookie):
        sent = 0
        length = 2000
        while sent < len(self._object):
            chunk = self._object[sent:sent+length]
            packet = transfers.PutBytes(data=transfers.PutBytesPut(cookie=cookie, payload=chunk))
            self._assert_success(self._pebble.send_and_read(packet, transfers.PutBytesResponse))
            sent += len(chunk)
            self._broadcast_event("progress", len(chunk), sent, len(self._object))

    def _commit(self, cookie):
        crc = stm32_crc.crc32(self._object)
        packet = transfers.PutBytes(data=transfers.PutBytesCommit(cookie=cookie, object_crc=crc))
        self._assert_success(self._pebble.send_and_read(packet, transfers.PutBytesResponse))

    def _install(self, cookie):
        packet = transfers.PutBytes(data=transfers.PutBytesInstall(cookie=cookie))
        self._assert_success(self._pebble.send_and_read(packet, transfers.PutBytesResponse))
