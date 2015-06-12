from __future__ import absolute_import
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
    def queue_events(self, event):
        pass

    @abstractmethod
    def broadcast_event(self, event, *args):
        pass


class BaseEventQueue(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass


