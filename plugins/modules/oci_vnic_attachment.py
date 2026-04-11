# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI VNIC Attachments."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_vnic_attachment
short_description: Manage OCI VNIC Attachments
description:
    - Attach and detach VNICs to compute instances in Oracle Cloud Infrastructure.
    - Uses the ComputeClient from the OCI Python SDK.
    - This is a create/delete only resource; update is not supported.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
    vnic_attachment_id:
        description:
            - The OCID of the VNIC attachment.
            - Required for delete operations.
        type: str
    instance_id:
        description:
            - The OCID of the instance to attach the VNIC to.
            - Required when creating a new VNIC attachment.
        type: str
    create_vnic_details:
        description:
            - Details for creating the VNIC.
        type: dict
        suboptions:
            subnet_id:
                description:
                    - The OCID of the subnet for the VNIC.
                type: str
                required: true
            display_name:
                description:
                    - A user-friendly name for the VNIC.
                type: str
            assign_public_ip:
                description:
                    - Whether the VNIC should be assigned a public IP address.
                type: bool
            nsg_ids:
                description:
                    - A list of NSG OCIDs for the VNIC.
                type: list
                elements: str
            private_ip:
                description:
                    - A private IP address of your choice.
                type: str
    display_name:
        description:
            - A user-friendly name for the VNIC attachment.
        type: str
    state:
        description:
            - The desired state of the VNIC attachment.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Attach a VNIC to an instance
  oracle.oci.oci_vnic_attachment:
    instance_id: "ocid1.instance.oc1..example"
    display_name: "secondary-vnic"
    create_vnic_details:
      subnet_id: "ocid1.subnet.oc1..example"
      display_name: "my-secondary-vnic"
      assign_public_ip: false
    state: present

- name: Detach a VNIC from an instance
  oracle.oci.oci_vnic_attachment:
    vnic_attachment_id: "ocid1.vnicattachment.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the VNIC attachment.
    returned: on success
    type: dict
    sample:
        id: "ocid1.vnicattachment.oc1..example"
        instance_id: "ocid1.instance.oc1..example"
        display_name: "secondary-vnic"
        lifecycle_state: "ATTACHED"
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
    from oci.core import ComputeClient
    from oci.core.models import AttachVnicDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVnicAttachment(OciResourceBase):
    """Manage OCI VNIC Attachments."""

    client_class = ComputeClient if HAS_OCI_SDK else None

    def get_resource(self):
        attachment_id = self.module.params.get("vnic_attachment_id")
        if not attachment_id:
            return None
        try:
            return call_with_retry(
                self.client.get_vnic_attachment, attachment_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        details = AttachVnicDetails(
            instance_id=self.module.params["instance_id"],
            display_name=self.module.params.get("display_name"),
            create_vnic_details=self.module.params.get("create_vnic_details"),
        )
        response = call_with_retry(self.client.attach_vnic, details)
        return wait_for_resource(
            self.module,
            self.client.get_vnic_attachment,
            response.data.id,
            READY_STATES | {"ATTACHED"},
        )

    def update_resource(self, resource):
        # VNIC attachments do not support updates.
        return resource

    def delete_resource(self, resource):
        call_with_retry(self.client.detach_vnic, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_vnic_attachment,
                resource.id,
                DEAD_STATES | {"DETACHED"},
            )

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vnic_attachment_id=dict(type="str"),
        instance_id=dict(type="str"),
        create_vnic_details=dict(type="dict"),
        display_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("instance_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciVnicAttachment(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
