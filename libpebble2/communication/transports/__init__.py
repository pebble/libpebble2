__author__ = 'katharine'

from six import with_metaclass

from abc import ABCMeta, abstractmethod, abstractproperty


class MessageTarget(object):
    pass


class MessageTargetWatch(object):
    pass


class BaseTransport(with_metaclass(ABCMeta)):
    TARGET_WATCH = 'watch'

    @abstractproperty
    def must_initialise(self):
        pass

    @abstractproperty
    def connected(self):
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
