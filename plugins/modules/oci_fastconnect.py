# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI FastConnect Virtual Circuits."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_fastconnect
short_description: Manage FastConnect Virtual Circuits in OCI
description:
    - Create, update, and delete FastConnect Virtual Circuits in Oracle Cloud Infrastructure.
    - FastConnect provides dedicated, private connectivity between on-premises
      networks and OCI.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the virtual circuit.
            - Required for creating a virtual circuit.
        type: str
    virtual_circuit_id:
        description:
            - The OCID of the virtual circuit.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the virtual circuit.
        type: str
    type:
        description:
            - The type of virtual circuit (PRIVATE or PUBLIC).
            - Required for creating a virtual circuit.
        type: str
        choices: [PRIVATE, PUBLIC]
    bandwidth_shape_name:
        description:
            - The provisioned bandwidth of the virtual circuit.
            - Example values include C(1 Gbps), C(10 Gbps).
        type: str
    cross_connect_mappings:
        description:
            - List of cross-connect or cross-connect group mappings for the virtual circuit.
            - Each mapping is a dict with keys such as cross_connect_or_cross_connect_group_id,
              vlan_tag, customer_bgp_peering_ip, oracle_bgp_peering_ip.
        type: list
        elements: dict
    gateway_id:
        description:
            - The OCID of the dynamic routing gateway (DRG) for private virtual circuits.
        type: str
    provider_name:
        description:
            - The name of the FastConnect provider.
        type: str
    provider_service_name:
        description:
            - The name of the specific provider service.
        type: str
    state:
        description:
            - The desired state of the virtual circuit.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a private FastConnect virtual circuit
  stevefulme1.oci_cloud.oci_fastconnect:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-fastconnect"
    type: PRIVATE
    bandwidth_shape_name: "1 Gbps"
    gateway_id: "ocid1.drg.oc1..example"
    cross_connect_mappings:
      - cross_connect_or_cross_connect_group_id: "ocid1.crossconnect.oc1..example"
        vlan_tag: 100
        customer_bgp_peering_ip: "10.0.0.1/30"
        oracle_bgp_peering_ip: "10.0.0.2/30"
    state: present

- name: Update a virtual circuit
  stevefulme1.oci_cloud.oci_fastconnect:
    virtual_circuit_id: "ocid1.virtualcircuit.oc1..example"
    display_name: "updated-fastconnect"
    bandwidth_shape_name: "10 Gbps"
    state: present

- name: Delete a virtual circuit
  stevefulme1.oci_cloud.oci_fastconnect:
    virtual_circuit_id: "ocid1.virtualcircuit.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Virtual Circuit resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.virtualcircuit.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-fastconnect"
        type: "PRIVATE"
        bandwidth_shape_name: "1 Gbps"
        lifecycle_state: "PROVISIONED"
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
        CreateVirtualCircuitDetails,
        UpdateVirtualCircuitDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciFastConnect(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        virtual_circuit_id = self.module.params.get("virtual_circuit_id")
        if not virtual_circuit_id:
            return None
        try:
            return self.client.get_virtual_circuit(virtual_circuit_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateVirtualCircuitDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            type=self.module.params["type"],
            bandwidth_shape_name=self.module.params.get("bandwidth_shape_name"),
            cross_connect_mappings=self.module.params.get("cross_connect_mappings"),
            gateway_id=self.module.params.get("gateway_id"),
            provider_name=self.module.params.get("provider_name"),
            provider_service_name=self.module.params.get("provider_service_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_virtual_circuit(details).data
        return wait_for_resource(
            self.module,
            self.client.get_virtual_circuit,
            resource.id,
            target_states={"PROVISIONED", LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("bandwidth_shape_name") is not None:
            kwargs["bandwidth_shape_name"] = self.module.params["bandwidth_shape_name"]
        if self.module.params.get("cross_connect_mappings") is not None:
            kwargs["cross_connect_mappings"] = self.module.params["cross_connect_mappings"]
        if self.module.params.get("gateway_id") is not None:
            kwargs["gateway_id"] = self.module.params["gateway_id"]
        if self.module.params.get("provider_name") is not None:
            kwargs["provider_name"] = self.module.params["provider_name"]
        if self.module.params.get("provider_service_name") is not None:
            kwargs["provider_service_name"] = self.module.params["provider_service_name"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateVirtualCircuitDetails(**kwargs)
        self.client.update_virtual_circuit(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_virtual_circuit,
            resource.id,
            target_states={"PROVISIONED", LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_virtual_circuit(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_virtual_circuit,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "bandwidth_shape_name", "cross_connect_mappings",
                "gateway_id", "provider_name", "provider_service_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        virtual_circuit_id=dict(type="str"),
        display_name=dict(type="str"),
        type=dict(type="str", choices=["PRIVATE", "PUBLIC"]),
        bandwidth_shape_name=dict(type="str"),
        cross_connect_mappings=dict(type="list", elements="dict"),
        gateway_id=dict(type="str"),
        provider_name=dict(type="str"),
        provider_service_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "type"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciFastConnect(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
