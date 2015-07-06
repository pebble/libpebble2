Connections
===========

Connections to the Pebble are represented by the :class:`PebbleConnection`, connecting via a
:doc:`transport <transports>`.

Event loops
-----------

Having connected to a Pebble, the event loop must be run for anything interesting to occur. There are three ways to do
this:

Fire and forget
~~~~~~~~~~~~~~~

:meth:`.PebbleConnection.run_async` will spawn a new thread (called ``PebbleConnection``) and run the event loop on that
thread. It handles expected exceptions and will emit :mod:`log messages <logging>` at the ``WARNING`` level. It will
also call :meth:`.PebbleConnection.fetch_watch_info` on your behalf before returning. This is the easiest
option, and often what you want. ::

   pebble.connect()
   pebble.run_async()

Blocking forever
~~~~~~~~~~~~~~~~

:meth:`PebbleConnection.run_sync` will run the event loop in place. It will handle exceptions for you and emit logs
at the ``WARNING`` level. It will not return until the watch disconnects or an error occurs. ::

   pebble.connect()
   pebble.run_sync()

Do it manually
~~~~~~~~~~~~~~

Calling :meth:`PebbleConnection.pump_reader` will (synchronously) cause exactly one message to be read from the
transport, which may or may not be a message from the Pebble. It will fire all of the events for that message, and
then return. It doesn't return anything. ::

   pebble.connect()
   while pebble.connected:
       pebble.pump_reader()

.. note:: :meth:`pump_reader <PebbleConnection.pump_reader>` may throw exceptions on receiving malformed messages; these
          should probably be handled.

API
---

.. automodule:: libpebble2.communication
    :members:
