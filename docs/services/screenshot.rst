Screenshots
===========

This service takes screenshots and returns them in 8-bit ARGB format. The resulting images are lists of bytearrays,
but can easily be converted to PNGs using `pypng <https://pypi.python.org/pypi/pypng>`_: ::

   import png
   image = Screenshot(pebble).grab_image()
   png.from_array(image).save('screenshot.png')

.. automodule:: libpebble2.services.screenshot
    :members:
    :inherited-members:
