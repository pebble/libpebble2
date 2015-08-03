from __future__ import absolute_import
__author__ = 'andrews'

import threading
import uuid

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.protocol.voice import *
from libpebble2.protocol.audio import *

__all__ = ["VoiceServer"]


class VoiceServer(EventSourceMixin):
    SESSION_ID_INVALID = 0

    def __init__(self, pebble, timeout):
        self._pebble = pebble
        self._session_id = VoiceServer.SESSION_ID_INVALID
        self._lock = threading.Lock()

        self._pebble.register_endpoint(VoiceControlCommand, self._handle_voice_control)
        self._pebble.register_endpoint(AudioStream, self._handle_audio)

        EventSourceMixin.__init__(self)

    def _handle_voice_control(self, packet):
        assert isinstance(packet, VoiceControlCommand)
        if isinstance(packet.data, SessionSetupCommand):
            self._handle_session_setup(packet.flags, packet.data)

    def _handle_audio(self, packet):
        pass

    def _handle_session_setup(self, flags, message):
        if (message.session_type != SessionType.Dictation) or (message.session_id == VoiceServer.SESSION_ID_INVALID) or \
                (message.attributes.is_empty()) or \
                (message.attributes.get_attribute(AttributeType.SpeexEncoderInfo) is None):
            return

        with self._lock:
            if self._session_id != VoiceServer.SESSION_ID_INVALID:
                return

            app_initiated = (flags & 0x1 != 0)
            app_uuid = message.attributes.get_attribute(AttributeType.AppUuid)
            app_uuid_present = app_uuid is not None
            if app_initiated != app_uuid_present:
                return

            self._app_uuid = app_uuid
            self._session_id = message.session_id
            self._encoder_info = message.attributes.get_attribute(AttributeType.SpeexEncoderInfo)
            if self._encoder_info is None:
                return

            self._broadcast_event("voice:session_setup", self._session_id, self._app_uuid, self._encoder_info)

    def _handle_audio(self, packet):
        assert isinstance(packet, AudioStream)
        if isinstance(packet.data, DataTransfer):
            self._handle_audio_frame(packet.session_id, packet.data)
        elif isinstance(packet.data, StopTransfer):
            self._handle_stop_transfer(packet.session_id)

    def _handle_audio_frame(self, session_id, frame_data):
        if session_id != self._session_id:
            self.send_stop_audio(session_id)
        else:
            # this should actually store the data, but for now we'll just stop the transmission
            self.send_stop_audio(session_id)
            self._broadcast_event("voice:audio_stop", self._session_id)

    def _handle_stop_transfer(self, session_id):
        if session_id == self._session_id:
            self._broadcast_event("voice:audio_stop", self._session_id)

    def send_stop_audio(self):
        self._pebble.send_packet(AudioStream(session_id=self._session_id, message=StopTransfer()))

    def send_session_setup_result(self, app_uuid, result):
        assert isinstance(app_uuid, uuid.UUID)
        assert isinstance(result, Result)

        flags = 0 if app_uuid is None else 1
        self._pebble.send_packet(VoiceControlResult(flags=flags, message=SessionSetupResult(
            session_type=SessionType.Dictation, result=result)))

    def send_dictation_result(self, app_uuid, result, transcription):
        assert isinstance(result, Result)
        # assert isinstance(transcription, Transcription)

        flags = 0 if app_uuid is None else 1
        attributes = []
        if app_uuid is not None:
            assert isinstance(app_uuid, uuid.UUID)
            attributes.append(Attribute(id=AttributeType.AppUuid, data=app_uuid))

        attributes.append(Attribute(id=AttributeType.Transcription, data=transcription))

        self._pebble.send_packet(VoiceControlResult(flags=flags, message=DictationResult(
            session_id=self._session_id, result=result)))
