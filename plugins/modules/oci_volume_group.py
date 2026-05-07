# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Volume Groups."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_volume_group
short_description: Manage OCI Volume Groups
description:
    - Create, update, and delete block volume groups in Oracle Cloud
      Infrastructure.
    - Uses the BlockstorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the volume group.
            - Required when creating a new volume group.
        type: str
    volume_group_id:
        description:
            - The OCID of the volume group.
            - Required for update and delete operations.
        type: str
    availability_domain:
        description:
            - The availability domain of the volume group.
            - Required when creating a new volume group.
        type: str
    display_name:
        description:
            - A user-friendly name for the volume group.
        type: str
    volume_ids:
        description:
            - OCIDs of the volumes in this volume group.
        type: list
        elements: str
    source_details:
        description:
            - Specifies the source for the volume group.
        type: dict
        suboptions:
            type:
                description:
                    - The type of source (volumeGroupId, volumeGroupBackupId, volumeIds).
                type: str
                required: true
            volume_group_id:
                description:
                    - The OCID of the source volume group (when cloning).
                type: str
            volume_group_backup_id:
                description:
                    - The OCID of the volume group backup (when restoring).
                type: str
            volume_ids:
                description:
                    - OCIDs of the volumes to include in the group.
                type: list
                elements: str
    state:
        description:
            - The desired state of the volume group.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a volume group
  stevefulme1.oci_cloud.oci_volume_group:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-volume-group"
    source_details:
      type: volumeIds
      volume_ids:
        - "ocid1.volume.oc1..example1"
        - "ocid1.volume.oc1..example2"
    state: present

- name: Update a volume group
  stevefulme1.oci_cloud.oci_volume_group:
    volume_group_id: "ocid1.volumegroup.oc1..example"
    display_name: "renamed-volume-group"
    volume_ids:
      - "ocid1.volume.oc1..example1"
      - "ocid1.volume.oc1..example2"
      - "ocid1.volume.oc1..example3"
    state: present

- name: Delete a volume group
  stevefulme1.oci_cloud.oci_volume_group:
    volume_group_id: "ocid1.volumegroup.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the volume group.
    returned: on success
    type: dict
    sample:
        id: "ocid1.volumegroup.oc1..example"
        display_name: "my-volume-group"
        lifecycle_state: "AVAILABLE"
        availability_domain: "Uocm:PHX-AD-1"
        volume_ids:
            - "ocid1.volume.oc1..example1"
            - "ocid1.volume.oc1..example2"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import BlockstorageClient
    from oci.core.models import (
        CreateVolumeGroupDetails,
        UpdateVolumeGroupDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVolumeGroup(OciResourceBase):
    """Manage OCI Volume Groups."""

    client_class = BlockstorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        volume_group_id = self.module.params.get("volume_group_id")
        if not volume_group_id:
            return None
        try:
            return call_with_retry(
                self.client.get_volume_group, volume_group_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateVolumeGroupDetails(
            compartment_id=self.module.params["compartment_id"],
            availability_domain=self.module.params["availability_domain"],
            display_name=self.module.params.get("display_name"),
            source_details=self.module.params.get("source_details"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(self.client.create_volume_group, details)
        return wait_for_resource(
            self.module,
            self.client.get_volume_group,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateVolumeGroupDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            volume_ids=self.module.params.get("volume_ids") or resource.volume_ids,
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_volume_group, resource.id, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_volume_group,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_volume_group, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_volume_group,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "volume_ids"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        volume_group_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        volume_ids=dict(type="list", elements="str"),
        source_details=dict(type="dict"),
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

    resource_helper = OciVolumeGroup(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
