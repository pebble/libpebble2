from __future__ import absolute_import
__author__ = 'katharine'

from .base import PebblePacket
from .base.types import *

__all__ = ["AnswerCall", "HangUpCall", "PhoneStateRequest", "IncomingCall", "OutgoingCall", "MissedCall",
           "Ring", "CallStart", "CallEnd", "CallStateItem", "PhoneStateResponse", "PhoneNotification"]


class AnswerCall(PebblePacket):
    pass


class HangUpCall(PebblePacket):
    pass


class PhoneStateRequest(PebblePacket):
    pass


class IncomingCall(PebblePacket):
    number = PascalString()
    name = PascalString()


class OutgoingCall(PebblePacket):
    pass


class MissedCall(PebblePacket):
    number = PascalString()
    name = PascalString()


class Ring(PebblePacket):
    pass


class CallStart(PebblePacket):
    pass


class CallEnd(PebblePacket):
    pass


class CallStateItem(PebblePacket):
    command_id = Uint8()
    cookie = Uint32()
    item = Union(command_id, {
        0x04: IncomingCall,
        0x05: OutgoingCall,
        0x08: CallStart,
    })


class PhoneStateResponse(PebblePacket):
    items = PascalList(CallStateItem)


class PhoneNotification(PebblePacket):
    class Meta:
        endpoint = 0x21

    command_id = Uint8()
    cookie = Uint32()
    message = Union(command_id, {
        0x01: AnswerCall,
        0x02: HangUpCall,
        0x03: PhoneStateRequest,
        0x83: PhoneStateResponse,
        0x04: IncomingCall,
        0x05: OutgoingCall,
        0x06: MissedCall,
        0x07: Ring,
        0x08: CallStart,
        0x09: CallEnd,
    })
