__author__ = 'katharine'


class PebbleError(Exception):
    """
    The base class for all exceptions raised by libpebble2.
    """
    pass


class AppInstallError(PebbleError):
    """
    An app install failed.
    """
    pass


class PutBytesError(PebbleError):
    """
    A putbytes session failed.
    """
    pass


class ScreenshotError(PebbleError):
    """
    A screenshot failed.
    """
    pass


class TimeoutError(PebbleError):
    """
    Something was waiting for an event and timed out.
    """
    pass


class PacketDecodeError(PebbleError):
    """
    Decoding a packet received from the Pebble failed.
    """
    pass


class ConnectionError(PebbleError):
    """
    Connecting to the Pebble failed.
    """
    pass


class IncompleteMessage(PebbleError):
    pass
