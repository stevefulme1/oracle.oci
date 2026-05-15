# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Volume Attachments."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_volume_attachment
short_description: Manage OCI Volume Attachments
description:
    - Attach and detach block volumes to compute instances in Oracle Cloud
      Infrastructure.
    - Supports iSCSI and paravirtualized attachment types.
    - Uses the ComputeClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
    volume_attachment_id:
        description:
            - The OCID of the volume attachment.
            - Required for delete operations.
        type: str
    instance_id:
        description:
            - The OCID of the instance to attach the volume to.
            - Required when creating a new volume attachment.
        type: str
    volume_id:
        description:
            - The OCID of the volume to attach.
            - Required when creating a new volume attachment.
        type: str
    type:
        description:
            - The type of volume attachment.
        type: str
        default: paravirtualized
        choices: [iscsi, paravirtualized]
    display_name:
        description:
            - A user-friendly name for the volume attachment.
        type: str
    is_read_only:
        description:
            - Whether the attachment is read-only.
        type: bool
        default: false
    state:
        description:
            - The desired state of the volume attachment.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Attach a volume using paravirtualized
  stevefulme1.oci_cloud.oci_volume_attachment:
    instance_id: "ocid1.instance.oc1..example"
    volume_id: "ocid1.volume.oc1..example"
    type: paravirtualized
    display_name: "data-volume"
    state: present

- name: Attach a volume using iSCSI
  stevefulme1.oci_cloud.oci_volume_attachment:
    instance_id: "ocid1.instance.oc1..example"
    volume_id: "ocid1.volume.oc1..example"
    type: iscsi
    display_name: "iscsi-data-volume"
    is_read_only: true
    state: present

- name: Detach a volume
  stevefulme1.oci_cloud.oci_volume_attachment:
    volume_attachment_id: "ocid1.volumeattachment.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the volume attachment.
    returned: on success
    type: dict
    sample:
        id: "ocid1.volumeattachment.oc1..example"
        instance_id: "ocid1.instance.oc1..example"
        volume_id: "ocid1.volume.oc1..example"
        display_name: "data-volume"
        lifecycle_state: "ATTACHED"
        attachment_type: "paravirtualized"
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
    from oci.core import ComputeClient
    from oci.core.models import (
        AttachIScsiVolumeDetails,
        AttachParavirtualizedVolumeDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVolumeAttachment(OciResourceBase):
    """Manage OCI Volume Attachments."""

    client_class = ComputeClient if HAS_OCI_SDK else None

    def get_resource(self):
        attachment_id = self.module.params.get("volume_attachment_id")
        if not attachment_id:
            return None
        try:
            return call_with_retry(
                self.client.get_volume_attachment, attachment_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        attach_type = self.module.params.get("type", "paravirtualized")
        common_kwargs = dict(
            instance_id=self.module.params["instance_id"],
            volume_id=self.module.params["volume_id"],
            display_name=self.module.params.get("display_name"),
            is_read_only=self.module.params.get("is_read_only", False),
        )

        if attach_type == "iscsi":
            details = AttachIScsiVolumeDetails(**common_kwargs)
        else:
            details = AttachParavirtualizedVolumeDetails(**common_kwargs)

        response = call_with_retry(self.client.attach_volume, details)
        return wait_for_resource(
            self.module,
            self.client.get_volume_attachment,
            response.data.id,
            READY_STATES | {"ATTACHED"},
        )

    def update_resource(self, resource):
        # Volume attachments do not support updates.
        return resource

    def delete_resource(self, resource):
        call_with_retry(self.client.detach_volume, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_volume_attachment,
                resource.id,
                DEAD_STATES | {"DETACHED"},
            )

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        volume_attachment_id=dict(type="str"),
        instance_id=dict(type="str"),
        volume_id=dict(type="str"),
        type=dict(type="str", default="paravirtualized", choices=["iscsi", "paravirtualized"]),
        display_name=dict(type="str"),
        is_read_only=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("instance_id", "volume_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciVolumeAttachment(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
