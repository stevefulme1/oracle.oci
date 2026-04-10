#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Volume Backups."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_volume_backup
short_description: Manage OCI Volume Backups
description:
    - Create, update, and delete volume backups in Oracle Cloud Infrastructure.
    - Uses the BlockstorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    volume_id:
        description:
            - The OCID of the volume to back up.
            - Required when creating a new backup.
        type: str
    display_name:
        description:
            - A user-friendly name for the volume backup.
        type: str
    type:
        description:
            - The type of backup to create.
        type: str
        default: FULL
        choices: [FULL, INCREMENTAL]
    volume_backup_id:
        description:
            - The OCID of an existing volume backup.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the volume backup.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a full volume backup
  oracle.oci.oci_volume_backup:
    volume_id: "ocid1.volume.oc1..example"
    display_name: "my-volume-backup"
    type: FULL
    state: present

- name: Create an incremental backup
  oracle.oci.oci_volume_backup:
    volume_id: "ocid1.volume.oc1..example"
    display_name: "my-incremental-backup"
    type: INCREMENTAL
    state: present

- name: Delete a volume backup
  oracle.oci.oci_volume_backup:
    volume_backup_id: "ocid1.volumebackup.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the volume backup.
    returned: on success
    type: dict
    sample:
        id: "ocid1.volumebackup.oc1..example"
        display_name: "my-volume-backup"
        lifecycle_state: "AVAILABLE"
        type: "FULL"
        size_in_gbs: 50
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import BlockstorageClient
    from oci.core.models import CreateVolumeBackupDetails, UpdateVolumeBackupDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVolumeBackup(OciResourceBase):
    """Manage OCI Volume Backups."""

    client_class = BlockstorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        backup_id = self.module.params.get("volume_backup_id")
        if not backup_id:
            return None
        try:
            return call_with_retry(self.client.get_volume_backup, backup_id).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateVolumeBackupDetails(
            volume_id=self.module.params["volume_id"],
            display_name=self.module.params.get("display_name"),
            type=self.module.params.get("type", "FULL"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(self.client.create_volume_backup, details)
        return wait_for_resource(
            self.module,
            self.client.get_volume_backup,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateVolumeBackupDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_volume_backup,
            resource.id,
            details,
        )
        return wait_for_resource(
            self.module,
            self.client.get_volume_backup,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_volume_backup, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_volume_backup,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        volume_id=dict(type="str"),
        display_name=dict(type="str"),
        type=dict(type="str", default="FULL", choices=["FULL", "INCREMENTAL"]),
        volume_backup_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("volume_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciVolumeBackup(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
