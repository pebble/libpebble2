from __future__ import absolute_import
__author__ = 'katharine'

from libpebble2.protocol.appglance import *
from libpebble2.protocol.blobdb import BlobDatabaseID
from libpebble2.services.blobdb import BlobDBClient, SyncWrapper

import time


class AppGlances(object):
    """
    Reloads app glances.

    .. note:
       If a :class:`BlobDBClient` already exists for the given :class:`PebbleConnection`, you should pass that in here
       to avoid conflicts.

    :param pebble: The Pebble to send an app glance reload message to.
    :type pebble: .PebbleConnection
    :param blobdb: An existing :class:`BlobDBClient`, if any. If necessary, one will be created.
    """
    def __init__(self, pebble, blobdb=None):
        self._pebble = pebble
        self._blobdb = blobdb or BlobDBClient(pebble)

    def reload_glance(self, target_app, slices=None):
        """
        Reloads an app's glance. Blocks as long as necessary.

        :param target_app: The UUID of the app for which to reload its glance.
        :type target_app: ~uuid.UUID
        :param slices: The slices with which to reload the app's glance.
        :type slices: list[.AppGlanceSlice]
        """
        glance = AppGlance(
            version=1,
            creation_time=time.time(),
            slices=(slices or [])
        )
        SyncWrapper(self._blobdb.insert, BlobDatabaseID.AppGlance, target_app, glance.serialise()).wait()
