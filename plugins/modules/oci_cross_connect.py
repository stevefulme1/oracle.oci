# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Cross-Connects."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_cross_connect
short_description: Manage physical Cross-Connects in OCI
description:
    - Create, update, and delete physical Cross-Connects in Oracle Cloud Infrastructure.
    - Cross-connects represent the physical cabling between your network and OCI
      in a FastConnect location.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the cross-connect.
            - Required for creating a cross-connect.
        type: str
    cross_connect_id:
        description:
            - The OCID of the cross-connect.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the cross-connect.
        type: str
    location_name:
        description:
            - The name of the FastConnect location where the cross-connect is installed.
            - Required for creating a cross-connect.
        type: str
    port_speed_shape_name:
        description:
            - The port speed for the cross-connect.
            - Example values include C(10 Gbps), C(100 Gbps).
            - Required for creating a cross-connect.
        type: str
    cross_connect_group_id:
        description:
            - The OCID of the cross-connect group this cross-connect belongs to.
        type: str
    state:
        description:
            - The desired state of the cross-connect.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a Cross-Connect
  oracle.oci.oci_cross_connect:
    compartment_id: "ocid1.compartment.oc1..example"
    location_name: "Equinix i]DC Phoenix"
    port_speed_shape_name: "10 Gbps"
    display_name: "my-cross-connect"
    state: present

- name: Update a Cross-Connect
  oracle.oci.oci_cross_connect:
    cross_connect_id: "ocid1.crossconnect.oc1..example"
    display_name: "updated-cross-connect"
    state: present

- name: Delete a Cross-Connect
  oracle.oci.oci_cross_connect:
    cross_connect_id: "ocid1.crossconnect.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Cross-Connect resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.crossconnect.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-cross-connect"
        location_name: "Equinix DC Phoenix"
        port_speed_shape_name: "10 Gbps"
        lifecycle_state: "PROVISIONED"
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
        CreateCrossConnectDetails,
        UpdateCrossConnectDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciCrossConnect(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        cross_connect_id = self.module.params.get("cross_connect_id")
        if not cross_connect_id:
            return None
        try:
            return self.client.get_cross_connect(cross_connect_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateCrossConnectDetails(
            compartment_id=self.module.params["compartment_id"],
            location_name=self.module.params["location_name"],
            port_speed_shape_name=self.module.params["port_speed_shape_name"],
            display_name=self.module.params.get("display_name"),
            cross_connect_group_id=self.module.params.get("cross_connect_group_id"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_cross_connect(details).data
        return wait_for_resource(
            self.module,
            self.client.get_cross_connect,
            resource.id,
            target_states={"PROVISIONED", LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("cross_connect_group_id") is not None:
            kwargs["cross_connect_group_id"] = self.module.params["cross_connect_group_id"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateCrossConnectDetails(**kwargs)
        self.client.update_cross_connect(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_cross_connect,
            resource.id,
            target_states={"PROVISIONED", LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_cross_connect(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_cross_connect,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "cross_connect_group_id"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cross_connect_id=dict(type="str"),
        display_name=dict(type="str"),
        location_name=dict(type="str"),
        port_speed_shape_name=dict(type="str"),
        cross_connect_group_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "location_name", "port_speed_shape_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciCrossConnect(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
