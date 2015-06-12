__author__ = 'katharine'


class PebbleError(Exception):
    pass


class AppInstallError(PebbleError):
    pass


class PutBytesError(PebbleError):
    pass


class ScreenshotError(PebbleError):
    pass


class TimeoutError(PebbleError):
    pass


class PacketDecodeError(PebbleError):
    pass


class ConnectionError(PebbleError):
    pass
