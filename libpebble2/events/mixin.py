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
        """
        Registers a handler to be triggered by an event

        :param event: The event to handle
        :param handler: The handler callable.
        :return: A handle that can be used to unregister the handler.
        """
        return self.__handler.register_handler(event, handler)

    def unregister_handler(self, handle):
        """
        Unregisters an event handler.

        :param handle: The handle returned from :meth:`register_handler`
        """
        self.__handler.unregister_handler(handle)

    def wait_for_event(self, event, timeout=10):
        """
        Block waiting for the given event. Returns the event params.

        :param event: The event to handle.
        :return: The event params.
        :param timeout: The maximum time to wait before raising :exc:`.TimeoutError`.
        """
        return self.__handler.wait_for_event(event, timeout=timeout)

    def _broadcast_event(self, event, *args):
        return self.__handler.broadcast_event(event, *args)
