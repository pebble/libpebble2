Transports
==========

A transport represents a channel over which libpebble2 can communicate with a Pebble. Transports can also support
sending and receiving messages not destined for the Pebble — for instance, the WebSocket transport can install a
JavaScript app in the phone app. Two transports are currently provided, but it would be easy to add more.

Transports are usually only accessed directly by :class:`.PebbleConnection`, but it can be useful to use them
directly to interact with the transport instead of a Pebble. The transport can be accessed using the `transport`
attribute of the :class:`.PebbleConnection`.

The origin or destination of a message is indicated using a "message target". Messages to or from the watch use
:class:`MessageTargetWatch`; other transports may define additional targets of their own, which they can use to route
messages elsewhere.

BaseTransport
-------------

:class:`.BaseTransport` defines the functionality expected of any transport. All transports should inherit from
:class:`.BaseTransport`.

.. autoclass:: libpebble2.communication.transports.BaseTransport
    :members:

.. autoclass:: libpebble2.communication.transports.MessageTargetWatch
    :show-inheritance:
    :members:

.. autoclass:: libpebble2.communication.transports.MessageTarget


WebSocket transport
-------------------

The WebSocket transport connects to a phone running the Pebble mobile app using the "Developer Connection",
which exposes a WebSocket server on the phone. By default it runs on port 9000. ::

   >>> pebble = PebbleConnection(WebsocketTransport("ws://192.168.204:9000/"))

.. autoclass:: libpebble2.communication.transports.websocket.WebsocketTransport
    :show-inheritance:

.. autoclass:: libpebble2.communication.transports.websocket.MessageTargetPhone
    :show-inheritance:
    :members:

QEMU transport
--------------

The QEMU transport connects to an instance of `Pebble QEMU <https://github.com/pebble/qemu>`_ via
`Pebble QEMU Protocol <https://developer.getpebble.com/blog/2015/01/30/Development-Of-The-Pebble-Emulator/#the-qemu-channel-socket>`_.
Note that, due to how QEMU is implemented, the watch will not necessarily notice connections or disconnections over this
transport.

Messages directed at the emulator itself, rather than the firmware running on it, can be sent using
:class:`.MessageTargetQemu`. ::

   >>> pebble = PebbleConnection(QemuTransport("localhost", 12344))

.. autoclass:: libpebble2.communication.transports.qemu.QemuTransport
    :members:
    :show-inheritance:

.. autoclass:: libpebble2.communication.transports.qemu.MessageTargetQemu
    :members:
    :show-inheritance:
