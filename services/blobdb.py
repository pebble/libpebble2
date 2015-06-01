__author__ = 'katharine'

from collections import namedtuple, OrderedDict
import random
import threading
import time
from Queue import Queue

from events import EventSourceMixin
from protocol.blobdb import *

__all__ = ["BlobDBClient", "SyncWrapper"]


class BlobDBClient(EventSourceMixin):
    _PendingItem = namedtuple('_PendingItem', ('token', 'data', 'callback'))
    _PendingAck = namedtuple('_PendingAck', ('timestamp', 'data', 'callback'))

    def __init__(self, pebble, event_handler, timeout=5):
        self._pebble = pebble
        self._timeout = timeout
        self._pending_ack = OrderedDict()
        self._queue = Queue()
        self._lock = threading.Lock()
        self._running = True
        self._pebble.register_endpoint(BlobResponse, self._handle_response)
        self._start_threads()
        EventSourceMixin.__init__(self, event_handler)

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
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=InsertCommand(key=key.bytes, value=value)),
                                        callback))

    def delete(self, database, key, callback=None):
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=DeleteCommand(key=key.bytes)),
                                        callback))

    def clear(self, database, callback=None):
        token = self._get_token()
        self._enqueue(self._PendingItem(token, BlobCommand(token=token, database=database,
                                                           content=ClearCommand()),
                                        callback))

    def _check_pending_acks(self):
        while self._running:
            with self._lock:
                # check pending acks
                now = time.time()
                for token, pending in self._pending_ack.items():
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
    def __init__(self, method, *args, **kwargs):
        self.event = threading.Event()
        self.result = None
        method(*args, callback=self.callback, **kwargs)

    def wait(self):
        self.event.wait()
        return self.result

    def callback(self, *args, **kwargs):
        self.result = args[0]
        self.event.set()
