from __future__ import absolute_import
__author__ = 'andrews'

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__all__ = ["AudioCodec", "SpeexEncoderInfo", "AppUuid", "Transcription", "AttributeType", "Attribute", "AttributeList",
           "SessionType", "Command", "SessionSetupCommand", "VoiceControlCommand", "Result", "SessionSetupResult",
           "DictationResult", "VoiceControlResult"]


class AudioCodec(IntEnum):
    Speex = 0x01


class SpeexEncoderInfo(PebblePacket):
    version = FixedString(20)
    sample_rate = Uint32()
    bit_rate = Uint16()
    bitstream_version = Uint8()
    frame_size = Uint16()


class Transcription(PebblePacket):
    class Word(PebblePacket):
        confidence = Uint8()
        length = Uint16()
        data = FixedString(length=length)

    class Sentence(PebblePacket):
        count = Uint16()
        words = FixedList(Transcription.Word, count=count)

    class SentenceList(PebblePacket):
        count = Uint8()
        sentences = FixedList(Transcription.Sentence, count=count)

    class TranscriptionType(IntEnum):
        SentenceList = 0x01

    type = Uint8(enum=TranscriptionType)
    transcription = Union(type, {
        TranscriptionType.SentenceList: SentenceList
    })


class AttributeType(IntEnum):
    SpeexEncoderInfo = 0x01
    Transcription = 0x02
    AppUuid = 0x03


class Attribute(PebblePacket):
    # Voice endpoint attribute (key-value pair)
    id = Uint8(enum=AttributeType)
    length = Uint16()
    data = Union(id, {
        AttributeType.SpeexEncoderInfo: SpeexEncoderInfo,
        AttributeType.Transcription: Transcription,
        AttributeType.AppUuid: UUID,
    }, length=length, accept_missing=True)



class AttributeList(PebblePacket):
    # Attribute List
    count = Uint8()
    dictionary = FixedList(Attribute, count=count)

    def get_attribute(self, id):
        if self.is_empty():
            return None

        for attr in self.dictionary:
            assert isinstance(attr, Attribute)
            if attr.id == id:
                assert isinstance(attr.data, attr.data.contents[attr.id])
                return attr.data

        return None

    def is_empty(self):
        return self.dictionary.count == 0


class SessionType(IntEnum):
    Dictation = 0x01
    Command = 0x02


class SessionSetupCommand(PebblePacket):
    session_type = Uint8(enum=SessionType)
    session_id = Uint16()
    attributes = Embed(AttributeList)


class Command(IntEnum):
    SessionSetup = 0x01
    DictationResult = 0x02


class VoiceControlCommand(PebblePacket):
    class Meta:
        endpoint = 0x2af8
        endianness = '<'

    command = Uint8(enum=Command)
    flags = Uint32()
    data = Union(command, {
        Command.SessionSetup: SessionSetupCommand,
    })


class Result(IntEnum):
    Success = 0x00
    FailServiceUnavailable = 0x01
    FailTimeout = 0x02
    FailRecognizerError = 0x03
    FailInvalidRecognizerResponse = 0x04
    FailDisabled = 0x05
    FailInvalidMessage = 0x06


class SessionSetupResult(PebblePacket):
    session_type = Uint8(enum=SessionType)
    result = Uint8(enum=Result)


class DictationResult(PebblePacket):
    session_id = Uint16()
    result = Uint8(enum=Result)
    attributes = Embed(AttributeList)


class VoiceControlResult(PebblePacket):
    class Meta:
        endpoint = 0x2af8
        endianness = '<'
        register = False

    command = Uint8(enum=Command)
    flags = Uint32()
    data = Union(command, {
        Command.SessionSetup: SessionSetupResult,
        Command.DictationResult: DictationResult
    })
