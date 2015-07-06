Protocol handling
=================

libpebble2 provides a simple DSL for defining Pebble Protocol messages, accounting for various quirks in the Pebble
Protocol, such as the four different ways of defining strings and mixed endianness.

Defining messages
-----------------

All messages inherit from :class:`.PebblePacket`, which uses metaclass magic (from :class:`.PacketType`) to parse
the definitions. An empty message would look like this: ::

   class SampleMessage(PebblePacket):
       pass

This message is not very interesting — it represents a zero-length, unidentifiable packet. Despite this, it can be
useful in conjunction with certain field types, such as :class:`Union`.

Metadata
~~~~~~~~

To add some useful information about our message, we can define a ``Meta`` inner class inside it: ::

   class SampleMessage(PebblePacket):
       class Meta:
           endpoint = 0xbead
           endianness = '<'

This defines our ``SampleMessage`` as being a little-endian Pebble Protocol message that should be sent to endpoint
0xbead.

The following attributes on ``Meta`` are meaningful (but all are optional):

* :attr:`endpoint` — defines the Pebble Protocol endpoint to which the message should be sent.
* :attr:`endianness` — defines the endianness of the message. Use ``'<'`` for little-endian or ``'>'`` for big-endian.
* :attr:`register` — if specified and ``False``, the message will not be registered for parsing when received, even if
  ``endpoint`` is specified. This can be useful if the protocol design is asymmetric and ambiguous.

.. note:: ``Meta`` is not inherited if you subclass a ``PebblePacket``. In particular, you will probably want to
          re-specify ``endianness`` when doing this. The default endianness is **big-endian**.

We can now use this class to send an empty message to the watch, or receive one back! ::

   >>> pebble.send_packet(SampleMessage())

Fields
~~~~~~

Empty messages are rarely useful. To actually send some information, we can add more attributes to our messages. For
instance, let's say we want to specify a time message that looks like this:

======  ======  ========  ====================================
Offset  Length  Type      Value
======  ======  ========  ====================================
0       4       uint32_t  Seconds since 1970 (unix time, UTC)
4       2       uint16_t  UTC offset in minutes, including DST
6       1       uint8_t   Length of the timezone region name
7       ...     char *    The timezone region name
======  ======  ========  ====================================

We could represent that packet like this: ::

   class SetUTC(PebblePacket):
       unix_time = Uint32()
       utc_offset_mins = Int16()
       tz_name = PascalString()

The lengths and offsets are determined automatically. Also notice that we didn't have to include the length explicitly
— including a length byte before a string is a sufficiently common pattern that it has a dedicated :class:`PascalString`
field. This definition works: ::

   >>> from binascii import hexlify
   >>> message = SetUTC(unix_time=1436165495, utc_offset_mins=-420, tz_name=u"America/Los_Angeles")
   >>> hexlify(message.serialise())
   '559a2577fe5c13416d65726963612f4c6f735f416e67656c6573'
   >>> SetUTC.parse('559a2577fe5c13416d65726963612f4c6f735f416e67656c6573'.decode('hex'))
   (SetUTC(unix_time=1436165495, utc_offset=-420, tz_name=America/Los_Angeles), 26)

(:meth:`~.PebblePacket.parse` returns a ``(message, consumed_bytes)`` tuple.)

Which is nice, but isn't usable as a Pebble Protocol message — after all, we don't have an endpoint. It also turns out
that this isn't *actually* a message you can send to the Pebble; rather, it's merely one of four possible messages to
the "Time" endpoint. How can we handle that? With a :class:`Union`! Let's build the whole Time message: ::

   class GetTimeRequest(PebblePacket):
       pass

   class GetTimeResponse(PebblePacket):
       localtime = Uint32()

   class SetLocaltime(PebblePacket):
       localtime = Uint32()

   class SetUTC(PebblePacket):
       unix_time = Uint32()
       utc_offset_mins = Int16()
       tz_name = PascalString()

   class TimeMessage(PebblePacket):
       class Meta:
           endpoint = 0xb
           endianness = '>'  # big endian

       command = Uint8()
       message = Union(command, {
           0x00: GetTimeRequest,
           0x01: GetTimeResponse,
           0x02: SetLocaltime,
           0x03: SetUTC,
       })

``TimeMessage`` is now our Pebble Protocol message. Its ``Meta`` class contains two pieces of information; the endpoint
and the endianness of the message (which is actually the default). It consists of two fields: a ``command``, which is just a
``uint8_t``, and a ``message``. Union applies the endianness specified in ``TimeMessage`` to the other classes it
references.

During deserialisation, the :class:`Union` will use the value of ``command`` to figure
out which member of the union to use, then use that class to parse the remainder of the message. During serialisation,
:class:`Union` will inspect the type of the provided ``message``: ::

   >>> message = TimeMessage(message=SetUTC(unix_time=1436165495, utc_offset_mins=-420, tz_name=u"America/Los_Angeles"))
   #  We don't have to set command because Union does that for us.
   >>> hexlify(message.serialise_packet())
   '001b000b03559a2577fe5c13416d65726963612f4c6f735f416e67656c6573'
   >>> PebblePacket.parse_message('001b000b03559a2577fe5c13416d65726963612f4c6f735f416e67656c6573'.decode('hex'))
   (TimeMessage(kind=3, message=SetUTC(unix_time=1436165495, utc_offset=-420, tz_name=America/Los_Angeles)), 31)
   >>> pebble.send_packet(message)

And there we go! We encoded a pebble packet, then asked the general :class:`PebblePacket` to deserialise it for us.
But wait: how did :class:`PebblePacket` know to return a ``TimeMessage``?

When defining a subclass of :class:`PebblePacket`, it will automatically be registered in an internal "packet registry"
if it has an ``endpoint`` specified. Sometimes this behaviour is undesirable; in this case, you can specify
``register = False`` to disable this behaviour.

API
---

Packets
~~~~~~~

.. autoclass:: libpebble2.protocol.base.PebblePacket
    :members:

Field types
~~~~~~~~~~~

.. autosummary::
    :nosignatures:

    ~libpebble2.protocol.base.types.Padding
    ~libpebble2.protocol.base.types.Boolean
    ~libpebble2.protocol.base.types.Uint8
    ~libpebble2.protocol.base.types.Uint16
    ~libpebble2.protocol.base.types.Uint32
    ~libpebble2.protocol.base.types.Uint64
    ~libpebble2.protocol.base.types.Int8
    ~libpebble2.protocol.base.types.Int16
    ~libpebble2.protocol.base.types.Int32
    ~libpebble2.protocol.base.types.Int64
    ~libpebble2.protocol.base.types.FixedString
    ~libpebble2.protocol.base.types.NullTerminatedString
    ~libpebble2.protocol.base.types.PascalString
    ~libpebble2.protocol.base.types.FixedList
    ~libpebble2.protocol.base.types.PascalList
    ~libpebble2.protocol.base.types.Union
    ~libpebble2.protocol.base.types.Embed

\

.. automodule:: libpebble2.protocol.base.types
    :members: