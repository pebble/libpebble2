from __future__ import absolute_import, division, print_function

from enum import IntEnum

from .base import PebblePacket
from .base.types import *

__author__ = 'katharine'


class HealthSample(PebblePacket):
    class Meta:
        endianness = '<'

    steps = Uint8()
    orientation = Uint8()
    vmc = Uint16()
    light = Uint8()
    flags = Optional(Uint8())


class HealthRecord(PebblePacket):
    class Meta:
        endianness = '<'

    version = Uint16()
    time_utc = Uint32()
    time_local_offset_15_min = Uint8()
    sample_size = Uint8()
    num_samples = Uint8()
    samples = FixedList(HealthSample, count=num_samples, member_length=sample_size)


class SleepRecord(PebblePacket):
    version = Uint16()
    utc_offset = Uint32()
    start_utc = Uint32()
    end_utc = Uint32()
    restful_secs = Uint32()


class ActivitySettings(PebblePacket):
    class Gender(IntEnum):
        Female = 0
        Male = 1
        Other = 2

    height_mm = Uint16()
    weight_dag = Uint16()
    activity_tracking = Boolean()
    activity_insights = Boolean()
    sleep_insights = Boolean()
    age_years = Uint8()
    gender = Uint8(enum=Gender)
