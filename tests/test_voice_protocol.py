from __future__ import absolute_import

__author__ = 'andrews'

import unittest
import uuid
import array
from binascii import hexlify

from libpebble2.protocol.voice import *


class TestVoiceProtocol(unittest.TestCase):

    def test_session_setup_command(self):
        # this test is a bit of a sanity check to ensure that the voice control endpoint description works with the
        # pebble protocol definition methodology

        attributes = []
        app_uuid = uuid.uuid4()
        attributes.append(Attribute(data=AppUuid(uuid=app_uuid)))
        encoder_info = Attribute(data=SpeexEncoderInfo(version="1.2rc1",
                                                       sample_rate=16000,
                                                       bit_rate=12800,
                                                       bitstream_version=4,
                                                       frame_size=320
                                                       ))
        attributes.append(encoder_info)
        attr_list = AttributeList(dictionary=attributes)
        packet = VoiceControlCommand(flags=1, data=SessionSetupCommand(session_type=SessionType.Dictation,
                                                                       session_id=0x55, attributes=attr_list))
        data = [0x01,                    # Message ID: Session setup
                0x01, 0x00, 0x00, 0x00,  # flags
                0x01,                    # Dictation session
                0x55, 0x00,              # Audio streaming session ID

                0x02,                    # attribute list - num attributes

                0x03,                    # attribute id - app uuid
                16, 0x00,
                ]
        serial = array.array('B', data).tostring() + app_uuid.bytes
        data = [0x01,                    # attribute id - attribute info speex
                0x1D, 0x00,              # attribute length
                ord('1'), ord('.'), ord('2'), ord('r'), ord('c'), ord('1'), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0x80, 0x3e, 0x00, 0x00,
                0x00, 0x32,
                0x04,
                0x40, 0x01]
        serial += array.array('B', data).tostring()
        self.assertEqual(serial, packet.serialise())

        cmd = VoiceControlCommand.parse(packet.serialise())[0]

        self.assertEqual(cmd.flags, 1)
        self.assertEqual(cmd.command, Command.SessionSetup)
        self.assertIsInstance(cmd.data, SessionSetupCommand)
        setup = cmd.data
        self.assertEqual(setup.session_type, SessionType.Dictation)
        self.assertEqual(setup.session_id, 0x55)
        self.assertEqual(setup.attributes.count, 2)
        attributes = setup.attributes.dictionary
        self.assertIsInstance(attributes[0].data, AppUuid)
        self.assertIsInstance(attributes[1].data, SpeexEncoderInfo)
        self.assertEqual(attributes[0].data.uuid, app_uuid)
        self.assertEqual(attributes[1].data.version, "1.2rc1")
        self.assertEqual(attributes[1].data.sample_rate, 16000)
        self.assertEqual(attributes[1].data.bit_rate, 12800)
        self.assertEqual(attributes[1].data.bitstream_version, 4)
        self.assertEqual(attributes[1].data.frame_size, 320)


    def test_session_setup_result(self):
        data = [0x01,                    # Message ID: Session setup
                0x01, 0x00, 0x00, 0x00,  # flags
                0x01,                    # Dictation session
                0x00
                ]
        serial = array.array('B', data).tostring()

        msg = VoiceControlResult(flags=1, data=SessionSetupResult(session_type=SessionType.Dictation,
                                                                  result=Result.Success))
        self.assertEqual(serial, msg.serialise())


    def test_transcription(self):
        expected = [
            # Transcription
            0x01,         # Transcription type
            0x02,         # Sentence count

            # Sentence #1
            0x02, 0x00,   # Word count

            # Word #1
            85,           # Confidence
            0x05, 0x00,   # Word length
            ord('H'), ord('e'), ord('l'), ord('l'), ord('o'),

            # Word #2
            74,           # Confidence
            0x08, 0x00,   # Word length
            ord('c'), ord('o'), ord('m'), ord('p'), ord('u'), ord('t'), ord('e'), ord('r'),

            # Sentence #2
            0x03, 0x00,   # Word count

            # Word #1
            13,           # Confidence
            0x04, 0x00,   # Word length
            ord('h'), ord('e'), ord('l'), ord('l'),

            # Word #1
            3,           # Confidence
            0x02, 0x00,   # Word length
            ord('o'), ord('h'),

            # Word #2
            0,           # Confidence
            0x07, 0x00,   # Word length
            ord('c'), ord('o'), ord('m'), ord('p'), ord('u'), ord('t'), ord('a')
        ]

        expected = array.array('B', expected).tostring()
        s1 = [Word(confidence=85, data="Hello"), Word(confidence=74, data="computer")]
        s2 = [Word(confidence=13, data="hell"), Word(confidence=3, data="oh"), Word(confidence=0, data="computa")]

        t = Transcription(transcription=SentenceList(sentences=[Sentence(words=s1), Sentence(words=s2)]))
        self.assertEqual(expected, t.serialise(default_endianness='<'))

    def test_dictation_result(self):
        app_uuid = uuid.uuid4()
        expected = [
            0x02,         # Message ID: Dictation result
            0x01, 0x00, 0x00, 0x00,  # flags
            0x11, 0x22,   # Audio streaming session ID
            0x00,         # Dictation result - success
        
            0x02,         # attribute list - num attributes

            0x03,         # attribute type - app uuid
            0x10, 0x00,   # attribute length
        ]
        expected = array.array('B', expected).tostring() + app_uuid.bytes
        transcription = [
            0x02,         # attribute type - transcription
            0x2F, 0x00,   # attribute length

            # Transcription
            0x01,         # Transcription type
            0x02,         # Sentence count

            # Sentence #1
            0x02, 0x00,   # Word count

            # Word #1
            85,           # Confidence
            0x05, 0x00,   # Word length
            ord('H'), ord('e'), ord('l'), ord('l'), ord('o'),

            # Word #2
            74,           # Confidence
            0x08, 0x00,   # Word length
            ord('c'), ord('o'), ord('m'), ord('p'), ord('u'), ord('t'), ord('e'), ord('r'),

            # Sentence #2
            0x03, 0x00,   # Word count

            # Word #1
            13,           # Confidence
            0x04, 0x00,   # Word length
            ord('h'), ord('e'), ord('l'), ord('l'),

            # Word #1
            3,           # Confidence
            0x02, 0x00,   # Word length
            ord('o'), ord('h'),

            # Word #2
            0,           # Confidence
            0x07, 0x00,   # Word length
            ord('c'), ord('o'), ord('m'), ord('p'), ord('u'), ord('t'), ord('a')
        ]
        expected += array.array('B', transcription).tostring()

        s1 = [Word(confidence=85, data="Hello"), Word(confidence=74, data="computer")]
        s2 = [Word(confidence=13, data="hell"), Word(confidence=3, data="oh"), Word(confidence=0, data="computa")]

        t = Transcription(type=TranscriptionType.SentenceList,
                          transcription=SentenceList(sentences=[Sentence(words=s1), Sentence(words=s2)]))
        attr_list = AttributeList(dictionary=[Attribute(data=AppUuid(uuid=app_uuid)), Attribute(data=t)])
        msg = VoiceControlResult(flags=1,
                                 data=DictationResult(session_id=0x2211, result=Result.Success, attributes=attr_list))
        self.assertEqual(expected, msg.serialise())


if __name__ == '__main__':
    unittest.main()
