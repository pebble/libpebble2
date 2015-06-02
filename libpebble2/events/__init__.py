__author__ = 'katharine'

from abc import ABCMeta, abstractmethod


class BaseEventHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def register_handler(self, event, handler):
        pass

    @abstractmethod
    def unregister_handler(self, handle):
        pass

    @abstractmethod
    def wait_for_event(self, event):
        pass

    @abstractmethod
    def broadcast_event(self, event, *args):
        pass


class EventSourceMixin(object):
    """
    A convenient mixin to save on repeatedly exposing generic event handler functionality.
    """
    def __init__(self, handler):
        self.__handler = handler()

    def register_handler(self, event, handler):
        return self.__handler.register_handler(event, handler)

    def unregister_handler(self, handle):
        self.__handler.unregister_handler(handle)

    def wait_for_event(self, event):
        return self.__handler.wait_for_event(event)

    def _broadcast_event(self, event, *args):
        return self.__handler.broadcast_event(event, *args)
