from __future__ import absolute_import
__author__ = 'katharine'

from array import array
import struct

from libpebble2.events import EventSourceMixin
from libpebble2.protocol.appmessage import *

__all__ = ["AppMessageService", "Uint8", "Uint16", "Uint32", "Int8", "Int16", "Int32", "CString", "ByteArray"]


class AppMessageService(EventSourceMixin):
    _type_mapping = {
        (AppMessageTuple.Type.Int, 1): 'b',
        (AppMessageTuple.Type.Int, 2): 'h',
        (AppMessageTuple.Type.Int, 4): 'i',
        (AppMessageTuple.Type.Uint, 1): 'B',
        (AppMessageTuple.Type.Uint, 2): 'H',
        (AppMessageTuple.Type.Uint, 4): 'I',
    }

    def __init__(self, pebble, events):
        self._pebble = pebble
        self._current_txid = 1
        self._pending_messages = {}
        super(AppMessageService, self).__init__(events)
        self._handle = self._pebble.register_endpoint(AppMessage, self._handle_message)

    def _handle_message(self, packet):
        assert isinstance(packet, AppMessage)
        if isinstance(packet.data, AppMessagePush):
            message = packet.data
            result = {}
            for t in message.dictionary:
                assert isinstance(t, AppMessageTuple)
                if t.type == AppMessageTuple.Type.ByteArray:
                    result[t.key] = t.data
                elif t.type == AppMessageTuple.Type.CString:
                    result[t.key] = t.data.tostring().split('\x00')[0]
                else:
                    result[t.key] = struct.unpack(self._type_mapping[(t.type, t.length)], t.data.tostring())
            self._broadcast_event("appmessage", packet.transaction_id, message.uuid, result)
            self._pebble.send_packet(AppMessage(transaction_id=packet.transaction_id, message=AppMessageACK()))
        else:
            if packet.transaction_id in self._pending_messages:
                uuid = self._pending_messages[packet.transaction_id]
                del self._pending_messages[packet.transaction_id]
            else:
                uuid = None
            if isinstance(packet.data, AppMessageACK):
                self._broadcast_event("ack", packet.transaction_id, uuid)
            elif isinstance(packet.data, AppMessageNACK):
                self._broadcast_event("nack", packet.transaction_id, uuid)

    def send_message(self, target_app, dictionary):
        tid = self._get_txid()
        message = AppMessage(transaction_id=tid)
        tuples = []
        for k, v in dictionary.iteritems():
            if isinstance(v, AppMessageNumber):
                tuples.append(AppMessageTuple(key=k, type=v.type,
                                data=array('B', struct.pack(self._type_mapping[v.type, v.length], v.value))))
            elif v.type == AppMessageTuple.Type.CString:
                tuples.append(AppMessageTuple(key=k, type=v.type, data=array('B', v.value + '\x00')))
            elif v.type == AppMessageTuple.Type.ByteArray:
                tuples.append(AppMessageTuple(key=k, type=v.type, data=v.value))
        message.data = AppMessagePush(uuid=target_app, dictionary=tuples)
        self._pending_messages[tid] = target_app
        self._pebble.send_packet(message)
        return tid

    def shutdown(self):
        self._pebble.unregister_endpoint(self._handle)

    def _get_txid(self):
        self._current_txid += 1
        return self._current_txid


class AppMessageType(object):
    type = None
    length = None

    def __init__(self, value):
        self.value = value


class AppMessageNumber(AppMessageType):
    pass


class Uint8(AppMessageNumber):
    type = AppMessageTuple.Type.Uint
    length = 1


class Uint16(AppMessageNumber):
    type = AppMessageTuple.Type.Uint
    length = 2


class Uint32(AppMessageNumber):
    type = AppMessageTuple.Type.Uint
    length = 4


class Int8(AppMessageNumber):
    type = AppMessageTuple.Type.Int
    length = 1


class Int16(AppMessageNumber):
    type = AppMessageTuple.Type.Int
    length = 2


class Int32(AppMessageNumber):
    type = AppMessageTuple.Type.Int
    length = 4


class CString(AppMessageType):
    type = AppMessageTuple.Type.CString


class ByteArray(AppMessageType):
    type = AppMessageTuple.Type.ByteArray
