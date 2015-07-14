from __future__ import absolute_import
__author__ = 'katharine'

import errno
import serial
import struct

from . import BaseTransport, MessageTargetWatch
from libpebble2.exceptions import ConnectionError


class SerialTransport(BaseTransport):
    """
    Represents a direct connection to a physical Pebble paired to the computer via Bluetooth serial.
    This transport expects to be given a device file over which it can communicate with the watch via Bluetooth.

    .. warning::
        Using this transport may cause occasional kernel panics on some versions of OS X.

    :param device: The path to the device file (on OS X, often of the form ``/dev/cu.PebbleTimeXXXX-SerialPo`` or
                   ``/dev/cu.PebbleXXXX-SerialPortSe``).
    :type device: str
    """
    must_initialise = True

    def __init__(self, device):
        self.device = device
        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(self.device, 115200)
        except OSError as e:
            if e.errno == errno.EBUSY:
                raise ConnectionError("Could not connect to Pebble.")
            else:
                raise

    @property
    def connected(self):
        return self.connection is not None and self.connection.isOpen()

    def read_packet(self):
        try:
            data = self.connection.read(2)
        except serial.SerialException:
            self.connection.close()
            raise ConnectionError("Disconnected from watch.")
        if len(data) < 2:
            raise ConnectionError("Got malformed packet.")

        length, = struct.unpack('!H', data)
        data += self.connection.read(length + 2)
        return MessageTargetWatch(), data

    def send_packet(self, message, target=MessageTargetWatch()):
        assert isinstance(target, MessageTargetWatch)
        self.connection.write(message)
