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


class GetBytesError(PebbleError):
    """
    A getbytes session failed.
    """
    def __init__(self, code):
        self.code = code
        PebbleError.__init__(self, "Failed to get bytes: {!s}".format(code))


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


class PacketEncodeError(PebbleError):
    """
    Encoding a packet failed.
    """
    pass


class ConnectionError(PebbleError):
    """
    Connecting to the Pebble failed.
    """
    pass


class IncompleteMessage(PebbleError):
    pass
