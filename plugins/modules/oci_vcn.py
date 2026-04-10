#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Virtual Cloud Networks."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_vcn
short_description: Manage Virtual Cloud Networks (VCNs) in OCI
description:
    - Create, update, and delete Virtual Cloud Networks in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the VCN.
            - Required for creating a VCN.
        type: str
    cidr_blocks:
        description:
            - The list of IPv4 CIDR blocks for the VCN.
            - Required for creating a VCN.
        type: list
        elements: str
    display_name:
        description:
            - A user-friendly name for the VCN.
        type: str
    dns_label:
        description:
            - A DNS label for the VCN used in conjunction with the VNIC's hostname
              and subnet's DNS label to form a fully qualified domain name.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the VCN.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a VCN
  oracle.oci.oci_vcn:
    compartment_id: "ocid1.compartment.oc1..example"
    cidr_blocks:
      - "10.0.0.0/16"
    display_name: "my-vcn"
    dns_label: "myvcn"
    state: present

- name: Update a VCN display name
  oracle.oci.oci_vcn:
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "updated-vcn-name"
    state: present

- name: Delete a VCN
  oracle.oci.oci_vcn:
    vcn_id: "ocid1.vcn.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The VCN resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.vcn.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-vcn"
        cidr_blocks: ["10.0.0.0/16"]
        lifecycle_state: "AVAILABLE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import CreateVcnDetails, UpdateVcnDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVcn(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        vcn_id = self.module.params.get("vcn_id")
        if not vcn_id:
            return None
        try:
            return self.client.get_vcn(vcn_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateVcnDetails(
            compartment_id=self.module.params["compartment_id"],
            cidr_blocks=self.module.params["cidr_blocks"],
            display_name=self.module.params.get("display_name"),
            dns_label=self.module.params.get("dns_label"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        vcn = self.client.create_vcn(details).data
        return wait_for_resource(
            self.module,
            self.client.get_vcn,
            vcn.id,
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
        if self.module.params.get("cidr_blocks") is not None:
            kwargs["cidr_blocks"] = self.module.params["cidr_blocks"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateVcnDetails(**kwargs)
        self.client.update_vcn(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_vcn,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_vcn(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_vcn,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "cidr_blocks"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cidr_blocks=dict(type="list", elements="str"),
        display_name=dict(type="str"),
        dns_label=dict(type="str"),
        vcn_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "cidr_blocks"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_vcn = OciVcn(module)
    oci_vcn.run()


if __name__ == "__main__":
    main()
