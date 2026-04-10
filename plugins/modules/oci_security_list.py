#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Security Lists."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_security_list
short_description: Manage security lists in OCI
description:
    - Create, update, and delete security lists in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the security list.
            - Required for creating a security list.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN to contain the security list.
            - Required for creating a security list.
        type: str
    display_name:
        description:
            - A user-friendly name for the security list.
        type: str
    ingress_security_rules:
        description:
            - Rules for allowing inbound IP packets.
            - Each rule is a dict with keys such as source, protocol, tcp_options,
              udp_options, icmp_options, source_type, is_stateless.
        type: list
        elements: dict
    egress_security_rules:
        description:
            - Rules for allowing outbound IP packets.
            - Each rule is a dict with keys such as destination, protocol,
              tcp_options, udp_options, icmp_options, destination_type, is_stateless.
        type: list
        elements: dict
    security_list_id:
        description:
            - The OCID of the security list.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the security list.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a security list allowing SSH and HTTPS ingress
  oracle.oci.oci_security_list:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "web-seclist"
    ingress_security_rules:
      - source: "0.0.0.0/0"
        protocol: "6"
        tcp_options:
          destination_port_range:
            min: 22
            max: 22
      - source: "0.0.0.0/0"
        protocol: "6"
        tcp_options:
          destination_port_range:
            min: 443
            max: 443
    egress_security_rules:
      - destination: "0.0.0.0/0"
        protocol: "all"
    state: present

- name: Delete a security list
  oracle.oci.oci_security_list:
    security_list_id: "ocid1.securitylist.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The security list resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.securitylist.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "web-seclist"
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
        CreateSecurityListDetails,
        UpdateSecurityListDetails,
        IngressSecurityRule,
        EgressSecurityRule,
        TcpOptions,
        UdpOptions,
        IcmpOptions,
        PortRange,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def _build_port_range(pr_dict):
    """Convert port range dict to PortRange object."""
    if not pr_dict:
        return None
    return PortRange(min=pr_dict["min"], max=pr_dict["max"])


def _build_tcp_options(opts_dict):
    """Convert tcp_options dict to TcpOptions object."""
    if not opts_dict:
        return None
    kwargs = {}
    if "destination_port_range" in opts_dict:
        kwargs["destination_port_range"] = _build_port_range(opts_dict["destination_port_range"])
    if "source_port_range" in opts_dict:
        kwargs["source_port_range"] = _build_port_range(opts_dict["source_port_range"])
    return TcpOptions(**kwargs)


def _build_udp_options(opts_dict):
    """Convert udp_options dict to UdpOptions object."""
    if not opts_dict:
        return None
    kwargs = {}
    if "destination_port_range" in opts_dict:
        kwargs["destination_port_range"] = _build_port_range(opts_dict["destination_port_range"])
    if "source_port_range" in opts_dict:
        kwargs["source_port_range"] = _build_port_range(opts_dict["source_port_range"])
    return UdpOptions(**kwargs)


def _build_icmp_options(opts_dict):
    """Convert icmp_options dict to IcmpOptions object."""
    if not opts_dict:
        return None
    kwargs = {"type": opts_dict["type"]}
    if "code" in opts_dict:
        kwargs["code"] = opts_dict["code"]
    return IcmpOptions(**kwargs)


def build_ingress_rules(rules_param):
    """Convert list of dicts to list of IngressSecurityRule objects."""
    if not rules_param:
        return []
    rules = []
    for r in rules_param:
        rules.append(IngressSecurityRule(
            source=r["source"],
            protocol=r["protocol"],
            source_type=r.get("source_type", "CIDR_BLOCK"),
            is_stateless=r.get("is_stateless", False),
            tcp_options=_build_tcp_options(r.get("tcp_options")),
            udp_options=_build_udp_options(r.get("udp_options")),
            icmp_options=_build_icmp_options(r.get("icmp_options")),
        ))
    return rules


def build_egress_rules(rules_param):
    """Convert list of dicts to list of EgressSecurityRule objects."""
    if not rules_param:
        return []
    rules = []
    for r in rules_param:
        rules.append(EgressSecurityRule(
            destination=r["destination"],
            protocol=r["protocol"],
            destination_type=r.get("destination_type", "CIDR_BLOCK"),
            is_stateless=r.get("is_stateless", False),
            tcp_options=_build_tcp_options(r.get("tcp_options")),
            udp_options=_build_udp_options(r.get("udp_options")),
            icmp_options=_build_icmp_options(r.get("icmp_options")),
        ))
    return rules


class OciSecurityList(OciResourceBase):
    client_class = VirtualNetworkClient

    def get_resource(self):
        sl_id = self.module.params.get("security_list_id")
        if not sl_id:
            return None
        try:
            return self.client.get_security_list(sl_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateSecurityListDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            ingress_security_rules=build_ingress_rules(
                self.module.params.get("ingress_security_rules"),
            ),
            egress_security_rules=build_egress_rules(
                self.module.params.get("egress_security_rules"),
            ),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        sl = self.client.create_security_list(details).data
        return wait_for_resource(
            self.module,
            self.client.get_security_list,
            sl.id,
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
        if self.module.params.get("ingress_security_rules") is not None:
            kwargs["ingress_security_rules"] = build_ingress_rules(
                self.module.params["ingress_security_rules"],
            )
        if self.module.params.get("egress_security_rules") is not None:
            kwargs["egress_security_rules"] = build_egress_rules(
                self.module.params["egress_security_rules"],
            )
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateSecurityListDetails(**kwargs)
        self.client.update_security_list(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_security_list,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_security_list(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_security_list,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "ingress_security_rules", "egress_security_rules"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        ingress_security_rules=dict(type="list", elements="dict"),
        egress_security_rules=dict(type="list", elements="dict"),
        security_list_id=dict(type="str"),
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

    oci_sl = OciSecurityList(module)
    oci_sl.run()


if __name__ == "__main__":
    main()
