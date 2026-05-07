# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DNS Traffic Management Steering Policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_traffic_management_steering_policy
short_description: Manage DNS Traffic Management Steering Policies in OCI
description:
    - Create, update, and delete DNS Traffic Management Steering Policies in
      Oracle Cloud Infrastructure.
    - Steering policies enable intelligent DNS-based traffic routing using
      templates such as failover, load balance, or geo-based routing.
    - Uses the OCI Python SDK DnsClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the steering policy.
            - Required for creating a steering policy.
        type: str
    steering_policy_id:
        description:
            - The OCID of the steering policy.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the steering policy.
        type: str
    template:
        description:
            - The steering policy template type.
            - Required for creating a steering policy.
        type: str
        choices:
            - FAILOVER
            - LOAD_BALANCE
            - ROUTE_BY_GEO
            - ROUTE_BY_ASN
            - ROUTE_BY_IP
            - CUSTOM
    answers:
        description:
            - List of DNS answers for the steering policy.
            - Each answer is a dict with keys such as name, rtype, rdata, pool, and is_disabled.
        type: list
        elements: dict
    rules:
        description:
            - List of steering rules that define routing logic.
            - Each rule is a dict with keys such as rule_type, cases, and default_answer_data.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the steering policy.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a failover steering policy
  stevefulme1.oci_cloud.oci_traffic_management_steering_policy:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "failover-policy"
    template: FAILOVER
    answers:
      - name: "primary"
        rtype: "A"
        rdata: "10.0.0.1"
        pool: "primary-pool"
      - name: "secondary"
        rtype: "A"
        rdata: "10.0.0.2"
        pool: "secondary-pool"
    state: present

- name: Update a steering policy
  stevefulme1.oci_cloud.oci_traffic_management_steering_policy:
    steering_policy_id: "ocid1.steeringpolicy.oc1..example"
    display_name: "updated-policy"
    state: present

- name: Delete a steering policy
  stevefulme1.oci_cloud.oci_traffic_management_steering_policy:
    steering_policy_id: "ocid1.steeringpolicy.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Steering Policy resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.steeringpolicy.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "failover-policy"
        template: "FAILOVER"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.dns import DnsClient
    from oci.dns.models import (
        CreateSteeringPolicyDetails,
        UpdateSteeringPolicyDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciTrafficManagementSteeringPolicy(OciResourceBase):
    def __init__(self, module):
        self.client_class = DnsClient
        super().__init__(module)

    def get_resource(self):
        steering_policy_id = self.module.params.get("steering_policy_id")
        if not steering_policy_id:
            return None
        try:
            return self.client.get_steering_policy(steering_policy_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateSteeringPolicyDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            template=self.module.params["template"],
            answers=self.module.params.get("answers"),
            rules=self.module.params.get("rules"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_steering_policy(details).data
        return wait_for_resource(
            self.module,
            self.client.get_steering_policy,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("template") is not None:
            kwargs["template"] = self.module.params["template"]
        if self.module.params.get("answers") is not None:
            kwargs["answers"] = self.module.params["answers"]
        if self.module.params.get("rules") is not None:
            kwargs["rules"] = self.module.params["rules"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateSteeringPolicyDetails(**kwargs)
        self.client.update_steering_policy(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_steering_policy,
            resource.id,
            target_states={"ACTIVE", LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_steering_policy(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_steering_policy,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "template", "answers", "rules"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        steering_policy_id=dict(type="str"),
        display_name=dict(type="str"),
        template=dict(
            type="str",
            choices=[
                "FAILOVER", "LOAD_BALANCE", "ROUTE_BY_GEO",
                "ROUTE_BY_ASN", "ROUTE_BY_IP", "CUSTOM",
            ],
        ),
        answers=dict(type="list", elements="dict"),
        rules=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "template"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciTrafficManagementSteeringPolicy(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
