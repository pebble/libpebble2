__author__ = 'katharine'

import logging

from .exceptions import *

logging.getLogger('libpebble2').addHandler(logging.NullHandler())
