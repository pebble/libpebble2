from __future__ import absolute_import
__author__ = 'katharine'

from libpebble2.protocol.blobdb import BlobDatabaseID
from libpebble2.protocol.legacy2 import *
from libpebble2.protocol.timeline import *
from libpebble2.services.blobdb import BlobDBClient, SyncWrapper

import struct
import time
import uuid


NotificationSource = LegacyNotification.Source


class Notifications(object):
    """
    Sends notifications.

    .. note:
       If a :class:`BlobDBClient` already exists for the given :class:`PebbleConnection`, you should pass that in here
       to avoid conflicts.

    :param pebble: The Pebble to send a notification to.
    :type pebble: .PebbleConnection
    :param blobdb: An existing :class:`BlobDBClient`, if any. If necessary, one will be created.
    """
    def __init__(self, pebble, blobdb=None):
        self._pebble = pebble
        self._blobdb = blobdb or BlobDBClient(pebble)

    def send_notification(self, subject="", message="", sender="", source=None, actions=None):
        """
        Sends a notification. Blocks as long as necessary.

        :param subject: The subject.
        :type subject: str
        :param message: The message.
        :type message: str
        :param sender: The sender.
        :type sender: str
        :param source: The source of the notification
        :type source: .LegacyNotification.Source
        :param actions Actions to be sent with a notification (list of TimelineAction objects)
        :type actions list
        """
        if self._pebble.firmware_version.major < 3:
            self._send_legacy_notification(subject, message, sender, source)
        else:
            self._send_modern_notification(subject, message, sender, source, actions)

    def _send_legacy_notification(self, subject, message, sender, source):
        if source is None:
            source = LegacyNotification.Source.SMS
        ts = str(int(time.time() * 1000))
        self._pebble.send_packet(LegacyNotification(type=source, timestamp=ts, subject=subject, body=message,
                                                    sender=sender))

    def _send_modern_notification(self, subject, message, sender, source, additional_actions):
        source_map = {
            None: 1,
            NotificationSource.Email: 19,
            NotificationSource.Facebook: 11,
            NotificationSource.SMS: 45,
            NotificationSource.Twitter: 6,
        }
        attributes = [
            TimelineAttribute(attribute_id=0x01, content=sender.encode('utf-8')),
            TimelineAttribute(attribute_id=4, content=struct.pack('<I', source_map[source]))
        ]
        if message:
            attributes.append(TimelineAttribute(attribute_id=0x03, content=message.encode('utf-8')))

        attributes.append(TimelineAttribute(attribute_id=0x02, content=subject.encode('utf-8')))
        item_id = uuid.uuid4()

        actions = [TimelineAction(action_id=0, type=TimelineAction.Type.Dismiss,
                                  attributes=[
                                      TimelineAttribute(attribute_id=0x01, content=b"Dismiss")
                                  ])
                   ]
        if additional_actions:
            actions.extend(additional_actions)

        notification = TimelineItem(
            item_id=item_id,
            parent_id=uuid.UUID(int=0),
            timestamp=time.time(),
            duration=0,
            type=TimelineItem.Type.Notification,
            flags=0,
            layout=0x01,
            attributes=attributes,
            actions=actions
        )
        SyncWrapper(self._blobdb.insert, BlobDatabaseID.Notification, item_id, notification.serialise()).wait()
