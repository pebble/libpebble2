from __future__ import absolute_import
__author__ = 'katharine'

"""
This file is special in that it actually contains definitions of
blobdb blob formats rather than pebble protocol messages.
"""

from copy import deepcopy
from enum import IntEnum

from .base import PebblePacket
from .base.types import *
from .timeline import TimelineAttribute

import struct

__all__ = ["AppGlanceSliceIconAndSubtitle", "AppGlance"]


class AppGlanceSliceType(IntEnum):
    IconAndSubtitle = 0


class AppGlanceSlice(PebblePacket):

    def __init__(self, expiration_time, slice_type, extra_attributes=None):
        attributes = []
        if extra_attributes:
            attributes.extend(deepcopy(extra_attributes))
        attributes.append(TimelineAttribute(attribute_id=37, content=struct.pack('<I', expiration_time)))

        # Add 4 bytes to account for total_size (2), type (1), and attribute_count (1)
        total_size = 4 + sum([len(attribute.serialise()) for attribute in attributes])

        super(AppGlanceSlice, self).__init__(total_size=total_size, type=slice_type, attribute_count=len(attributes),
                                             attributes=attributes)

    class Meta:
        endianness = '<'

    total_size = Uint16()
    type = Uint8(enum=AppGlanceSliceType)
    attribute_count = Uint8()
    attributes = FixedList(TimelineAttribute, count=attribute_count)


class AppGlanceSliceIconAndSubtitle(AppGlanceSlice):

    def __init__(self, expiration_time, icon=None, subtitle_template_string=None):
        attributes = []
        if icon:
            attributes.append(TimelineAttribute(attribute_id=48, content=struct.pack('<I', icon)))
        if subtitle_template_string:
            attributes.append(TimelineAttribute(attribute_id=47, content=subtitle_template_string.encode('utf-8')))
        super(AppGlanceSliceIconAndSubtitle, self).__init__(expiration_time, AppGlanceSliceType.IconAndSubtitle,
                                                            extra_attributes=attributes)


class AppGlance(PebblePacket):
    class Meta:
        endianness = '<'

    version = Uint8()
    creation_time = Uint32()
    slices = FixedList(AppGlanceSlice)
