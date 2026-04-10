# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Internet Gateways."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_internet_gateway
short_description: Manage internet gateways in OCI
description:
    - Create, update, and delete internet gateways in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the internet gateway.
            - Required for creating an internet gateway.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the internet gateway.
            - Required for creating an internet gateway.
        type: str
    display_name:
        description:
            - A user-friendly name for the internet gateway.
        type: str
    is_enabled:
        description:
            - Whether the internet gateway is enabled.
        type: bool
        default: true
    ig_id:
        description:
            - The OCID of the internet gateway.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the internet gateway.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an internet gateway
  oracle.oci.oci_internet_gateway:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "my-igw"
    is_enabled: true
    state: present

- name: Disable an internet gateway
  oracle.oci.oci_internet_gateway:
    ig_id: "ocid1.internetgateway.oc1..example"
    is_enabled: false
    state: present

- name: Delete an internet gateway
  oracle.oci.oci_internet_gateway:
    ig_id: "ocid1.internetgateway.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The internet gateway resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.internetgateway.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-igw"
        is_enabled: true
        lifecycle_state: "AVAILABLE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import (
        CreateInternetGatewayDetails,
        UpdateInternetGatewayDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciInternetGateway(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        ig_id = self.module.params.get("ig_id")
        if not ig_id:
            return None
        try:
            return self.client.get_internet_gateway(ig_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateInternetGatewayDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            is_enabled=self.module.params.get("is_enabled", True),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        igw = self.client.create_internet_gateway(details).data
        return wait_for_resource(
            self.module,
            self.client.get_internet_gateway,
            igw.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("is_enabled") is not None:
            kwargs["is_enabled"] = self.module.params["is_enabled"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateInternetGatewayDetails(**kwargs)
        self.client.update_internet_gateway(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_internet_gateway,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_internet_gateway(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_internet_gateway,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "is_enabled"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        is_enabled=dict(type="bool", default=True),
        ig_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "vcn_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_igw = OciInternetGateway(module)
    oci_igw.run()


if __name__ == "__main__":
    main()
