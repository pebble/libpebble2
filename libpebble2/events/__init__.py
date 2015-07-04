from __future__ import absolute_import
__author__ = 'katharine'

from six import with_metaclass

from abc import ABCMeta, abstractmethod


class BaseEventHandler(with_metaclass(ABCMeta)):
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


class BaseEventQueue(with_metaclass(ABCMeta)):
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass


