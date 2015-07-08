BlobDB
======

The BlobDB service provides a mechanism for interacting with the Pebble BlobDB service. The service handles
multiple messages in flight, retries, and provides callbacks for completion and failure. A :class:`.SyncWrapper` is
provided that can be passed any blobdb method and will block until it completes.

.. automodule:: libpebble2.services.blobdb
    :members:
