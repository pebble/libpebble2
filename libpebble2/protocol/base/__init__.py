from __future__ import print_function, absolute_import
__author__ = 'katharine'

from six import with_metaclass, iteritems

from binascii import hexlify
import collections
import logging
import struct

from libpebble2.exceptions import IncompleteMessage
from .types import Field, DEFAULT_ENDIANNESS

__all__ = ["PebblePacket"]

logger = logging.getLogger("libpebble2.protocol")

_PacketRegistry = {}


def make_output(thing):
    class C(object):
        def __repr__(self):
            return thing
    return C()


class PacketType(type):
    """
    Metaclass for :class:`PebblePacket` that transforms properties that are subclasses of :class:`Field` into a
    Pebble Protocol parser.
    """
    def __new__(mcs, name, bases, dct):
        mapping = []
        # If we have a _Meta property, delete it.
        if '_Meta' in dct:
            del dct['_Meta']
        # If we have a Meta property, move it to _Meta. This effectively prevents it being inherited.
        if 'Meta' in dct:
            dct['_Meta'] = dct['Meta'].__dict__
            del dct['Meta']

        # For each Field, add it to our mapping, then set the exposed value to its default value.
        # We go through the classes we inherited from to add anything in there.
        # This means that inheritance works, with inherited classes appending their fields to the end.
        dct['_type_mapping'] = collections.OrderedDict()
        for base in bases:
            if hasattr(base, '_type_mapping'):
                dct['_type_mapping'].update(getattr(base, '_type_mapping'))
        for k, v in iteritems(dct):
            if not isinstance(v, Field):
                continue
            v._name = k
            mapping.append((k, v))
            dct[k] = v._default
        # Put the results into an ordered dict. We sort on field_id to ensure that our dict ends up
        # in the correct order.
        dct['_type_mapping'].update(collections.OrderedDict(sorted(mapping, key=lambda x: x[1].field_id)))
        return super(PacketType, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, name, bases, dct):
        # At this point we actually have a references to the class, so we can register it
        # in our packet type registry for later decoding.
        if hasattr(cls, '_Meta'):
            if 'endpoint' in cls._Meta and cls._Meta.get('register', True):
                _PacketRegistry[cls._Meta['endpoint']] = cls
        # Fill in all of the fields with a reference to this class.
        # TODO: This isn't used any more; remove it?
        for k, v in iteritems(cls._type_mapping):
            v._parent = cls
        super(PacketType, cls).__init__(name, bases, dct)

    def __repr__(self):
        return self.__name__


class PebblePacket(with_metaclass(PacketType)):
    """
    Represents some sort of Pebble Protocol message.

    A PebblePacket can have an inner class named ``Meta`` containing some information about the property:

    ==================  ===============================================================================================
    **endpoint**        The Pebble Protocol endpoint that is represented by this message.
    **endianness**      The endianness of the packet. The default endianness is big-endian, but it can be overridden by
                        packets and fields, with the priority:
    **register**        If set to ``False``, the packet will not be registered and thus will be ignored by
                        :meth:`parse_message`. This is useful when messages are ambiguous, and distinguished only by
                        whether they are sent to or from the Pebble.
    ==================  ===============================================================================================

    A sample packet might look like this: ::

       class AppFetchResponse(PebblePacket):
           class Meta:
               endpoint = 0x1771
               endianness = '<'
               register = False

           command = Uint8(default=0x01)
           response = Uint8(enum=AppFetchStatus)

    :param \*\*kwargs: Initial values for any properties on the object.
    """
    def __init__(self, **kwargs):
        for k, v in iteritems(kwargs):
            if k.startswith('_'):
                raise AttributeError("You cannot set internal properties during construction.")
            getattr(self, k)  # Throws an exception if the property doesn't exist.
            setattr(self, k, v)

    def serialise(self, default_endianness=None):
        """
        Serialise a message, without including any framing.

        :param default_endianness: The default endianness, unless overridden by the fields or class metadata.
                                   Should usually be left at ``None``. Otherwise, use ``'<'`` for little endian and
                                   ``'>'`` for big endian.
        :type default_endianness: str
        :return: The serialised message.
        :rtype: bytes
        """
        # Figure out an endianness.
        endianness = (default_endianness or DEFAULT_ENDIANNESS)
        if hasattr(self, '_Meta'):
            endianness = self._Meta.get('endianness', endianness)

        # Some fields want to manipulate other fields that appear before them (e.g. Unions)
        for k, v in iteritems(self._type_mapping):
            v.prepare(self, getattr(self, k))

        message = b''
        for k, v in iteritems(self._type_mapping):
            message += v.value_to_bytes(self, getattr(self, k), default_endianness=endianness)
        return message

    def serialise_packet(self):
        """
        Serialise a message, including framing information inferred from the ``Meta`` inner class of the packet.
        ``self.Meta.endpoint`` must be defined to call this method.

        :return: A serialised message, ready to be sent to the Pebble.
        """
        if not hasattr(self, '_Meta'):
            raise ReferenceError("Can't serialise a packet that doesn't have an endpoint ID.")
        serialised = self.serialise()
        return struct.pack('!HH', len(serialised), self._Meta['endpoint']) + serialised

    @classmethod
    def parse_message(cls, message):
        """
        Parses a message received from the Pebble. Uses Pebble Protocol framing to figure out what sort of packet
        it is. If the packet is registered (has been defined and imported), returns the deserialised packet, which will
        not necessarily be the same class as this. Otherwise returns ``None``.

        Also returns the length of the message consumed during deserialisation.

        :param message: A serialised message received from the Pebble.
        :type message: bytes
        :return: ``(decoded_message, decoded length)``
        :rtype: (:class:`PebblePacket`, :any:`int`)
        """
        length = struct.unpack_from('!H', message, 0)[0] + 4
        if len(message) < length:
            raise IncompleteMessage()
        command, = struct.unpack_from('!H', message, 2)
        if command in _PacketRegistry:
            return _PacketRegistry[command].parse(message[4:length])[0], length
        else:
            return None, length

    @classmethod
    def parse(cls, message, default_endianness=DEFAULT_ENDIANNESS):
        """
        Parses a message without any framing, returning the decoded result and length of message consumed. The result
        will always be of the same class as :meth:`parse` was called on. If the message is invalid,
        :exc:`.PacketDecodeError` will be raised.

        :param message: The message to decode.
        :type message: bytes
        :param default_endianness: The default endianness, unless overridden by the fields or class metadata.
                                   Should usually be left at ``None``. Otherwise, use ``'<'`` for little endian and
                                   ``'>'`` for big endian.
        :return: ``(decoded_message, decoded length)``
        :rtype: (:class:`PebblePacket`, :any:`int`)
        """
        obj = cls()
        offset = 0
        if hasattr(cls, '_Meta'):
            default_endianness = cls._Meta.get('endianness', default_endianness)
        for k, v in iteritems(cls._type_mapping):
            try:
                value, length = v.buffer_to_value(obj, message, offset, default_endianness=default_endianness)
            except Exception:
                logger.warning("Exception decoding {}.{}".format(cls.__name__, k))
                raise
            offset += length
            setattr(obj, k, value)
        return obj, offset

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__,
                           ', '.join('%s=%s' % (k, self._format_repr(getattr(self, k))) for k in self._type_mapping.keys()))

    def __eq__(self, other):
        if not isinstance(other, PebblePacket):
            return NotImplemented

        if type(self) != type(other):
            return False

        for k in self._type_mapping:
            if getattr(self, k) != getattr(other, k):
                return False

        return True

    def __ne__(self, other):
        return not (self == other)

    def _format_repr(self, value):
        if isinstance(value, bytes):
            if len(value) < 20:
                return hexlify(value).decode()
            else:
                return hexlify(value[:17]).decode() + '...'
        else:
            return value
