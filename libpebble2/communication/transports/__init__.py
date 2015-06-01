__author__ = 'katharine'

from abc import ABCMeta, abstractmethod, abstractproperty


class MessageTarget(object):
    pass


class MessageTargetWatch(object):
    pass


class BaseTransport(object):
    __metaclass__ = ABCMeta

    TARGET_WATCH = 'watch'

    @abstractproperty
    def must_initialise(self):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def read_packet(self):
        pass

    @abstractmethod
    def send_packet(self, message, target=MessageTargetWatch()):
        pass
