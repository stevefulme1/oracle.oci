#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Route Tables."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_route_table
short_description: Manage route tables in OCI
description:
    - Create, update, and delete route tables in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the route table.
            - Required for creating a route table.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN to contain the route table.
            - Required for creating a route table.
        type: str
    display_name:
        description:
            - A user-friendly name for the route table.
        type: str
    route_rules:
        description:
            - List of route rules for the route table.
        type: list
        elements: dict
        suboptions:
            destination:
                description:
                    - The destination CIDR block or service CIDR.
                type: str
                required: true
            destination_type:
                description:
                    - Type of destination. CIDR_BLOCK or SERVICE_CIDR_BLOCK.
                type: str
                default: CIDR_BLOCK
                choices: [CIDR_BLOCK, SERVICE_CIDR_BLOCK]
            network_entity_id:
                description:
                    - The OCID of the target resource (gateway, DRG, etc.).
                type: str
                required: true
    route_table_id:
        description:
            - The OCID of the route table.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the route table.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a route table with internet gateway route
  oracle.oci.oci_route_table:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "public-rt"
    route_rules:
      - destination: "0.0.0.0/0"
        destination_type: CIDR_BLOCK
        network_entity_id: "ocid1.internetgateway.oc1..example"
    state: present

- name: Delete a route table
  oracle.oci.oci_route_table:
    route_table_id: "ocid1.routetable.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The route table resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.routetable.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "public-rt"
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
        CreateRouteTableDetails,
        UpdateRouteTableDetails,
        RouteRule,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def build_route_rules(rules_param):
    """Convert list of dicts to list of RouteRule objects."""
    if not rules_param:
        return []
    rules = []
    for r in rules_param:
        rules.append(RouteRule(
            destination=r["destination"],
            destination_type=r.get("destination_type", "CIDR_BLOCK"),
            network_entity_id=r["network_entity_id"],
        ))
    return rules


class OciRouteTable(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        rt_id = self.module.params.get("route_table_id")
        if not rt_id:
            return None
        try:
            return self.client.get_route_table(rt_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateRouteTableDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            route_rules=build_route_rules(self.module.params.get("route_rules")),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        rt = self.client.create_route_table(details).data
        return wait_for_resource(
            self.module,
            self.client.get_route_table,
            rt.id,
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
        if self.module.params.get("route_rules") is not None:
            kwargs["route_rules"] = build_route_rules(self.module.params["route_rules"])
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateRouteTableDetails(**kwargs)
        self.client.update_route_table(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_route_table,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_route_table(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_route_table,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "route_rules"]


def main():
    route_rule_spec = dict(
        destination=dict(type="str", required=True),
        destination_type=dict(
            type="str", default="CIDR_BLOCK",
            choices=["CIDR_BLOCK", "SERVICE_CIDR_BLOCK"],
        ),
        network_entity_id=dict(type="str", required=True),
    )

    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        route_rules=dict(type="list", elements="dict", options=route_rule_spec),
        route_table_id=dict(type="str"),
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

    oci_rt = OciRouteTable(module)
    oci_rt.run()


if __name__ == "__main__":
    main()
