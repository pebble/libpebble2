__author__ = 'katharine'
from .version import __version__, __version_info__

import logging

from .exceptions import *

logging.getLogger('libpebble2').addHandler(logging.NullHandler())
