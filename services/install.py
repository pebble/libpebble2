from __future__ import absolute_import
__author__ = 'katharine'

import uuid

from .blobdb import BlobDBClient, BlobDatabaseID, SyncWrapper, BlobStatus
from .putbytes import PutBytes, PutBytesType
from errors import PebbleError
from protocol.apps import AppMetadata, AppRunState, AppRunStateStart, AppFetchRequest, AppFetchResponse, AppFetchStatus
from util.bundle import PebbleBundle

__all__ = ["AppInstaller", "AppInstallError"]


class AppInstallError(PebbleError):
    pass


class AppInstaller(object):
    def __init__(self, pebble, event_handler=None, blobdb_client=None):
        self._pebble = pebble
        self._event_handler = event_handler
        self._blobdb = blobdb_client or BlobDBClient(pebble, event_handler)

    def install(self, pbw_path):
        bundle = PebbleBundle(pbw_path)
        if not bundle.is_app_bundle:
            raise AppInstallError("This is not an app bundle.")
        metadata = bundle.get_app_metadata()
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

        binary = bundle.zip.read(bundle.get_app_path())
        PutBytes(self._pebble, self._event_handler, PutBytesType.Binary, binary, app_install_id=app_fetch.app_id).send()

        if bundle.has_resources:
            resources = bundle.zip.read(bundle.get_resource_path())
            PutBytes(self._pebble, self._event_handler, PutBytesType.Resources, resources,
                     app_install_id=app_fetch.app_id).send()

        if bundle.has_worker:
            worker = bundle.zip.read(bundle.get_worker_path())
            PutBytes(self._pebble, self._event_handler, PutBytesType.Worker, worker,
                     app_install_id=app_fetch.app_id).send()
