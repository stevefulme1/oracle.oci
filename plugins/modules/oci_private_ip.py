# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Private IPs."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_private_ip
short_description: Manage secondary private IPs in OCI
description:
    - Create, update, and delete secondary private IP addresses in Oracle Cloud Infrastructure.
    - Secondary private IPs can be assigned to VNICs for high-availability or multi-IP scenarios.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    private_ip_id:
        description:
            - The OCID of the private IP.
            - Required for update and delete operations.
        type: str
    vnic_id:
        description:
            - The OCID of the VNIC to assign the private IP to.
            - Required for creating a secondary private IP.
        type: str
    display_name:
        description:
            - A user-friendly name for the private IP.
        type: str
    ip_address:
        description:
            - A specific private IP address to assign.
            - If omitted, an available IP in the subnet is automatically chosen.
        type: str
    hostname_label:
        description:
            - The hostname for DNS within the VCN.
        type: str
    state:
        description:
            - The desired state of the private IP.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a secondary private IP
  stevefulme1.oci_cloud.oci_private_ip:
    vnic_id: "ocid1.vnic.oc1..example"
    display_name: "my-secondary-ip"
    state: present

- name: Create a secondary private IP with a specific address
  stevefulme1.oci_cloud.oci_private_ip:
    vnic_id: "ocid1.vnic.oc1..example"
    ip_address: "10.0.1.100"
    display_name: "specific-ip"
    hostname_label: "myhost"
    state: present

- name: Update a private IP
  stevefulme1.oci_cloud.oci_private_ip:
    private_ip_id: "ocid1.privateip.oc1..example"
    display_name: "updated-ip"
    state: present

- name: Delete a secondary private IP
  stevefulme1.oci_cloud.oci_private_ip:
    private_ip_id: "ocid1.privateip.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The private IP resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.privateip.oc1..example"
        vnic_id: "ocid1.vnic.oc1..example"
        ip_address: "10.0.1.100"
        display_name: "my-secondary-ip"
        hostname_label: "myhost"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import CreatePrivateIpDetails, UpdatePrivateIpDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciPrivateIp(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        private_ip_id = self.module.params.get("private_ip_id")
        if not private_ip_id:
            return None
        try:
            return self.client.get_private_ip(private_ip_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreatePrivateIpDetails(
            vnic_id=self.module.params["vnic_id"],
            display_name=self.module.params.get("display_name"),
            ip_address=self.module.params.get("ip_address"),
            hostname_label=self.module.params.get("hostname_label"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        private_ip = self.client.create_private_ip(details).data
        return private_ip

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("hostname_label") is not None:
            kwargs["hostname_label"] = self.module.params["hostname_label"]
        if self.module.params.get("vnic_id") is not None:
            kwargs["vnic_id"] = self.module.params["vnic_id"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdatePrivateIpDetails(**kwargs)
        self.client.update_private_ip(resource.id, details)
        return self.client.get_private_ip(resource.id).data

    def delete_resource(self, resource):
        self.client.delete_private_ip(resource.id)

    def _updatable_attributes(self):
        return ["display_name", "hostname_label", "vnic_id"]


def main():
    module_args = dict(
        private_ip_id=dict(type="str"),
        vnic_id=dict(type="str"),
        display_name=dict(type="str"),
        ip_address=dict(type="str"),
        hostname_label=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("vnic_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_priv_ip = OciPrivateIp(module)
    oci_priv_ip.run()


if __name__ == "__main__":
    main()
