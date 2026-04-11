# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI IPSec VPN connections."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ipsec_connection
short_description: Manage IPSec VPN connections in OCI
description:
    - Create, update, and delete IPSec VPN connections in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the IPSec connection.
            - Required for creating an IPSec connection.
        type: str
    ipsc_id:
        description:
            - The OCID of the IPSec connection.
            - Required for update and delete operations.
        type: str
    drg_id:
        description:
            - The OCID of the DRG for the IPSec connection.
            - Required for creating an IPSec connection.
        type: str
    cpe_id:
        description:
            - The OCID of the CPE device for the IPSec connection.
            - Required for creating an IPSec connection.
        type: str
    static_routes:
        description:
            - Static routes to the CPE in CIDR notation.
            - Required for creating an IPSec connection.
        type: list
        elements: str
    display_name:
        description:
            - A user-friendly name for the IPSec connection.
        type: str
    state:
        description:
            - The desired state of the IPSec connection.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an IPSec connection
  oracle.oci.oci_ipsec_connection:
    compartment_id: "ocid1.compartment.oc1..example"
    drg_id: "ocid1.drg.oc1..example"
    cpe_id: "ocid1.cpe.oc1..example"
    static_routes:
      - "10.0.0.0/16"
    display_name: "my-ipsec"
    state: present

- name: Update an IPSec connection
  oracle.oci.oci_ipsec_connection:
    ipsc_id: "ocid1.ipsecconnection.oc1..example"
    display_name: "updated-ipsec"
    state: present

- name: Delete an IPSec connection
  oracle.oci.oci_ipsec_connection:
    ipsc_id: "ocid1.ipsecconnection.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The IPSec connection resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.ipsecconnection.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        drg_id: "ocid1.drg.oc1..example"
        cpe_id: "ocid1.cpe.oc1..example"
        display_name: "my-ipsec"
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
    from oci.core.models import CreateIPSecConnectionDetails, UpdateIPSecConnectionDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciIpsecConnection(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        ipsc_id = self.module.params.get("ipsc_id")
        if not ipsc_id:
            return None
        try:
            return self.client.get_ip_sec_connection(ipsc_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateIPSecConnectionDetails(
            compartment_id=self.module.params["compartment_id"],
            drg_id=self.module.params["drg_id"],
            cpe_id=self.module.params["cpe_id"],
            static_routes=self.module.params["static_routes"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        ipsc = self.client.create_ip_sec_connection(details).data
        return wait_for_resource(
            self.module,
            self.client.get_ip_sec_connection,
            ipsc.id,
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
        if self.module.params.get("static_routes") is not None:
            kwargs["static_routes"] = self.module.params["static_routes"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateIPSecConnectionDetails(**kwargs)
        self.client.update_ip_sec_connection(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_ip_sec_connection,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_ip_sec_connection(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_ip_sec_connection,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "static_routes"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        ipsc_id=dict(type="str"),
        drg_id=dict(type="str"),
        cpe_id=dict(type="str"),
        static_routes=dict(type="list", elements="str"),
        display_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "drg_id", "cpe_id", "static_routes"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_ipsc = OciIpsecConnection(module)
    oci_ipsc.run()


if __name__ == "__main__":
    main()
