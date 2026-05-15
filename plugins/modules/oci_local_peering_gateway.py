# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Local Peering Gateways."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_local_peering_gateway
short_description: Manage local peering gateways in OCI
description:
    - Create, update, and delete local peering gateways in Oracle Cloud Infrastructure.
    - Connect two VCNs in the same region via local peering.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the local peering gateway.
            - Required for creating a local peering gateway.
        type: str
    local_peering_gateway_id:
        description:
            - The OCID of the local peering gateway.
            - Required for update and delete operations.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the local peering gateway.
            - Required for creating a local peering gateway.
        type: str
    display_name:
        description:
            - A user-friendly name for the local peering gateway.
        type: str
    peer_id:
        description:
            - The OCID of the peer local peering gateway to connect to.
            - Used to establish the peering connection after creation.
        type: str
    state:
        description:
            - The desired state of the local peering gateway.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a local peering gateway
  stevefulme1.oci_cloud.oci_local_peering_gateway:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "my-lpg"
    state: present

- name: Connect to a peer LPG
  stevefulme1.oci_cloud.oci_local_peering_gateway:
    local_peering_gateway_id: "ocid1.localpeeringgateway.oc1..example"
    peer_id: "ocid1.localpeeringgateway.oc1..peer"
    state: present

- name: Delete a local peering gateway
  stevefulme1.oci_cloud.oci_local_peering_gateway:
    local_peering_gateway_id: "ocid1.localpeeringgateway.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The local peering gateway resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.localpeeringgateway.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-lpg"
        peering_status: "PEERED"
        lifecycle_state: "AVAILABLE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import (
        CreateLocalPeeringGatewayDetails,
        UpdateLocalPeeringGatewayDetails,
        ConnectLocalPeeringGatewaysDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciLocalPeeringGateway(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        lpg_id = self.module.params.get("local_peering_gateway_id")
        if not lpg_id:
            return None
        try:
            return self.client.get_local_peering_gateway(lpg_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateLocalPeeringGatewayDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        lpg = self.client.create_local_peering_gateway(details).data
        resource = wait_for_resource(
            self.module,
            self.client.get_local_peering_gateway,
            lpg.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

        # If peer_id is provided, establish the peering connection
        peer_id = self.module.params.get("peer_id")
        if peer_id:
            connect_details = ConnectLocalPeeringGatewaysDetails(peer_id=peer_id)
            self.client.connect_local_peering_gateways(resource.id, connect_details)
            resource = self.client.get_local_peering_gateway(resource.id).data

        return resource

    def update_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
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

        details = UpdateLocalPeeringGatewayDetails(**kwargs)
        self.client.update_local_peering_gateway(resource.id, details)

        # If peer_id is provided and not yet peered, establish the peering connection
        peer_id = self.module.params.get("peer_id")
        if peer_id and getattr(resource, "peering_status", None) != "PEERED":
            connect_details = ConnectLocalPeeringGatewaysDetails(peer_id=peer_id)
            self.client.connect_local_peering_gateways(resource.id, connect_details)

        return wait_for_resource(
            self.module,
            self.client.get_local_peering_gateway,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_local_peering_gateway(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_local_peering_gateway,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        local_peering_gateway_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        peer_id=dict(type="str"),
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

    oci_lpg = OciLocalPeeringGateway(module)
    oci_lpg.run()


if __name__ == "__main__":
    main()
