# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DHCP Options."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dhcp_options
short_description: Manage DHCP options in OCI
description:
    - Create, update, and delete DHCP options in Oracle Cloud Infrastructure.
    - DHCP options control certain types of configuration for instances in a VCN.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the DHCP options.
            - Required for creating DHCP options.
        type: str
    dhcp_id:
        description:
            - The OCID of the DHCP options.
            - Required for update and delete operations.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the DHCP options.
            - Required for creating DHCP options.
        type: str
    display_name:
        description:
            - A user-friendly name for the DHCP options.
        type: str
    options:
        description:
            - A list of DHCP option configurations.
            - Each item should be a dict with keys type, server_type, and optionally custom_dns_servers.
        type: list
        elements: dict
        suboptions:
            type:
                description:
                    - The type of DHCP option.
                    - Use C(DomainNameServer) or C(SearchDomain).
                type: str
                required: true
            server_type:
                description:
                    - The DNS server type for DomainNameServer options.
                    - Use C(VcnLocalPlusInternet) or C(CustomDnsServer).
                type: str
            custom_dns_servers:
                description:
                    - List of custom DNS server IP addresses.
                    - Required when server_type is C(CustomDnsServer).
                type: list
                elements: str
    state:
        description:
            - The desired state of the DHCP options.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create DHCP options with VCN-local DNS
  oracle.oci.oci_dhcp_options:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "my-dhcp-options"
    options:
      - type: "DomainNameServer"
        server_type: "VcnLocalPlusInternet"
    state: present

- name: Create DHCP options with custom DNS servers
  oracle.oci.oci_dhcp_options:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "custom-dns-dhcp"
    options:
      - type: "DomainNameServer"
        server_type: "CustomDnsServer"
        custom_dns_servers:
          - "8.8.8.8"
          - "8.8.4.4"
    state: present

- name: Delete DHCP options
  oracle.oci.oci_dhcp_options:
    dhcp_id: "ocid1.dhcpoptions.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The DHCP options resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.dhcpoptions.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-dhcp-options"
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
        CreateDhcpDetails,
        UpdateDhcpDetails,
        DhcpDnsOption,
        DhcpSearchDomainOption,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def _build_dhcp_options(options_list):
    """Convert a list of dicts into OCI DHCP option model objects."""
    if not options_list:
        return None
    result = []
    for opt in options_list:
        opt_type = opt.get("type", "")
        if opt_type == "DomainNameServer":
            dhcp_opt = DhcpDnsOption(
                type=opt_type,
                server_type=opt.get("server_type", "VcnLocalPlusInternet"),
                custom_dns_servers=opt.get("custom_dns_servers"),
            )
            result.append(dhcp_opt)
        elif opt_type == "SearchDomain":
            dhcp_opt = DhcpSearchDomainOption(
                type=opt_type,
                search_domain_names=opt.get("search_domain_names", []),
            )
            result.append(dhcp_opt)
    return result


class OciDhcpOptions(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        dhcp_id = self.module.params.get("dhcp_id")
        if not dhcp_id:
            return None
        try:
            return self.client.get_dhcp_options(dhcp_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        dhcp_options = _build_dhcp_options(self.module.params.get("options"))
        details = CreateDhcpDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            options=dhcp_options,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        dhcp = self.client.create_dhcp_options(details).data
        return wait_for_resource(
            self.module,
            self.client.get_dhcp_options,
            dhcp.id,
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
        if self.module.params.get("options") is not None:
            kwargs["options"] = _build_dhcp_options(self.module.params["options"])
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateDhcpDetails(**kwargs)
        self.client.update_dhcp_options(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_dhcp_options,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_dhcp_options(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_dhcp_options,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "options"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        dhcp_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        options=dict(
            type="list",
            elements="dict",
            options=dict(
                type=dict(type="str", required=True),
                server_type=dict(type="str"),
                custom_dns_servers=dict(type="list", elements="str"),
            ),
        ),
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

    oci_dhcp = OciDhcpOptions(module)
    oci_dhcp.run()


if __name__ == "__main__":
    main()
