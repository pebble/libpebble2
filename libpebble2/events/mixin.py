from __future__ import absolute_import
__author__ = 'katharine'

from libpebble2.events.threaded import ThreadedEventHandler


class EventSourceMixin(object):
    """
    A convenient mixin to save on repeatedly exposing generic event handler functionality.
    """
    def __init__(self):
        self.__handler = ThreadedEventHandler()

    def register_handler(self, event, handler):
        return self.__handler.register_handler(event, handler)

    def unregister_handler(self, handle):
        self.__handler.unregister_handler(handle)

    def wait_for_event(self, event):
        return self.__handler.wait_for_event(event)

    def _broadcast_event(self, event, *args):
        return self.__handler.broadcast_event(event, *args)
