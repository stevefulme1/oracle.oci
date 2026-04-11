# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Network Security Group security rules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_nsg_rule
short_description: Manage security rules in an OCI Network Security Group
description:
    - Add, update, and remove security rules in a Network Security Group.
    - This is a standalone module that does not use OciResourceBase since rules
      are sub-resources of an NSG.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    nsg_id:
        description:
            - The OCID of the Network Security Group to manage rules for.
        type: str
        required: true
    security_rules:
        description:
            - List of security rule definitions.
            - Each rule is a dict with keys such as direction, protocol, source,
              source_type, destination, destination_type, tcp_options,
              udp_options, icmp_options, description, and is_stateless.
            - Required when state is present.
        type: list
        elements: dict
    purge_rules:
        description:
            - When true, remove all existing rules not in the provided security_rules list.
            - When false (default), only add or update rules as specified.
        type: bool
        default: false
    state:
        description:
            - The desired state of the security rules.
            - Use C(present) to add or update rules and C(absent) to remove all rules.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Add security rules to an NSG
  oracle.oci.oci_nsg_rule:
    nsg_id: "ocid1.networksecuritygroup.oc1..example"
    security_rules:
      - direction: INGRESS
        protocol: "6"
        source: "10.0.0.0/16"
        source_type: CIDR_BLOCK
        tcp_options:
          destination_port_range:
            min: 443
            max: 443
        description: "Allow HTTPS from VCN"
      - direction: EGRESS
        protocol: "all"
        destination: "0.0.0.0/0"
        destination_type: CIDR_BLOCK
        description: "Allow all outbound"
    state: present

- name: Replace all rules (purge unmatched)
  oracle.oci.oci_nsg_rule:
    nsg_id: "ocid1.networksecuritygroup.oc1..example"
    security_rules:
      - direction: INGRESS
        protocol: "6"
        source: "10.0.0.0/16"
        source_type: CIDR_BLOCK
        tcp_options:
          destination_port_range:
            min: 80
            max: 80
    purge_rules: true
    state: present

- name: Remove all security rules from an NSG
  oracle.oci.oci_nsg_rule:
    nsg_id: "ocid1.networksecuritygroup.oc1..example"
    state: absent
"""

RETURN = r"""
security_rules:
    description: The list of security rules in the NSG after the operation.
    returned: on success
    type: list
    elements: dict
    sample:
      - id: "ocid1.nsg-security-rule.oc1..example"
        direction: INGRESS
        protocol: "6"
        source: "10.0.0.0/16"
        source_type: CIDR_BLOCK
        description: "Allow HTTPS from VCN"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import (
        AddNetworkSecurityGroupSecurityRulesDetails,
        RemoveNetworkSecurityGroupSecurityRulesDetails,
        AddSecurityRuleDetails,
        UpdateSecurityRuleDetails,
        PortRange,
        TcpOptions,
        UdpOptions,
        IcmpOptions,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def _build_port_range(data):
    """Build a PortRange from a dict."""
    if data is None:
        return None
    return PortRange(min=data["min"], max=data["max"])


def _build_tcp_options(data):
    """Build TcpOptions from a dict."""
    if data is None:
        return None
    return TcpOptions(
        destination_port_range=_build_port_range(data.get("destination_port_range")),
        source_port_range=_build_port_range(data.get("source_port_range")),
    )


def _build_udp_options(data):
    """Build UdpOptions from a dict."""
    if data is None:
        return None
    return UdpOptions(
        destination_port_range=_build_port_range(data.get("destination_port_range")),
        source_port_range=_build_port_range(data.get("source_port_range")),
    )


def _build_icmp_options(data):
    """Build IcmpOptions from a dict."""
    if data is None:
        return None
    return IcmpOptions(
        type=data["type"],
        code=data.get("code"),
    )


def _build_add_rule(rule_dict):
    """Build an AddSecurityRuleDetails from a user-supplied dict."""
    return AddSecurityRuleDetails(
        direction=rule_dict["direction"],
        protocol=rule_dict["protocol"],
        source=rule_dict.get("source"),
        source_type=rule_dict.get("source_type"),
        destination=rule_dict.get("destination"),
        destination_type=rule_dict.get("destination_type"),
        tcp_options=_build_tcp_options(rule_dict.get("tcp_options")),
        udp_options=_build_udp_options(rule_dict.get("udp_options")),
        icmp_options=_build_icmp_options(rule_dict.get("icmp_options")),
        description=rule_dict.get("description"),
        is_stateless=rule_dict.get("is_stateless", False),
    )


def _build_update_rule(rule_id, rule_dict):
    """Build an UpdateSecurityRuleDetails from a user-supplied dict."""
    return UpdateSecurityRuleDetails(
        id=rule_id,
        direction=rule_dict["direction"],
        protocol=rule_dict["protocol"],
        source=rule_dict.get("source"),
        source_type=rule_dict.get("source_type"),
        destination=rule_dict.get("destination"),
        destination_type=rule_dict.get("destination_type"),
        tcp_options=_build_tcp_options(rule_dict.get("tcp_options")),
        udp_options=_build_udp_options(rule_dict.get("udp_options")),
        icmp_options=_build_icmp_options(rule_dict.get("icmp_options")),
        description=rule_dict.get("description"),
        is_stateless=rule_dict.get("is_stateless", False),
    )


def _rule_to_dict(rule):
    """Convert an OCI security rule object to a serializable dict."""
    result = {}
    for key in ("id", "direction", "protocol", "source", "source_type",
                "destination", "destination_type", "description", "is_stateless",
                "time_created"):
        val = getattr(rule, key, None)
        if val is not None:
            result[key] = val
    for opt_key in ("tcp_options", "udp_options", "icmp_options"):
        opt = getattr(rule, opt_key, None)
        if opt is not None:
            opt_dict = {}
            if hasattr(opt, "destination_port_range") and opt.destination_port_range:
                opt_dict["destination_port_range"] = {
                    "min": opt.destination_port_range.min,
                    "max": opt.destination_port_range.max,
                }
            if hasattr(opt, "source_port_range") and opt.source_port_range:
                opt_dict["source_port_range"] = {
                    "min": opt.source_port_range.min,
                    "max": opt.source_port_range.max,
                }
            if hasattr(opt, "type") and opt.type is not None:
                opt_dict["type"] = opt.type
            if hasattr(opt, "code") and opt.code is not None:
                opt_dict["code"] = opt.code
            result[opt_key] = opt_dict
    return result


def _list_all_rules(client, nsg_id):
    """List all security rules for the given NSG."""
    rules = []
    response = client.list_network_security_group_security_rules(nsg_id)
    rules.extend(response.data)
    while response.has_next_page:
        response = client.list_network_security_group_security_rules(
            nsg_id, page=response.next_page,
        )
        rules.extend(response.data)
    return rules


def main():
    module_args = dict(
        nsg_id=dict(type="str", required=True),
        security_rules=dict(type="list", elements="dict"),
        purge_rules=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("security_rules",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, VirtualNetworkClient)
    nsg_id = module.params["nsg_id"]
    state = module.params["state"]
    desired_rules = module.params.get("security_rules") or []
    purge_rules = module.params.get("purge_rules", False)

    existing_rules = _list_all_rules(client, nsg_id)
    changed = False

    if state == "absent":
        # Remove all rules
        if existing_rules:
            if module.check_mode:
                module.exit_json(changed=True, security_rules=[])
            rule_ids = [r.id for r in existing_rules]
            details = RemoveNetworkSecurityGroupSecurityRulesDetails(
                security_rule_ids=rule_ids,
            )
            client.remove_network_security_group_security_rules(nsg_id, details)
            changed = True
        final_rules = []
    else:
        # state == present
        if module.check_mode:
            module.exit_json(changed=True)
            return

        # Add the desired rules
        if desired_rules:
            add_details = AddNetworkSecurityGroupSecurityRulesDetails(
                security_rules=[_build_add_rule(r) for r in desired_rules],
            )
            client.add_network_security_group_security_rules(nsg_id, add_details)
            changed = True

        # Purge rules not in the desired set
        if purge_rules and existing_rules:
            rule_ids_to_remove = [r.id for r in existing_rules]
            if rule_ids_to_remove:
                remove_details = RemoveNetworkSecurityGroupSecurityRulesDetails(
                    security_rule_ids=rule_ids_to_remove,
                )
                client.remove_network_security_group_security_rules(nsg_id, remove_details)
                changed = True

        final_rules = _list_all_rules(client, nsg_id)
        final_rules = [_rule_to_dict(r) for r in final_rules]

    module.exit_json(changed=changed, security_rules=final_rules if state == "present" else [])


if __name__ == "__main__":
    main()
