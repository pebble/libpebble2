from __future__ import absolute_import
__author__ = 'katharine'

import json
import os
import struct
import uuid
import zipfile

from .hardware import PebbleHardware

__all__ = ["PebbleBundle"]


class PebbleBundle(object):
    MANIFEST_FILENAME = 'manifest.json'
    UNIVERSAL_FILES = {'appinfo.json', 'pebble-js-app.js'}

    STRUCT_DEFINITION = [
            '8s',   # header
            '2B',   # struct version
            '2B',   # sdk version
            '2B',   # app version
            'H',    # size
            'I',    # offset
            'I',    # crc
            '32s',  # app name
            '32s',  # company name
            'I',    # icon resource id
            'I',    # symbol table address
            'I',    # flags
            'I',    # num relocation list entries
            '16s'   # uuid
    ]

    PLATFORM_PATHS = {
        'unknown': ('',),
        'aplite': ('',),
        'basalt': ('basalt/', ''),
        'chalk': ('chalk/',),
    }

    def __init__(self, bundle_path, hardware=PebbleHardware.UNKNOWN):
        self.hardware = hardware
        bundle_abs_path = os.path.abspath(bundle_path)
        if not os.path.exists(bundle_abs_path):
            raise Exception("Bundle does not exist: " + bundle_path)

        self.zip = zipfile.ZipFile(bundle_abs_path)
        self.path = bundle_abs_path
        self.manifest = None
        self.header = None
        self._zip_contents = set(self.zip.namelist())

        self.app_metadata_struct = struct.Struct(''.join(self.STRUCT_DEFINITION))
        self.app_metadata_length_bytes = self.app_metadata_struct.size

        self.print_pbl_logs = False

    @classmethod
    def prefixes_for_hardware(cls, hardware):
        platform = PebbleHardware.hardware_platform(hardware)
        return cls.PLATFORM_PATHS[platform]

    def get_real_path(self, path):
        if path in self.UNIVERSAL_FILES:
            return path
        else:
            prefixes = self.prefixes_for_hardware(self.hardware)
            for prefix in prefixes:
                real_path = prefix + path
                if real_path in self._zip_contents:
                    return real_path
            return None

    def get_manifest(self):
        if self.manifest:
            return self.manifest

        if self.get_real_path(self.MANIFEST_FILENAME) not in self.zip.namelist():
            raise Exception("Could not find {}; are you sure this is a PebbleBundle?".format(self.MANIFEST_FILENAME))

        self.manifest = json.loads(self.zip.read(self.get_real_path(self.MANIFEST_FILENAME)).decode('utf-8'))
        return self.manifest

    def get_app_metadata(self):
        if self.header:
            return self.header

        app_manifest = self.get_manifest()['application']

        app_bin = self.zip.open(self.get_real_path(app_manifest['name'])).read()

        header = app_bin[0:self.app_metadata_length_bytes]
        values = self.app_metadata_struct.unpack(header)
        self.header = {
            'sentinel': values[0],
            'struct_version_major': values[1],
            'struct_version_minor': values[2],
            'sdk_version_major': values[3],
            'sdk_version_minor': values[4],
            'app_version_major': values[5],
            'app_version_minor': values[6],
            'app_size': values[7],
            'offset': values[8],
            'crc': values[9],
            'app_name': values[10].rstrip(b'\0').decode('utf-8'),
            'company_name': values[11].rstrip(b'\0').decode('utf-8'),
            'icon_resource_id': values[12],
            'symbol_table_addr': values[13],
            'flags': values[14],
            'num_relocation_entries': values[15],
            'uuid': uuid.UUID(bytes=values[16])
        }
        return self.header

    def close(self):
        self.zip.close()

    @property
    def is_firmware_bundle(self):
        return 'firmware' in self.get_manifest()

    @property
    def is_app_bundle(self):
        return 'application' in self.get_manifest()

    @property
    def has_resources(self):
        return 'resources' in self.get_manifest()

    @property
    def has_worker(self):
        return 'worker' in self.get_manifest()

    @property
    def has_javascript(self):
        return 'js' in self.get_manifest()

    def get_firmware_info(self):
        if not self.is_firmware_bundle:
            return None

        return self.get_manifest()['firmware']

    def get_application_info(self):
        if not self.is_app_bundle:
            return None

        return self.get_manifest()['application']

    def get_resources_info(self):
        if not self.has_resources:
            return None

        return self.get_manifest()['resources']

    def get_worker_info(self):
        if not self.is_app_bundle or not self.has_worker:
            return None

        return self.get_manifest()['worker']

    def get_app_path(self):
        return self.get_real_path(self.get_application_info()['name'])

    def get_resource_path(self):
        return self.get_real_path(self.get_resources_info()['name'])

    def get_worker_path(self):
        return self.get_real_path(self.get_worker_info()['name'])
