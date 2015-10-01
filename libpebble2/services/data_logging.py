from __future__ import absolute_import

import logging
import datetime

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.protocol.data_logging import *
from libpebble2.exceptions import TimeoutError

logger = logging.getLogger("libpebble2.services.data_logging")

class DataLoggingService(EventSourceMixin):
    """
    Supports various data logging functions

    :param pebble: The :class:`PebbleConnection` over which to communicate
    :type pebble: .PebbleConnection
    """
    def __init__(self, pebble):
        self._pebble = pebble
        super(DataLoggingService, self).__init__()

    def list(self):
        """
        List all available data logging sessions
        """

        # We have to open this queue before we make the request, to ensure we don't miss the response.
        queue = self._pebble.get_endpoint_queue(DataLogging)

        self._pebble.send_packet(DataLogging(data=DataLoggingReportOpenSessions(sessions=[])))

        sessions = []
        while True:
            try:
                result = queue.get(timeout=2).data
            except TimeoutError:
                break
            if isinstance(result, DataLoggingDespoolOpenSession):
                self._pebble.send_packet(DataLogging(data=DataLoggingACK(
                                                     session_id=result.session_id)))
                sessions.append(result.__dict__)

        queue.close()
        return sessions


    def download(self, session_id):
        """
        Download a specific session. 
        Returns (session_info, data)
        """

        # We have to open this queue before we make the request, to ensure we don't miss the response.
        queue = self._pebble.get_endpoint_queue(DataLogging)

        # First, we need to open up all sessions
        self._pebble.send_packet(DataLogging(data=DataLoggingReportOpenSessions(sessions=[])))

        session = None
        while True:
            try:
                result = queue.get(timeout=2).data
            except TimeoutError:
                break

            if isinstance(result, DataLoggingDespoolOpenSession):
                self._pebble.send_packet(DataLogging(data=DataLoggingACK(
                                                          session_id=result.session_id)))
                if session is None and result.session_id == session_id:
                    session = result

        if session is None:
            queue.close()
            return (None, None)


        # -----------------------------------------------------------------------------
        # Request an empty of this session
        logger.info("Requesting empty of session {}".format(session_id))
        self._pebble.send_packet(DataLogging(data=DataLoggingEmptySession(session_id=session_id)))
        data = None
        timeout_count = 0
        while True:
            logger.debug("Looping again. Time: {}".format(datetime.datetime.now()))
            try:
                result = queue.get(timeout=5).data
                timeout_count = 0
            except TimeoutError:
                logger.debug("Got timeout error Time: {}".format(datetime.datetime.now()))
                timeout_count += 1
                if timeout_count >= 2:
                    break
                else:
                    self._pebble.send_packet(DataLogging(data=DataLoggingEmptySession(
                                             session_id=session_id)))
                    continue

            if isinstance(result, DataLoggingDespoolSendData):
                if result.session_id != session_id:
                    self._pebble.send_packet(DataLogging(
                        data=DataLoggingNACK(session_id=result.session_id)))
                else:
                    logger.info("Received {} bytes of data: {}".format(len(result.data), result))
                    if data is None:
                        data = result.data
                    else:
                        data += result.data
                    self._pebble.send_packet(DataLogging(
                                             data=DataLoggingACK(session_id=session_id)))

        queue.close()
        return (session, data)


    def get_send_enable(self):
        """
        Return true if sending of sessions is enabled on the watch
        """

        # We have to open this queue before we make the request, to ensure we don't miss the response.
        queue = self._pebble.get_endpoint_queue(DataLogging)

        self._pebble.send_packet(DataLogging(data=DataLoggingGetSendEnableRequest()))
        enabled = False
        while True:
            result = queue.get().data
            if isinstance(result, DataLoggingGetSendEnableResponse):
                enabled = result.enabled
                break

        queue.close()
        return enabled


    def set_send_enable(self, setting):
        """
        Set the send enable setting on the watch
        """
        self._pebble.send_packet(DataLogging(data=DataLoggingSetSendEnable(enabled=setting)))

