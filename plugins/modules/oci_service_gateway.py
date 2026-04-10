# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Service Gateways."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_service_gateway
short_description: Manage service gateways in OCI
description:
    - Create, update, and delete service gateways in Oracle Cloud Infrastructure.
    - A service gateway enables resources in a VCN to access Oracle services
      without exposing data to the public internet.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the service gateway.
            - Required for creating a service gateway.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the service gateway.
            - Required for creating a service gateway.
        type: str
    display_name:
        description:
            - A user-friendly name for the service gateway.
        type: str
    services:
        description:
            - List of service OCIDs that the service gateway will route traffic to.
            - Each element is a dict with a C(service_id) key.
            - Required for creating a service gateway.
        type: list
        elements: dict
        suboptions:
            service_id:
                description:
                    - The OCID of the Oracle service.
                type: str
                required: true
    service_gateway_id:
        description:
            - The OCID of the service gateway.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the service gateway.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a service gateway for Object Storage
  oracle.oci.oci_service_gateway:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    display_name: "my-sgw"
    services:
      - service_id: "ocid1.service.oc1..example"
    state: present

- name: Delete a service gateway
  oracle.oci.oci_service_gateway:
    service_gateway_id: "ocid1.servicegateway.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The service gateway resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.servicegateway.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-sgw"
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
        CreateServiceGatewayDetails,
        UpdateServiceGatewayDetails,
        ServiceIdRequestDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def build_service_id_details(services_param):
    """Convert list of dicts to list of ServiceIdRequestDetails objects."""
    if not services_param:
        return []
    return [
        ServiceIdRequestDetails(service_id=s["service_id"])
        for s in services_param
    ]


class OciServiceGateway(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        sgw_id = self.module.params.get("service_gateway_id")
        if not sgw_id:
            return None
        try:
            return self.client.get_service_gateway(sgw_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateServiceGatewayDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            display_name=self.module.params.get("display_name"),
            services=build_service_id_details(self.module.params.get("services")),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        sgw = self.client.create_service_gateway(details).data
        return wait_for_resource(
            self.module,
            self.client.get_service_gateway,
            sgw.id,
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
        if self.module.params.get("services") is not None:
            kwargs["services"] = build_service_id_details(self.module.params["services"])
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateServiceGatewayDetails(**kwargs)
        self.client.update_service_gateway(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_service_gateway,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_service_gateway(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_service_gateway,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "services"]


def main():
    service_spec = dict(
        service_id=dict(type="str", required=True),
    )

    module_args = dict(
        compartment_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        services=dict(type="list", elements="dict", options=service_spec),
        service_gateway_id=dict(type="str"),
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

    oci_sgw = OciServiceGateway(module)
    oci_sgw.run()


if __name__ == "__main__":
    main()
