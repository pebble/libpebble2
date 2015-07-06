========================
libpebble2 documentation
========================

.. toctree::
   :hidden:

   connection
   transports
   protocol

libpebble2 is a python library for interacting with Pebble devices. It:

* Supports connections to Pebble QEMU instances and to watches via the Pebble mobile app
* Supports connection to watches running both 2.x and 3.x firmware on aplite or basalt hardware
* Provides automatic serialisation and deserialisation of pebble protocol messages
* Asynchronous information is provided by a usable event system
* Features a simple DSL for defining new message types
* Provides ready-made implementations several Pebble Protocol services, including BlobDB and app installation
* Works on Python 2.7 and 3.4

Getting Started
===============

Installation
------------

``pip install libpebble2``, or grab the source from https://github.com/pebble/libpebble2

Usage
-----

Connecting: ::

   >>> from libpebble2.communication import PebbleConnection
   >>> from libpebble2.communication.transports.websocket import WebsocketTransport
   >>> pebble = PebbleConnection(WebsocketTransport("ws://192.168.0.204:9000/"))
   >>> pebble.connect()
   >>> pebble.run_async()
   >>> pebble.watch_info.serial
   u'Q306175E006V'

Sending and receiving messages: ::

   >>> from libpebble2.protocol import *
   >>> pebble.send_packet(PingPong(message=Ping(), cookie=53))
   >>> pebble.read_from_endpoint(PingPong)
   PingPong(command=1, cookie=53, message=Pong())

Installing an app: ::

   >>> from libpebble2.services.install import AppInstaller
   >>> AppInstaller(pebble, "some_app.pbw").install()

Components
==========

libpebble2 is split into a number of components.

Communication and transports
----------------------------

libpebble2 provides a :class:`.PebbleConnection` to connect to a Pebble. This class manages all Pebble Protocol
communication, but does not itself know how to establish a connection to one. Connecting to a Pebble is handled by
the transports, :class:`.QemuTransport` and :class:`.WebsocketTransport`. It is possible to define new transports if
necessary.

Protocol
--------

The protocol layer provides serialisation and deserialisation of Pebble Protocol messages (and, in fact, any arbitrary
packed structure). It provides a simple DSL for defining messages: ::

   class WatchFirmwareVersion(PebblePacket):
       timestamp = Uint32()
       version_tag = FixedString(32)
       git_hash = FixedString(8)
       is_recovery = Boolean()
       hardware_platform = Uint8()
       metadata_version = Uint8()

Most messages are defined by the library in the :mod:`.protocol` package, but defining more is easy.

Services
--------

Some watch services are more complex than one or two messages. For these, services are provided to reduce effort. ::

   >>> import png  # from pypng
   >>> image = Screenshot(pebble).grab_image()
   >>> png.from_array(image, mode="RGB;8").save("screenshot.png")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

