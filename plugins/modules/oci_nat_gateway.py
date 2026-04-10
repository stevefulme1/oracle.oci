#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI NAT Gateways."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_nat_gateway
short_description: Manage NAT gateways in OCI
description:
    - Create, update, and delete NAT gateways in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the NAT gateway.
            - Required for creating a NAT gateway.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the NAT gateway.
            - Required for creating a NAT gateway.
        type: str
    display_name:
        description:
            - A user-friendly name for the NAT gateway.
        type: str
    block_traffic:
        description:
            - Whether the NAT gateway blocks traffic through it.
        type: bool
        default: false
    nat_gateway_id:
        description:
            - The OCID of the NAT gateway.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the NAT gateway.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a NAT gateway
  oracle.oci.oci_nat_gateway:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "my-nat-gw"
    state: present

- name: Block traffic on a NAT gateway
  oracle.oci.oci_nat_gateway:
    nat_gateway_id: "ocid1.natgateway.oc1..example"
    block_traffic: true
    state: present

- name: Delete a NAT gateway
  oracle.oci.oci_nat_gateway:
    nat_gateway_id: "ocid1.natgateway.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The NAT gateway resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.natgateway.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-nat-gw"
        block_traffic: false
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
        CreateNatGatewayDetails,
        UpdateNatGatewayDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciNatGateway(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        nat_gw_id = self.module.params.get("nat_gateway_id")
        if not nat_gw_id:
            return None
        try:
            return self.client.get_nat_gateway(nat_gw_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateNatGatewayDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            block_traffic=self.module.params.get("block_traffic", False),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        nat_gw = self.client.create_nat_gateway(details).data
        return wait_for_resource(
            self.module,
            self.client.get_nat_gateway,
            nat_gw.id,
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
        if self.module.params.get("block_traffic") is not None:
            kwargs["block_traffic"] = self.module.params["block_traffic"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateNatGatewayDetails(**kwargs)
        self.client.update_nat_gateway(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_nat_gateway,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_nat_gateway(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_nat_gateway,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "block_traffic"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        block_traffic=dict(type="bool", default=False),
        nat_gateway_id=dict(type="str"),
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

    oci_nat = OciNatGateway(module)
    oci_nat.run()


if __name__ == "__main__":
    main()
