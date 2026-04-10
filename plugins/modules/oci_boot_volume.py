#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI boot volumes."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_boot_volume
short_description: Manage OCI boot volumes
description:
  - Create, update, and delete boot volumes in Oracle Cloud Infrastructure.
  - Boot volumes can be created from boot volume backups or boot volume replicas.
  - Uses C(oci.core.BlockstorageClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the boot volume in.
      - Required when creating a new boot volume.
    type: str
  availability_domain:
    description:
      - The availability domain of the boot volume.
      - Required when creating a new boot volume.
    type: str
  source_details:
    description:
      - Specifies the source of the boot volume.
    type: dict
    suboptions:
      type:
        description:
          - The type of source (bootVolumeBackup, bootVolume, bootVolumeReplica).
        type: str
        required: true
        choices: [bootVolumeBackup, bootVolume, bootVolumeReplica]
      id:
        description:
          - The OCID of the source resource.
        type: str
        required: true
  display_name:
    description:
      - A user-friendly name for the boot volume.
    type: str
  size_in_gbs:
    description:
      - The size of the boot volume in GBs.
    type: int
  vpus_per_gb:
    description:
      - The number of volume performance units (VPUs) to allocate per GB.
      - Values are 0 (Lower Cost), 10 (Balanced), 20 (Higher Performance),
        30-120 (Ultra High Performance).
    type: int
  boot_volume_id:
    description:
      - The OCID of the boot volume. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the boot volume.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a boot volume from a backup
  oracle.oci.oci_boot_volume:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-boot-volume"
    source_details:
      type: "bootVolumeBackup"
      id: "ocid1.bootvolumebackup.oc1.phx.example"
    size_in_gbs: 100
    vpus_per_gb: 10
    state: present

- name: Update boot volume size
  oracle.oci.oci_boot_volume:
    boot_volume_id: "ocid1.bootvolume.oc1.phx.example"
    size_in_gbs: 200
    state: present

- name: Delete a boot volume
  oracle.oci.oci_boot_volume:
    boot_volume_id: "ocid1.bootvolume.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The boot volume details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.bootvolume.oc1.phx.example"
    display_name: "my-boot-volume"
    lifecycle_state: "AVAILABLE"
    size_in_gbs: 100
    vpus_per_gb: 10
    availability_domain: "Uocm:PHX-AD-1"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

SOURCE_TYPE_MAP = {
    "bootVolumeBackup": oci.core.models.BootVolumeSourceFromBootVolumeBackupDetails if HAS_OCI_SDK else None,
    "bootVolume": oci.core.models.BootVolumeSourceFromBootVolumeDetails if HAS_OCI_SDK else None,
    "bootVolumeReplica": oci.core.models.BootVolumeSourceFromBootVolumeReplicaDetails if HAS_OCI_SDK else None,
}


class OciBootVolume(OciResourceBase):
    """Manage OCI boot volumes."""

    def __init__(self, module):
        self.client_class = oci.core.BlockstorageClient
        super().__init__(module)

    def get_resource(self):
        boot_volume_id = self.module.params.get("boot_volume_id")
        if not boot_volume_id:
            return None
        try:
            response = self.client.get_boot_volume(boot_volume_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_TERMINATED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _build_source_details(self):
        """Build the source details model from params."""
        sd = self.module.params.get("source_details")
        if not sd:
            return None
        source_cls = SOURCE_TYPE_MAP.get(sd["type"])
        if source_cls is None:
            self.module.fail_json(msg=f"Unsupported source type: {sd['type']}")
        return source_cls(id=sd["id"])

    def create_resource(self):
        params = self.module.params
        kwargs = dict(
            compartment_id=params["compartment_id"],
            availability_domain=params["availability_domain"],
            source_details=self._build_source_details(),
        )

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]
        if params.get("size_in_gbs") is not None:
            kwargs["size_in_gbs"] = params["size_in_gbs"]
        if params.get("vpus_per_gb") is not None:
            kwargs["vpus_per_gb"] = params["vpus_per_gb"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.core.models.CreateBootVolumeDetails(**kwargs)
        response = call_with_retry(self.client.create_boot_volume, create_details)
        boot_volume = response.data

        if self.module.params.get("wait", True):
            boot_volume = wait_for_resource(
                self.module,
                self.client.get_boot_volume,
                boot_volume.id,
                target_states={LIFECYCLE_AVAILABLE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return boot_volume

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]
        if params.get("size_in_gbs") is not None:
            kwargs["size_in_gbs"] = params["size_in_gbs"]
        if params.get("vpus_per_gb") is not None:
            kwargs["vpus_per_gb"] = params["vpus_per_gb"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.core.models.UpdateBootVolumeDetails(**kwargs)
        response = call_with_retry(
            self.client.update_boot_volume, resource.id, update_details,
        )
        boot_volume = response.data

        if self.module.params.get("wait", True):
            boot_volume = wait_for_resource(
                self.module,
                self.client.get_boot_volume,
                boot_volume.id,
                target_states={LIFECYCLE_AVAILABLE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return boot_volume

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_boot_volume, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_boot_volume,
                resource.id,
                target_states={LIFECYCLE_TERMINATED},
            )

    def _updatable_attributes(self):
        return ["display_name", "size_in_gbs", "vpus_per_gb"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        source_details=dict(
            type="dict",
            options=dict(
                type=dict(type="str", required=True, choices=["bootVolumeBackup", "bootVolume", "bootVolumeReplica"]),
                id=dict(type="str", required=True),
            ),
        ),
        display_name=dict(type="str"),
        size_in_gbs=dict(type="int"),
        vpus_per_gb=dict(type="int"),
        boot_volume_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain", "source_details"), True),
            ("state", "absent", ("boot_volume_id",)),
        ],
    )

    oci_bv = OciBootVolume(module)
    oci_bv.run()


if __name__ == "__main__":
    main()
