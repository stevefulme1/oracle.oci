# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Network Firewall Policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_network_firewall_policy
short_description: Manage Network Firewall Policies in OCI
description:
    - Create, update, and delete Network Firewall Policies in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK NetworkFirewallClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the firewall policy.
            - Required for creating a firewall policy.
        type: str
    network_firewall_policy_id:
        description:
            - The OCID of the network firewall policy.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the firewall policy.
        type: str
    ip_address_lists:
        description:
            - Map of IP address lists used in policy rules.
            - Each key is the list name, each value is a list of IP addresses or CIDR blocks.
        type: dict
    security_rules:
        description:
            - List of security rules for the firewall policy.
        type: list
        elements: dict
    decryption_rules:
        description:
            - List of decryption rules for the firewall policy.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the firewall policy.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a Network Firewall Policy
  stevefulme1.oci_cloud.oci_network_firewall_policy:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-firewall-policy"
    ip_address_lists:
      allowed_ips:
        - "10.0.0.0/8"
        - "192.168.1.0/24"
    state: present

- name: Update a Network Firewall Policy
  stevefulme1.oci_cloud.oci_network_firewall_policy:
    network_firewall_policy_id: "ocid1.networkfirewallpolicy.oc1..example"
    display_name: "updated-policy"
    state: present

- name: Delete a Network Firewall Policy
  stevefulme1.oci_cloud.oci_network_firewall_policy:
    network_firewall_policy_id: "ocid1.networkfirewallpolicy.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Network Firewall Policy resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.networkfirewallpolicy.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-firewall-policy"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.network_firewall import NetworkFirewallClient
    from oci.network_firewall.models import (
        CreateNetworkFirewallPolicyDetails,
        UpdateNetworkFirewallPolicyDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciNetworkFirewallPolicy(OciResourceBase):
    def __init__(self, module):
        self.client_class = NetworkFirewallClient
        super().__init__(module)

    def get_resource(self):
        policy_id = self.module.params.get("network_firewall_policy_id")
        if not policy_id:
            return None
        try:
            return self.client.get_network_firewall_policy(policy_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateNetworkFirewallPolicyDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            ip_address_lists=self.module.params.get("ip_address_lists"),
            security_rules=self.module.params.get("security_rules"),
            decryption_rules=self.module.params.get("decryption_rules"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_network_firewall_policy(details).data
        return wait_for_resource(
            self.module,
            self.client.get_network_firewall_policy,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("ip_address_lists") is not None:
            kwargs["ip_address_lists"] = self.module.params["ip_address_lists"]
        if self.module.params.get("security_rules") is not None:
            kwargs["security_rules"] = self.module.params["security_rules"]
        if self.module.params.get("decryption_rules") is not None:
            kwargs["decryption_rules"] = self.module.params["decryption_rules"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateNetworkFirewallPolicyDetails(**kwargs)
        self.client.update_network_firewall_policy(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_network_firewall_policy,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_network_firewall_policy(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_network_firewall_policy,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "ip_address_lists", "security_rules", "decryption_rules"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        network_firewall_policy_id=dict(type="str"),
        display_name=dict(type="str"),
        ip_address_lists=dict(type="dict"),
        security_rules=dict(type="list", elements="dict"),
        decryption_rules=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciNetworkFirewallPolicy(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
