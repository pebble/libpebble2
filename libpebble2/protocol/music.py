from __future__ import absolute_import
__author__ = 'katharine'

from .base import PebblePacket
from .base.types import *

__all__ = ["MusicControlPlayPause", "MusicControlPause", "MusicControlPlay", "MusicControlNextTrack",
           "MusicControlPreviousTrack", "MusicControlVolumeUp", "MusicControlVolumeDown", "MusicControlGetCurrentTrack",
           "MusicControlUpdateCurrentTrack", "MusicControl"]


class MusicControlPlayPause(PebblePacket):
    pass


class MusicControlPlay(PebblePacket):
    pass


class MusicControlPause(PebblePacket):
    pass


class MusicControlNextTrack(PebblePacket):
    pass


class MusicControlPreviousTrack(PebblePacket):
    pass


class MusicControlVolumeUp(PebblePacket):
    pass


class MusicControlVolumeDown(PebblePacket):
    pass


class MusicControlGetCurrentTrack(PebblePacket):
    pass


class MusicControlUpdateCurrentTrack(PebblePacket):
    artist = PascalString()
    album = PascalString()
    title = PascalString()


class MusicControl(PebblePacket):
    class Meta:
        endpoint = 0x20
        endianness = '<'

    command = Uint8()
    data = Union(command, {
        0x01: MusicControlPlayPause,
        0x02: MusicControlPause,
        0x03: MusicControlPlay,
        0x04: MusicControlNextTrack,
        0x05: MusicControlPreviousTrack,
        0x06: MusicControlVolumeUp,
        0x07: MusicControlVolumeDown,
        0x08: MusicControlGetCurrentTrack,
        0x10: MusicControlUpdateCurrentTrack,
    })
