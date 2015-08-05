Voice
=====

This service handles voice control endpoint messages, parses the data and exposes it for external tools. It also allows
voice control messages to be sent to a Pebble. It does not implement the state machine for ordering voice control
messages correctly: this must be handled by the user of the service.

The service exposes the following events, which can be subscribed to with VoiceServer.register_handler:

* ``session_setup`` - Session setup request received
* ``audio_frame`` - Audio data frame received
* ``audio_stop`` - Audio data stopped

Voice Protocol Sequencing:
--------------------------
The correct sequencing for communicating with the Pebble smartwatch is as follows:

**Watch-terminated sessions:**

This is the normal sequence of communication. The Server should wait until it receives a stop message from the watch before sending the dictation result.

====================== ======== ==========================================
Message                Sender   Event/Function
====================== ======== ==========================================
Session setup request  Watch    ``session_setup``
Session setup result   Server   ``VoiceService.send_session_setup_result``
Audio data (n frames)  Watch    ``audio_frame``
Audio stop             Watch    ``audio_stop``
Dictation result       Server   ``VoiceService.send_dictation_result``
====================== ======== ==========================================

**Server-terminated sessions:**

If an error occurs a server can terminate the session by sending an audio stop message followed by the dictation result. The dictation result should always be sent.

====================== ======== ==========================================
Message                Sender   Event/Function
====================== ======== ==========================================
Session setup request  Watch    ``session_setup``
Session setup result   Server   ``VoiceService.send_session_setup_result``
Audio data (n frames)  Watch    ``audio_frame``
Audio stop             Server   ``VoiceService.send_stop_audio``
Dictation result       Server   ``VoiceService.send_dictation_result``
====================== ======== ==========================================

.. automodule:: libpebble2.services.voice
    :members:
    :inherited-members: