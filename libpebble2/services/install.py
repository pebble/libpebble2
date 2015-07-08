from __future__ import absolute_import
__author__ = 'katharine'

from .blobdb import BlobDBClient, BlobDatabaseID, SyncWrapper, BlobStatus
from .putbytes import PutBytes, PutBytesType
from libpebble2.events.mixin import EventSourceMixin
from libpebble2.exceptions import AppInstallError
from libpebble2.protocol.apps import AppMetadata, AppRunState, AppRunStateStart, AppFetchRequest, AppFetchResponse, AppFetchStatus
from libpebble2.protocol.legacy2 import *
from libpebble2.services.appmessage import AppMessageService, Uint8 as AMUint8
from libpebble2.util.bundle import PebbleBundle

__all__ = ["AppInstaller"]


class AppInstaller(EventSourceMixin):
    """
    Installs an app on the Pebble via Pebble Protocol.

    .. note:
       If you use a :class:`BlobDBClient` in use elsewhere, pass it in here. If none is passed it will create one,
       and they will conflict.

    :param pebble: The :class:`PebbleConnection` over which to install the app.
    :type pebble: .PebbleConnection
    :param pbw_path: The path to the PBW file to be installed on the filesystem.
    :type pbw_path: str
    :param blobdb_client: An optional :class:`BlobDBClient` to use, if one already exists. If omitted, one will be
                          created.
    :type blobdb_client: .BlobDBClient
    """
    def __init__(self, pebble, pbw_path, blobdb_client=None):
        self._pebble = pebble
        self._blobdb = blobdb_client or BlobDBClient(pebble)
        EventSourceMixin.__init__(self)
        #: Total number of bytes sent so far.
        self.total_sent = 0
        #: Total number of bytes to send.
        self.total_size = None
        self._prepare(pbw_path)

    def _prepare(self, pbw_path):
        self._bundle = PebbleBundle(pbw_path, hardware=self._pebble.watch_info.running.hardware_platform)
        if not self._bundle.is_app_bundle:
            raise AppInstallError("This is not an app bundle.")

        self.total_size = self._bundle.zip.getinfo(self._bundle.get_app_path()).file_size
        if self._bundle.has_resources:
            self.total_size += self._bundle.zip.getinfo(self._bundle.get_resource_path()).file_size

        if self._bundle.has_worker:
            self.total_size += self._bundle.zip.getinfo(self._bundle.get_worker_path()).file_size

    def install(self):
        """
        Installs an app. Blocks until the installation is complete, or raises :exc:`AppInstallError` if it fails.

        While this method runs, "progress" events will be emitted regularly with the following signature: ::

           (sent_this_interval, sent_total, total_size)
        """
        if self._pebble.firmware_version.major < 3:
            self._install_legacy2()
        else:
            self._install_modern()

    def _install_modern(self):
        metadata = self._bundle.get_app_metadata()
        app_uuid = metadata['uuid']
        blob_packet = AppMetadata(uuid=app_uuid, flags=metadata['flags'], icon=metadata['icon_resource_id'],
                                  app_version_major=metadata['app_version_major'],
                                  app_version_minor=metadata['app_version_minor'],
                                  sdk_version_major=metadata['sdk_version_major'],
                                  sdk_version_minor=metadata['sdk_version_minor'],
                                  app_face_bg_color=0, app_face_template_id=0, app_name=metadata['app_name'])

        result = SyncWrapper(self._blobdb.insert, BlobDatabaseID.App, app_uuid, blob_packet.serialise()).wait()
        if result != BlobStatus.Success:
            raise AppInstallError("BlobDB error: {!s}".format(result))

        # Start the app.
        self._pebble.send_packet(AppRunState(data=AppRunStateStart(uuid=app_uuid)))

        # Wait for a launch request.
        app_fetch = self._pebble.read_from_endpoint(AppFetchRequest)
        if app_fetch.uuid != app_uuid:
            self._pebble.send_packet(AppFetchResponse(response=AppFetchStatus.InvalidUUID))
            raise AppInstallError("App requested the wrong UUID! Asked for {}; expected {}".format(
                app_fetch.uuid, app_uuid))
        self._broadcast_event('progress', 0, self.total_sent, self.total_size)

        # Send the app over
        binary = self._bundle.zip.read(self._bundle.get_app_path())
        self._send_part(PutBytesType.Binary, binary, app_fetch.app_id)

        if self._bundle.has_resources:
            resources = self._bundle.zip.read(self._bundle.get_resource_path())
            self._send_part(PutBytesType.Resources, resources, app_fetch.app_id)

        if self._bundle.has_worker:
            worker = self._bundle.zip.read(self._bundle.get_worker_path())
            self._send_part(PutBytesType.Worker, worker, app_fetch.app_id)

    def _send_part(self, type, object, install_id):
        pb = PutBytes(self._pebble, type, object, app_install_id=install_id)
        pb.register_handler("progress", self._handle_progress)
        pb.send()

    def _install_legacy2(self):
        metadata = self._bundle.get_app_metadata()
        app_uuid = metadata['uuid']

        self._pebble.send_packet(LegacyAppInstallRequest(data=LegacyUpgradeAppUUID(uuid=app_uuid)))
        # We don't really care if this worked; we're just waiting for it.
        self._pebble.read_from_endpoint(LegacyAppInstallResponse)

        # Find somewhere to install to.
        self._pebble.send_packet(LegacyAppInstallRequest(data=LegacyBankInfoRequest()))
        result = self._pebble.read_from_endpoint(LegacyAppInstallResponse).data
        assert isinstance(result, LegacyBankInfoResponse)
        first_free = 0
        for app in result.apps:
            assert isinstance(app, LegacyBankEntry)
            if app.bank_number == first_free:
                first_free += 1
        if first_free == result.bank_count:
            raise AppInstallError("No app banks free.")

        # Send the app over
        binary = self._bundle.zip.read(self._bundle.get_app_path())
        self._send_part_legacy2(PutBytesType.Binary, binary, first_free)

        if self._bundle.has_resources:
            resources = self._bundle.zip.read(self._bundle.get_resource_path())
            self._send_part_legacy2(PutBytesType.Resources, resources, first_free)

        if self._bundle.has_worker:
            worker = self._bundle.zip.read(self._bundle.get_worker_path())
            self._send_part_legacy2(PutBytesType.Worker, worker, first_free)

        # Mark it as available
        self._pebble.send_packet(LegacyAppInstallRequest(data=LegacyAppAvailable(bank=first_free, vibrate=True)))
        self._pebble.read_from_endpoint(LegacyAppInstallResponse)

        # Launch it (which is painful on 2.x).
        appmessage = AppMessageService(self._pebble, message_type=LegacyAppLaunchMessage)
        appmessage.send_message(app_uuid, {
            LegacyAppLaunchMessage.Keys.RunState: AMUint8(LegacyAppLaunchMessage.States.Running)
        })
        appmessage.shutdown()

    def _send_part_legacy2(self, type, object, bank):
        pb = PutBytes(self._pebble, type, object, bank=bank)
        pb.register_handler("progress", self._handle_progress)
        pb.send()

    def _handle_progress(self, sent, total_sent, total_length):
        self.total_sent += sent
        self._broadcast_event('progress', sent, self.total_sent, self.total_size)
