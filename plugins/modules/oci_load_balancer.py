#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Load Balancers."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_load_balancer
short_description: Manage load balancers in OCI
description:
    - Create, update, and delete load balancers in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK LoadBalancerClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the load balancer.
            - Required for creating a load balancer.
        type: str
    display_name:
        description:
            - A user-friendly name for the load balancer.
            - Required for creating a load balancer.
        type: str
    shape_name:
        description:
            - The shape of the load balancer (e.g., 100Mbps, 400Mbps, flexible).
            - Required for creating a load balancer.
        type: str
    subnet_ids:
        description:
            - List of subnet OCIDs for the load balancer.
            - Required for creating a load balancer.
        type: list
        elements: str
    is_private:
        description:
            - Whether the load balancer has a public or private IP address.
        type: bool
        default: false
    load_balancer_id:
        description:
            - The OCID of the load balancer.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the load balancer.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a public load balancer
  oracle.oci.oci_load_balancer:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-lb"
    shape_name: "flexible"
    subnet_ids:
      - "ocid1.subnet.oc1..example1"
      - "ocid1.subnet.oc1..example2"
    is_private: false
    state: present

- name: Delete a load balancer
  oracle.oci.oci_load_balancer:
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The load balancer resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.loadbalancer.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-lb"
        shape_name: "flexible"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.load_balancer import LoadBalancerClient
    from oci.load_balancer.models import (
        CreateLoadBalancerDetails,
        UpdateLoadBalancerDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciLoadBalancer(OciResourceBase):
    client_class = LoadBalancerClient

    def get_resource(self):
        lb_id = self.module.params.get("load_balancer_id")
        if not lb_id:
            return None
        try:
            return self.client.get_load_balancer(lb_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_work_request,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateLoadBalancerDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params["display_name"],
            shape_name=self.module.params["shape_name"],
            subnet_ids=self.module.params["subnet_ids"],
            is_private=self.module.params.get("is_private", False),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = self.client.create_load_balancer(details)

        if self.module.params.get("wait", True):
            work_request_id = response.headers.get("opc-work-request-id")
            if work_request_id:
                wait_for_work_request(self.module, self.client, work_request_id)

            # Retrieve the created load balancer by listing in the compartment
            lbs = self.client.list_load_balancers(
                self.module.params["compartment_id"],
            ).data
            for lb in lbs:
                if lb.display_name == self.module.params["display_name"]:
                    return lb
        return None

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_work_request,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateLoadBalancerDetails(**kwargs)
        response = self.client.update_load_balancer(resource.id, details)

        if self.module.params.get("wait", True):
            work_request_id = response.headers.get("opc-work-request-id")
            if work_request_id:
                wait_for_work_request(self.module, self.client, work_request_id)

        return self.client.get_load_balancer(resource.id).data

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_work_request,
        )

        response = self.client.delete_load_balancer(resource.id)
        if self.module.params.get("wait", True):
            work_request_id = response.headers.get("opc-work-request-id")
            if work_request_id:
                wait_for_work_request(self.module, self.client, work_request_id)

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        shape_name=dict(type="str"),
        subnet_ids=dict(type="list", elements="str"),
        is_private=dict(type="bool", default=False),
        load_balancer_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "shape_name", "subnet_ids"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_lb = OciLoadBalancer(module)
    oci_lb.run()


if __name__ == "__main__":
    main()
