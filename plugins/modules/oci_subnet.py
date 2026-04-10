#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Subnets."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_subnet
short_description: Manage subnets in OCI
description:
    - Create, update, and delete subnets in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the subnet.
            - Required for creating a subnet.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN to contain the subnet.
            - Required for creating a subnet.
        type: str
    cidr_block:
        description:
            - The CIDR block of the subnet.
            - Required for creating a subnet.
        type: str
    display_name:
        description:
            - A user-friendly name for the subnet.
        type: str
    dns_label:
        description:
            - A DNS label for the subnet.
        type: str
    availability_domain:
        description:
            - The availability domain for the subnet.
            - If omitted, the subnet is regional.
        type: str
    route_table_id:
        description:
            - The OCID of the route table the subnet will use.
        type: str
    security_list_ids:
        description:
            - The OCIDs of the security lists to associate with the subnet.
        type: list
        elements: str
    prohibit_public_ip_on_vnic:
        description:
            - Whether VNICs in this subnet can have public IP addresses.
        type: bool
        default: false
    subnet_id:
        description:
            - The OCID of the subnet.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the subnet.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a public subnet
  oracle.oci.oci_subnet:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    cidr_block: "10.0.1.0/24"
    display_name: "public-subnet"
    dns_label: "pubsub"
    state: present

- name: Create a private subnet
  oracle.oci.oci_subnet:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    cidr_block: "10.0.2.0/24"
    display_name: "private-subnet"
    prohibit_public_ip_on_vnic: true
    state: present

- name: Delete a subnet
  oracle.oci.oci_subnet:
    subnet_id: "ocid1.subnet.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The subnet resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.subnet.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        cidr_block: "10.0.1.0/24"
        display_name: "public-subnet"
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
    from oci.core.models import CreateSubnetDetails, UpdateSubnetDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciSubnet(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        subnet_id = self.module.params.get("subnet_id")
        if not subnet_id:
            return None
        try:
            return self.client.get_subnet(subnet_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateSubnetDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            cidr_block=self.module.params["cidr_block"],
            display_name=self.module.params.get("display_name"),
            dns_label=self.module.params.get("dns_label"),
            availability_domain=self.module.params.get("availability_domain"),
            route_table_id=self.module.params.get("route_table_id"),
            security_list_ids=self.module.params.get("security_list_ids"),
            prohibit_public_ip_on_vnic=self.module.params.get("prohibit_public_ip_on_vnic", False),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        subnet = self.client.create_subnet(details).data
        return wait_for_resource(
            self.module,
            self.client.get_subnet,
            subnet.id,
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
        if self.module.params.get("route_table_id") is not None:
            kwargs["route_table_id"] = self.module.params["route_table_id"]
        if self.module.params.get("security_list_ids") is not None:
            kwargs["security_list_ids"] = self.module.params["security_list_ids"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateSubnetDetails(**kwargs)
        self.client.update_subnet(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_subnet,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_subnet(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_subnet,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "route_table_id", "security_list_ids"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        cidr_block=dict(type="str"),
        display_name=dict(type="str"),
        dns_label=dict(type="str"),
        availability_domain=dict(type="str"),
        route_table_id=dict(type="str"),
        security_list_ids=dict(type="list", elements="str"),
        prohibit_public_ip_on_vnic=dict(type="bool", default=False),
        subnet_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "vcn_id", "cidr_block"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_subnet = OciSubnet(module)
    oci_subnet.run()


if __name__ == "__main__":
    main()
