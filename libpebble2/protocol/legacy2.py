from __future__ import absolute_import
__author__ = 'katharine'

from enum import IntEnum

from .appmessage import AppMessage
from .base import PebblePacket
from .base.types import *

__all__ = ["LegacyNotification", "LegacyBankInfoRequest", "LegacyRemoveAppUUID", "LegacyUpgradeAppUUID",
           "LegacyAppAvailable", "LegacyListInstalledUUIDs", "LegacyDescribeInstalledUUID",
           "LegacyCurrentAppRequest", "LegacyAppInstallRequest", "LegacyBankEntry", "LegacyBankInfoResponse",
           "LegacyAppInstallResult", "LegacyAppUUIDsResult", "LegacyAppDescribeResponse", "LegacyCurrentAppResponse",
           "LegacyAppInstallResponse", "LegacyAppLaunchMessage"]


class LegacyNotification(PebblePacket):
    class Meta:
        endpoint = 3000
        endianness = '<'

    class Source(IntEnum):
        Email = 0
        SMS = 1
        Facebook = 2
        Twitter = 3

    type = Uint8(enum=Source)
    sender = PascalString()
    body = PascalString()
    timestamp = PascalString()
    subject = PascalString()


class LegacyBankInfoRequest(PebblePacket):
    pass


class LegacyRemoveAppUUID(PebblePacket):
    uuid = UUID()


class LegacyUpgradeAppUUID(PebblePacket):
    uuid = UUID()


class LegacyAppAvailable(PebblePacket):
    bank = Uint32()
    vibrate = Boolean()


class LegacyListInstalledUUIDs(PebblePacket):
    pass


class LegacyDescribeInstalledUUID(PebblePacket):
    uuid = UUID()


class LegacyCurrentAppRequest(PebblePacket):
    pass


class LegacyAppInstallRequest(PebblePacket):
    class Meta:
        endpoint = 6000
        register = False

    command = Uint8()
    data = Union(command, {
        0x01: LegacyBankInfoRequest,
        0x02: LegacyRemoveAppUUID,
        0x08: LegacyUpgradeAppUUID,
        0x03: LegacyAppAvailable,
        0x05: LegacyListInstalledUUIDs,
        0x06: LegacyDescribeInstalledUUID,
        0x07: LegacyCurrentAppRequest
    })


class LegacyBankEntry(PebblePacket):
    install_id = Uint32()
    bank_number = Uint32()
    app_name = FixedString(32)
    company_name = FixedString(32)
    flags = Uint32()
    version_minor = Uint8()
    version_major = Uint8()


class LegacyBankInfoResponse(PebblePacket):
    bank_count = Uint32()
    occupied_banks = Uint32()
    apps = FixedList(LegacyBankEntry, count=occupied_banks)


class LegacyAppInstallResult(PebblePacket):
    class Status(IntEnum):
        Success = 1
        InvalidUUID = 6
        # Install
        BankInUse = 2
        InstallInvalidCommand = 3
        InstallGeneralFailure = 4
        IncompatibleSDK = 5
        UUIDConflict = 7
        MissingWorker = 8
        # Remove
        NoAppInBank = 2
        InstallIDMismatch = 3
        RemoveInvalidCommand = 4
        RemoveGeneralFailure = 5
    status = Uint32(enum=Status)


class LegacyAppUUIDsResult(PebblePacket):
    count = Uint8()
    uuids = FixedList(UUID, count=count)


class LegacyAppDescribeResponse(PebblePacket):
    version_minor = Uint8()
    version_major = Uint8()
    app_name = FixedString(32)
    company_name = FixedString(32)


class LegacyCurrentAppResponse(PebblePacket):
    uuid = UUID()


class LegacyAppInstallResponse(PebblePacket):
    class Meta:
        endpoint = 6000

    command = Uint8()
    data = Union(command, {
        0x01: LegacyBankInfoResponse,
        0x02: LegacyAppInstallResult,
        0x05: LegacyAppUUIDsResult,
        0x06: LegacyAppDescribeResponse,
        0x07: LegacyCurrentAppResponse,
    })


class LegacyAppLaunchMessage(AppMessage):
    class Meta:
        endpoint = 0x31
        endianness = '<'

    class Keys(IntEnum):
        RunState = 0x01
        StateFetch = 0x02

    class States(IntEnum):
        NotRunning = 0x00
        Running = 0x01
