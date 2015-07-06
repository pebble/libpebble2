__author__ = 'katharine'

from six import with_metaclass

from abc import ABCMeta, abstractmethod, abstractproperty


class MessageTarget(object):
    def __repr__(self):
        return type(self).__name__ + "()"


class MessageTargetWatch(MessageTarget):
    pass


class BaseTransport(with_metaclass(ABCMeta)):
    @abstractproperty
    def must_initialise(self):
        """
        :return: ``True`` if libpebble2 is responsible for negotiating the connection; otherwise ``False``.
        """
        pass

    @abstractproperty
    def connected(self):
        """
        :return: ``True`` if the transport is currently connected; otherwise ``False``.
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Synchronously connect to the Pebble. Once this method returns, libpebble2 should be able to safely send
        messages to the connected Pebble.

        Ordinarily, this method should only be called by :class:`.PebbleConnection`.
        """
        pass

    @abstractmethod
    def read_packet(self):
        """
        Synchronously read a message. This message could be from the Pebble(in which case it will be a
        :class:`PebblePacket`), or it could be from the transport, in which case the result is transport-defined.
        The origin of the result is indicated by the returned :class:`MessageTarget`.

        :return: (:class:`MessageTarget`, :class:`libpebble2.protocol.base.PebblePacket`)
        """
        pass

    @abstractmethod
    def send_packet(self, message, target=MessageTargetWatch()):
        """
        Send a message. This message could be to the Pebble (in which case it must be a :class:`PebblePacket`), or
        to the transport (in which case the message type is transport-defined).

        :param message: Message to send.
        :type message: PebblePacket
        :param target: Target for the message
        :type target: MessageTarget
        """
        pass
