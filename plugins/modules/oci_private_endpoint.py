# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Private Endpoints."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_private_endpoint
short_description: Manage private endpoints in OCI
description:
    - Create, update, and delete private endpoints in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK ResourceManagerClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the private endpoint.
            - Required for creating a private endpoint.
        type: str
    private_endpoint_id:
        description:
            - The OCID of the private endpoint.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the private endpoint.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN for the private endpoint.
            - Required for creating a private endpoint.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet for the private endpoint.
            - Required for creating a private endpoint.
        type: str
    description:
        description:
            - A description of the private endpoint.
        type: str
    state:
        description:
            - The desired state of the private endpoint.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a private endpoint
  oracle.oci.oci_private_endpoint:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-private-endpoint"
    vcn_id: "ocid1.vcn.oc1..example"
    subnet_id: "ocid1.subnet.oc1..example"
    description: "Private endpoint for resource manager"
    state: present

- name: Update a private endpoint
  oracle.oci.oci_private_endpoint:
    private_endpoint_id: "ocid1.ormpe.oc1..example"
    display_name: "updated-pe"
    state: present

- name: Delete a private endpoint
  oracle.oci.oci_private_endpoint:
    private_endpoint_id: "ocid1.ormpe.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The private endpoint resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.ormpe.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-private-endpoint"
        vcn_id: "ocid1.vcn.oc1..example"
        subnet_id: "ocid1.subnet.oc1..example"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.resourcemanager import ResourceManagerClient
    from oci.resourcemanager.models import (
        CreatePrivateEndpointDetails,
        UpdatePrivateEndpointDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciPrivateEndpoint(OciResourceBase):
    def __init__(self, module):
        self.client_class = ResourceManagerClient
        super().__init__(module)

    def get_resource(self):
        pe_id = self.module.params.get("private_endpoint_id")
        if not pe_id:
            return None
        try:
            return self.client.get_private_endpoint(pe_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreatePrivateEndpointDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            vcn_id=self.module.params["vcn_id"],
            subnet_id=self.module.params["subnet_id"],
            description=self.module.params.get("description"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        pe = self.client.create_private_endpoint(details).data
        return wait_for_resource(
            self.module,
            self.client.get_private_endpoint,
            pe.id,
            target_states={LIFECYCLE_ACTIVE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("description") is not None:
            kwargs["description"] = self.module.params["description"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdatePrivateEndpointDetails(**kwargs)
        self.client.update_private_endpoint(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_private_endpoint,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_private_endpoint(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_private_endpoint,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "description"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        private_endpoint_id=dict(type="str"),
        display_name=dict(type="str"),
        vcn_id=dict(type="str"),
        subnet_id=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "vcn_id", "subnet_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_pe = OciPrivateEndpoint(module)
    oci_pe.run()


if __name__ == "__main__":
    main()
