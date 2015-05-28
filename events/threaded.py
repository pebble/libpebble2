from __future__ import absolute_import

__author__ = 'katharine'

import threading

from . import BaseEventHandler


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

    def broadcast_event(self, event, *args):
        # TODO: This could maybe deadlock?
        with self._handler_lock:
            for handler in self._handlers.get(event, {}).itervalues():
                handler(*args)


class _BlockingEventWait(object):
    def __init__(self, events, event):
        self.block = threading.Event()
        self.event_handler = events
        self.result = None
        self.handle = None
        self.handle = self.event_handler.register_handler(event, self.result)

    def result(self, *args):
        self.result = args
        self.event_handler.unregister_handler(self.handle)
        self.block.set()

    def wait(self):
        self.block.wait()
        return self.result
