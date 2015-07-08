from __future__ import absolute_import
__author__ = 'katharine'

from collections import namedtuple, OrderedDict
import random
import threading
import time
from six.moves.queue import Queue

from libpebble2.events.mixin import EventSourceMixin
from libpebble2.protocol.blobdb import *

__all__ = ["BlobDBClient", "SyncWrapper"]


class BlobDBClient(EventSourceMixin):
    """
    Provides a mechanism for interacting with the Pebble's BlobDB service. All methods are asynchronous.
    Messages will be retried automatically if they time out, but all error responses from the watch
    are considered final and will be reported.

    If you want to interact synchronously with BlobDB, see :class:`SyncWrapper`.

    .. note:
       Avoid having multiple :class:`BlobDBClient` instances attached to a single :class:`PebbleConnection`.
       They are likely to interfere and cause failures.

    :param pebble: The pebble to connect to.
    :type pebble: .PebbleConnection
    :param timeout: The timeout before resending a BlobDB command.
    :type timeout: int
    """
    _PendingItem = namedtuple('_PendingItem', ('token', 'data', 'callback'))
    _PendingAck = namedtuple('_PendingAck', ('timestamp', 'data', 'callback'))

    def __init__(self, pebble, timeout=5):
        self._pebble = pebble
        self._timeout = timeout
        self._pending_ack = OrderedDict()
        self._queue = Queue()
        self._lock = threading.Lock()
        self._running = True
        self._pebble.register_endpoint(BlobResponse, self._handle_response)
        self._start_threads()
        EventSourceMixin.__init__(self)

    def _start_threads(self):
        self._pending_ack_thread = threading.Thread(target=self._check_pending_acks)
        self._pending_ack_thread.daemon = True
        self._pending_ack_thread.start()

        self._queued_data_thread = threading.Thread(target=self._send_queued_data)
        self._queued_data_thread.daemon = True
        self._queued_data_thread.start()

    def _enqueue(self, item):
        self._queue.put(item)

    def insert(self, database, key, value, callback=None):
        """
        Insert an item into the given database.

        :param database: The database into which to insert the value.
        :type database: .BlobDatabaseID
        :param key: The key to insert.
        :type key: uuid.UUID
        :param value: The value to insert.
        :type value: bytes
        :param callback: A callback to be called on success or failure.
        """
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=InsertCommand(key=key.bytes, value=value)),
                                        callback))

    def delete(self, database, key, callback=None):
        """
        Delete an item from the given database.

        :param database: The database from which to delete the value.
        :type database: .BlobDatabaseID
        :param key: The key to delete.
        :type key: uuid.UUID
        :param callback: A callback to be called on success or failure.
        """
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=DeleteCommand(key=key.bytes)),
                                        callback))

    def clear(self, database, callback=None):
        """
        Wipe the given database. This only affects items inserted remotely; items inserted on the watch
        (e.g. alarm clock timeline pins) are not removed.

        :param database: The database to wipe.
        :type database: .BlobDatabaseID
        :param callback: A callback to be called on success or failure.
        """
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=ClearCommand()),
                                        callback))

    def _check_pending_acks(self):
        while self._running:
            with self._lock:
                # check pending acks
                now = time.time()
                for token, pending in list(self._pending_ack.items()):
                    if now - pending.timestamp > self._timeout:
                        del self._pending_ack[token]
                        self._enqueue(self._PendingItem(token, pending.data, pending.callback))
            time.sleep(5)

    def _send_queued_data(self):
        while True:
            token, data, callback = self._queue.get()
            with self._lock:
                self._pending_ack[token] = self._PendingAck(time.time(), data, callback)
                self._pebble.send_packet(data)
            time.sleep(0.05)

    def _get_token(self):
        return random.randrange(1, 2**16 - 1, 1)

    def _handle_response(self, packet):
        with self._lock:
            if packet.token in self._pending_ack:
                pending = self._pending_ack[packet.token]
                del self._pending_ack[packet.token]
                if callable(pending.callback):
                    pending.callback(packet.response)


class SyncWrapper(object):
    """
    Wraps a :class:`BlobDBClient` call and returns when it completes.

    Use it like this: ::

       SyncWrapper(blobdb_client.insert, some_key, some_value).wait()

    :param method: The method to call.
    :param args: Arguments to pass to the method.
    """
    def __init__(self, method, *args, **kwargs):
        self.event = threading.Event()
        self.result = None
        method(*args, callback=self.callback, **kwargs)

    def wait(self, timeout=10):
        self.event.wait(timeout=timeout)
        return self.result

    def callback(self, *args, **kwargs):
        self.result = args[0]
        self.event.set()
