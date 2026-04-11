# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Network Load Balancers."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_network_load_balancer
short_description: Manage network load balancers in OCI
description:
    - Create, update, and delete network load balancers in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK NetworkLoadBalancerClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the network load balancer.
            - Required for creating a network load balancer.
        type: str
    network_load_balancer_id:
        description:
            - The OCID of the network load balancer.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the network load balancer.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet in which the network load balancer is created.
            - Required for creating a network load balancer.
        type: str
    is_private:
        description:
            - Whether the network load balancer has a private IP address.
        type: bool
        default: false
    is_preserve_source_destination:
        description:
            - Whether the network load balancer preserves source and destination.
        type: bool
        default: false
    listeners:
        description:
            - Listeners for the network load balancer.
        type: dict
    backend_sets:
        description:
            - Backend sets for the network load balancer.
        type: dict
    state:
        description:
            - The desired state of the network load balancer.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a network load balancer
  oracle.oci.oci_network_load_balancer:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-nlb"
    subnet_id: "ocid1.subnet.oc1..example"
    is_private: false
    state: present

- name: Update a network load balancer
  oracle.oci.oci_network_load_balancer:
    network_load_balancer_id: "ocid1.networkloadbalancer.oc1..example"
    display_name: "updated-nlb"
    state: present

- name: Delete a network load balancer
  oracle.oci.oci_network_load_balancer:
    network_load_balancer_id: "ocid1.networkloadbalancer.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The network load balancer resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.networkloadbalancer.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-nlb"
        subnet_id: "ocid1.subnet.oc1..example"
        is_private: false
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
    from oci.network_load_balancer import NetworkLoadBalancerClient
    from oci.network_load_balancer.models import (
        CreateNetworkLoadBalancerDetails,
        UpdateNetworkLoadBalancerDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciNetworkLoadBalancer(OciResourceBase):
    def __init__(self, module):
        self.client_class = NetworkLoadBalancerClient
        super().__init__(module)

    def get_resource(self):
        nlb_id = self.module.params.get("network_load_balancer_id")
        if not nlb_id:
            return None
        try:
            return self.client.get_network_load_balancer(nlb_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateNetworkLoadBalancerDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            subnet_id=self.module.params["subnet_id"],
            is_private=self.module.params.get("is_private", False),
            is_preserve_source_destination=self.module.params.get("is_preserve_source_destination", False),
            listeners=self.module.params.get("listeners"),
            backend_sets=self.module.params.get("backend_sets"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        nlb = self.client.create_network_load_balancer(details).data
        return wait_for_resource(
            self.module,
            self.client.get_network_load_balancer,
            nlb.id,
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
        if self.module.params.get("is_preserve_source_destination") is not None:
            kwargs["is_preserve_source_destination"] = self.module.params["is_preserve_source_destination"]
        if self.module.params.get("listeners") is not None:
            kwargs["listeners"] = self.module.params["listeners"]
        if self.module.params.get("backend_sets") is not None:
            kwargs["backend_sets"] = self.module.params["backend_sets"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateNetworkLoadBalancerDetails(**kwargs)
        self.client.update_network_load_balancer(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_network_load_balancer,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_network_load_balancer(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_network_load_balancer,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "is_preserve_source_destination", "listeners", "backend_sets"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        network_load_balancer_id=dict(type="str"),
        display_name=dict(type="str"),
        subnet_id=dict(type="str"),
        is_private=dict(type="bool", default=False),
        is_preserve_source_destination=dict(type="bool", default=False),
        listeners=dict(type="dict"),
        backend_sets=dict(type="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "subnet_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_nlb = OciNetworkLoadBalancer(module)
    oci_nlb.run()


if __name__ == "__main__":
    main()
