from __future__ import absolute_import

__author__ = 'katharine'

import threading
import Queue

from . import BaseEventHandler, BaseEventQueue


class ThreadedEventHandler(BaseEventHandler):
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

    def wait_for_event(self, event):
        return _BlockingEventWait(self, event).wait()

    def queue_events(self, event):
        return _QueuedEventWait(self, event)

    def broadcast_event(self, event, *args):
        # TODO: This could maybe deadlock?
        for handler in self._handlers.get(event, {}).values():
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

    def wait(self):
        self.block.wait()
        return self.result


class _QueuedEventWait(BaseEventQueue):
    def __init__(self, events, event):
        self.queue = Queue.Queue()
        self.event_handler = events
        self.handle = self.event_handler.register_handler(event, self._handle_event)

    def _handle_event(self, arg):
        self.queue.put(arg)

    def close(self):
        self.event_handler.unregister_handler(self.handle)

    def get(self):
        return self.queue.get()

    def __iter__(self):
        yield self.get()
