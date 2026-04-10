#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Network Security Groups."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_nsg
short_description: Manage Network Security Groups (NSGs) in OCI
description:
    - Create, update, and delete Network Security Groups in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the NSG.
            - Required for creating an NSG.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN to contain the NSG.
            - Required for creating an NSG.
        type: str
    display_name:
        description:
            - A user-friendly name for the NSG.
        type: str
    nsg_id:
        description:
            - The OCID of the Network Security Group.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the NSG.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a Network Security Group
  oracle.oci.oci_nsg:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "web-nsg"
    state: present

- name: Update an NSG display name
  oracle.oci.oci_nsg:
    nsg_id: "ocid1.networksecuritygroup.oc1..example"
    display_name: "updated-nsg"
    state: present

- name: Delete a Network Security Group
  oracle.oci.oci_nsg:
    nsg_id: "ocid1.networksecuritygroup.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Network Security Group resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.networksecuritygroup.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "web-nsg"
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
        CreateNetworkSecurityGroupDetails,
        UpdateNetworkSecurityGroupDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciNsg(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        nsg_id = self.module.params.get("nsg_id")
        if not nsg_id:
            return None
        try:
            return self.client.get_network_security_group(nsg_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateNetworkSecurityGroupDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        nsg = self.client.create_network_security_group(details).data
        return wait_for_resource(
            self.module,
            self.client.get_network_security_group,
            nsg.id,
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
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateNetworkSecurityGroupDetails(**kwargs)
        self.client.update_network_security_group(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_network_security_group,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_network_security_group(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_network_security_group,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        nsg_id=dict(type="str"),
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

    oci_nsg = OciNsg(module)
    oci_nsg.run()


if __name__ == "__main__":
    main()
