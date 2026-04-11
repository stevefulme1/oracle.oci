# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Remote Peering Connections."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_remote_peering_connection
short_description: Manage remote peering connections in OCI
description:
    - Create, update, and delete remote peering connections in Oracle Cloud Infrastructure.
    - Enables cross-region VCN peering through DRG attachments.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the remote peering connection.
            - Required for creating a remote peering connection.
        type: str
    remote_peering_connection_id:
        description:
            - The OCID of the remote peering connection.
            - Required for update and delete operations.
        type: str
    drg_id:
        description:
            - The OCID of the DRG for the remote peering connection.
            - Required for creating a remote peering connection.
        type: str
    display_name:
        description:
            - A user-friendly name for the remote peering connection.
        type: str
    peer_id:
        description:
            - The OCID of the peer remote peering connection in the remote region.
            - Used to establish the peering connection.
        type: str
    peer_region_name:
        description:
            - The name of the region containing the peer remote peering connection.
            - Required when establishing a peering connection with peer_id.
        type: str
    state:
        description:
            - The desired state of the remote peering connection.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a remote peering connection
  oracle.oci.oci_remote_peering_connection:
    compartment_id: "ocid1.compartment.oc1..example"
    drg_id: "ocid1.drg.oc1..example"
    display_name: "my-rpc"
    state: present

- name: Connect to a peer RPC in another region
  oracle.oci.oci_remote_peering_connection:
    remote_peering_connection_id: "ocid1.remotepeeringconnection.oc1..example"
    peer_id: "ocid1.remotepeeringconnection.oc1..peer"
    peer_region_name: "us-ashburn-1"
    state: present

- name: Delete a remote peering connection
  oracle.oci.oci_remote_peering_connection:
    remote_peering_connection_id: "ocid1.remotepeeringconnection.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The remote peering connection resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.remotepeeringconnection.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        drg_id: "ocid1.drg.oc1..example"
        display_name: "my-rpc"
        peering_status: "PEERED"
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
        CreateRemotePeeringConnectionDetails,
        UpdateRemotePeeringConnectionDetails,
        ConnectRemotePeeringConnectionsDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciRemotePeeringConnection(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        rpc_id = self.module.params.get("remote_peering_connection_id")
        if not rpc_id:
            return None
        try:
            return self.client.get_remote_peering_connection(rpc_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateRemotePeeringConnectionDetails(
            compartment_id=self.module.params["compartment_id"],
            drg_id=self.module.params["drg_id"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        rpc = self.client.create_remote_peering_connection(details).data
        resource = wait_for_resource(
            self.module,
            self.client.get_remote_peering_connection,
            rpc.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

        # If peer_id and peer_region_name are provided, establish the peering
        peer_id = self.module.params.get("peer_id")
        peer_region_name = self.module.params.get("peer_region_name")
        if peer_id and peer_region_name:
            connect_details = ConnectRemotePeeringConnectionsDetails(
                peer_id=peer_id,
                peer_region_name=peer_region_name,
            )
            self.client.connect_remote_peering_connections(resource.id, connect_details)
            resource = self.client.get_remote_peering_connection(resource.id).data

        return resource

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

        details = UpdateRemotePeeringConnectionDetails(**kwargs)
        self.client.update_remote_peering_connection(resource.id, details)

        # If peer_id and peer_region_name are provided and not yet peered
        peer_id = self.module.params.get("peer_id")
        peer_region_name = self.module.params.get("peer_region_name")
        if peer_id and peer_region_name and getattr(resource, "peering_status", None) != "PEERED":
            connect_details = ConnectRemotePeeringConnectionsDetails(
                peer_id=peer_id,
                peer_region_name=peer_region_name,
            )
            self.client.connect_remote_peering_connections(resource.id, connect_details)

        return wait_for_resource(
            self.module,
            self.client.get_remote_peering_connection,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_remote_peering_connection(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_remote_peering_connection,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        remote_peering_connection_id=dict(type="str"),
        drg_id=dict(type="str"),
        display_name=dict(type="str"),
        peer_id=dict(type="str"),
        peer_region_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "drg_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_rpc = OciRemotePeeringConnection(module)
    oci_rpc.run()


if __name__ == "__main__":
    main()
