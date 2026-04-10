#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Block Volumes."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_volume
short_description: Manage OCI Block Volumes
description:
    - Create, update, and delete block volumes in Oracle Cloud Infrastructure.
    - Uses the BlockstorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the volume.
            - Required when creating a new volume.
        type: str
    availability_domain:
        description:
            - The availability domain of the volume.
            - Required when creating a new volume.
        type: str
    display_name:
        description:
            - A user-friendly name for the volume.
        type: str
    size_in_gbs:
        description:
            - The size of the volume in GBs.
        type: int
    vpus_per_gb:
        description:
            - The number of volume performance units (VPUs) per GB.
            - Values of 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120 are supported.
        type: int
    volume_id:
        description:
            - The OCID of an existing volume.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the volume.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a block volume
  oracle.oci.oci_volume:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-block-volume"
    size_in_gbs: 50
    vpus_per_gb: 10
    state: present

- name: Update a block volume display name
  oracle.oci.oci_volume:
    volume_id: "ocid1.volume.oc1..example"
    display_name: "renamed-volume"
    state: present

- name: Delete a block volume
  oracle.oci.oci_volume:
    volume_id: "ocid1.volume.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the volume.
    returned: on success
    type: dict
    sample:
        id: "ocid1.volume.oc1..example"
        display_name: "my-block-volume"
        lifecycle_state: "AVAILABLE"
        size_in_gbs: 50
        vpus_per_gb: 10
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import BlockstorageClient
    from oci.core.models import CreateVolumeDetails, UpdateVolumeDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVolume(OciResourceBase):
    """Manage OCI Block Volumes."""

    client_class = BlockstorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        volume_id = self.module.params.get("volume_id")
        if not volume_id:
            return None
        try:
            return call_with_retry(self.client.get_volume, volume_id).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateVolumeDetails(
            compartment_id=self.module.params["compartment_id"],
            availability_domain=self.module.params["availability_domain"],
            display_name=self.module.params.get("display_name"),
            size_in_gbs=self.module.params.get("size_in_gbs"),
            vpus_per_gb=self.module.params.get("vpus_per_gb"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(self.client.create_volume, details)
        return wait_for_resource(
            self.module,
            self.client.get_volume,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateVolumeDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            size_in_gbs=self.module.params.get("size_in_gbs"),
            vpus_per_gb=self.module.params.get("vpus_per_gb"),
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(self.client.update_volume, resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_volume,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_volume, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_volume,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "size_in_gbs", "vpus_per_gb"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        size_in_gbs=dict(type="int"),
        vpus_per_gb=dict(type="int"),
        volume_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciVolume(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
