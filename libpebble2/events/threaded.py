from __future__ import absolute_import

__author__ = 'katharine'

import threading
from six.moves import queue

from . import BaseEventHandler, BaseEventQueue
from libpebble2.exceptions import TimeoutError


class ThreadedEventHandler(BaseEventHandler):
    """
    A threaded implementation of :class:`.BaseEventHandler`.
    """
    def __init__(self):
        self._handlers = {}
        self._handle_map = {}
        self._counter = 0
        self._handler_lock = threading.RLock()

    def register_handler(self, event, handler):
        with self._handler_lock:
            self._counter += 1
            self._handlers.setdefault(event, {})[self._counter] = handler
            self._handle_map[self._counter] = event
            return self._counter

    def unregister_handler(self, handle):
        with self._handler_lock:
            if handle not in self._handle_map:
                return
            del self._handlers[self._handle_map[handle]][handle]
            del self._handle_map[handle]

    def wait_for_event(self, event, timeout=10):
        return _BlockingEventWait(self, event).wait(timeout=timeout)

    def queue_events(self, event):
        return _QueuedEventWait(self, event)

    def broadcast_event(self, event, *args):
        for handler in list(self._handlers.get(event, {}).values()):
            handler(*args)


class _BlockingEventWait(object):
    def __init__(self, events, event):
        self.block = threading.Event()
        self.event_handler = events
        self.result = None
        self.handle = self.event_handler.register_handler(event, self.handle_result)

    def handle_result(self, *args):
        self.result, = args
        self.event_handler.unregister_handler(self.handle)
        self.block.set()

    def wait(self, timeout=10):
        if not self.block.wait(timeout=timeout):
            raise TimeoutError()
        return self.result


class _QueuedEventWait(BaseEventQueue):
    def __init__(self, events, event):
        self.queue = queue.Queue()
        self.event_handler = events
        self.handle = self.event_handler.register_handler(event, self._handle_event)

    def _handle_event(self, arg):
        self.queue.put(arg)

    def close(self):
        self.event_handler.unregister_handler(self.handle)

    def get(self, timeout=10):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError()

    def __iter__(self):
        yield self.get()
