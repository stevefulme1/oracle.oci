# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Network Firewalls."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_network_firewall
short_description: Manage Network Firewalls in OCI
description:
    - Create, update, and delete Network Firewalls in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK NetworkFirewallClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the network firewall.
            - Required for creating a network firewall.
        type: str
    network_firewall_id:
        description:
            - The OCID of the network firewall.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the network firewall.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet in which the network firewall is created.
            - Required for creating a network firewall.
        type: str
    network_firewall_policy_id:
        description:
            - The OCID of the network firewall policy associated with this firewall.
            - Required for creating a network firewall.
        type: str
    availability_domain:
        description:
            - The availability domain in which to create the network firewall.
            - Required for creating a network firewall.
        type: str
    state:
        description:
            - The desired state of the network firewall.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a Network Firewall
  oracle.oci.oci_network_firewall:
    compartment_id: "ocid1.compartment.oc1..example"
    subnet_id: "ocid1.subnet.oc1..example"
    network_firewall_policy_id: "ocid1.networkfirewallpolicy.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-firewall"
    state: present

- name: Update a Network Firewall
  oracle.oci.oci_network_firewall:
    network_firewall_id: "ocid1.networkfirewall.oc1..example"
    display_name: "updated-firewall"
    state: present

- name: Delete a Network Firewall
  oracle.oci.oci_network_firewall:
    network_firewall_id: "ocid1.networkfirewall.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Network Firewall resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.networkfirewall.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-firewall"
        subnet_id: "ocid1.subnet.oc1..example"
        network_firewall_policy_id: "ocid1.networkfirewallpolicy.oc1..example"
        availability_domain: "Uocm:PHX-AD-1"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.network_firewall import NetworkFirewallClient
    from oci.network_firewall.models import (
        CreateNetworkFirewallDetails,
        UpdateNetworkFirewallDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciNetworkFirewall(OciResourceBase):
    def __init__(self, module):
        self.client_class = NetworkFirewallClient
        super().__init__(module)

    def get_resource(self):
        network_firewall_id = self.module.params.get("network_firewall_id")
        if not network_firewall_id:
            return None
        try:
            return self.client.get_network_firewall(network_firewall_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateNetworkFirewallDetails(
            compartment_id=self.module.params["compartment_id"],
            subnet_id=self.module.params["subnet_id"],
            network_firewall_policy_id=self.module.params["network_firewall_policy_id"],
            availability_domain=self.module.params["availability_domain"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_network_firewall(details).data
        return wait_for_resource(
            self.module,
            self.client.get_network_firewall,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("network_firewall_policy_id") is not None:
            kwargs["network_firewall_policy_id"] = self.module.params["network_firewall_policy_id"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateNetworkFirewallDetails(**kwargs)
        self.client.update_network_firewall(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_network_firewall,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_network_firewall(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_network_firewall,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "network_firewall_policy_id"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        network_firewall_id=dict(type="str"),
        display_name=dict(type="str"),
        subnet_id=dict(type="str"),
        network_firewall_policy_id=dict(type="str"),
        availability_domain=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present",
             ("compartment_id", "subnet_id",
              "network_firewall_policy_id", "availability_domain"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciNetworkFirewall(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
