# encoding: utf-8
from __future__ import absolute_import, unicode_literals
__author__ = 'katharine'

from uuid import UUID

from libpebble2.services.appmessage import AppMessageService
from libpebble2.protocol.appmessage import *

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


def test_receive_appmessage_string():
    pebble = Mock()

    calls = [0]
    def handle_result(txid, uuid, result):
        assert uuid == UUID(int=128)
        assert txid == 42
        assert result == {
            14: "hello!",
            15: "éclair", # null terminated -> 'foo' should be omitted.
            16: "hello\uFFFDworld", # invalid unicode -> U+FFFD REPLACEMENT CHARACTER
        }
        calls[0] += 1

    service = AppMessageService(pebble)
    service.register_handler("appmessage", handle_result)
    assert pebble.register_endpoint.call_args is not None
    callback = pebble.register_endpoint.call_args[0][1]

    callback(
        AppMessage(
            transaction_id=42,
            data=AppMessagePush(
                uuid=UUID(int=128),
                dictionary=[
                    AppMessageTuple(key=14, type=AppMessageTuple.Type.CString, data=b"hello!\x00"),
                    AppMessageTuple(key=15, type=AppMessageTuple.Type.CString,
                                    data="éclair".encode('utf-8') + b'\x00foo',),
                    AppMessageTuple(key=16, type=AppMessageTuple.Type.CString, data=b"hello\xffworld"),
                ]
            )
        )
    )
    pebble.send_packet.assert_called_once_with(AppMessage(transaction_id=42, data=AppMessageACK()))
    assert calls[0] == 1
