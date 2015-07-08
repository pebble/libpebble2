AppMessage
==========

The AppMessage service is primarily used for interacting with apps via the Pebble AppMessage protocol. AppMessage
represents messages as flat dictionaries, with integer keys and arbitrary values. Because AppMessage dictionary values
express more type information than Python types can, wrappers are provided for the relevant types.

.. automodule:: libpebble2.services.appmessage
    :members: