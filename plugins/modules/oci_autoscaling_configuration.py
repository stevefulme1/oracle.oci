# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Autoscaling Configurations."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_autoscaling_configuration
short_description: Manage OCI Autoscaling Configurations
description:
    - Create, update, and delete autoscaling configurations for instance pools
      in Oracle Cloud Infrastructure.
    - Uses the AutoScalingClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment containing the autoscaling configuration.
            - Required when creating a new configuration.
        type: str
    auto_scaling_configuration_id:
        description:
            - The OCID of the autoscaling configuration.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the autoscaling configuration.
        type: str
    cool_down_in_seconds:
        description:
            - The minimum period of time to wait between scaling actions.
        type: int
    is_enabled:
        description:
            - Whether the autoscaling configuration is enabled.
        type: bool
    policies:
        description:
            - Autoscaling policy definitions.
        type: list
        elements: dict
        suboptions:
            policy_type:
                description:
                    - The type of autoscaling policy.
                type: str
                required: true
            capacity:
                description:
                    - The capacity requirements of the autoscaling policy.
                type: dict
            rules:
                description:
                    - Rules for the autoscaling policy.
                type: list
                elements: dict
    resource:
        description:
            - The resource details for the autoscaling configuration.
        type: dict
        suboptions:
            type:
                description:
                    - The type of resource (e.g., instancePool).
                type: str
                required: true
            id:
                description:
                    - The OCID of the resource.
                type: str
                required: true
    state:
        description:
            - The desired state of the autoscaling configuration.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an autoscaling configuration
  oracle.oci.oci_autoscaling_configuration:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-autoscaling-config"
    cool_down_in_seconds: 300
    is_enabled: true
    resource:
      type: instancePool
      id: "ocid1.instancepool.oc1..example"
    policies:
      - policy_type: threshold
        capacity:
          max: 5
          min: 1
          initial: 2
        rules:
          - action:
              type: CHANGE_COUNT_BY
              value: 1
            metric:
              metric_type: CPU_UTILIZATION
              threshold:
                operator: GT
                value: 80
    state: present

- name: Delete an autoscaling configuration
  oracle.oci.oci_autoscaling_configuration:
    auto_scaling_configuration_id: "ocid1.autoscalingconfiguration.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the autoscaling configuration.
    returned: on success
    type: dict
    sample:
        id: "ocid1.autoscalingconfiguration.oc1..example"
        display_name: "my-autoscaling-config"
        cool_down_in_seconds: 300
        is_enabled: true
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.autoscaling import AutoScalingClient
    from oci.autoscaling.models import (
        CreateAutoScalingConfigurationDetails,
        UpdateAutoScalingConfigurationDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciAutoscalingConfiguration(OciResourceBase):
    """Manage OCI Autoscaling Configurations."""

    client_class = AutoScalingClient if HAS_OCI_SDK else None

    def get_resource(self):
        config_id = self.module.params.get("auto_scaling_configuration_id")
        if not config_id:
            return None
        try:
            return call_with_retry(
                self.client.get_auto_scaling_configuration, config_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateAutoScalingConfigurationDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            cool_down_in_seconds=self.module.params.get("cool_down_in_seconds"),
            is_enabled=self.module.params.get("is_enabled"),
            policies=self.module.params.get("policies"),
            resource=self.module.params.get("resource"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.create_auto_scaling_configuration, details
        )
        return response.data

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateAutoScalingConfigurationDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            cool_down_in_seconds=(
                self.module.params.get("cool_down_in_seconds")
                or resource.cool_down_in_seconds
            ),
            is_enabled=self.module.params.get("is_enabled"),
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_auto_scaling_configuration, resource.id, details
        )
        return call_with_retry(
            self.client.get_auto_scaling_configuration, resource.id
        ).data

    def delete_resource(self, resource):
        call_with_retry(
            self.client.delete_auto_scaling_configuration, resource.id
        )

    def _updatable_attributes(self):
        return ["display_name", "cool_down_in_seconds", "is_enabled"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        auto_scaling_configuration_id=dict(type="str"),
        display_name=dict(type="str"),
        cool_down_in_seconds=dict(type="int"),
        is_enabled=dict(type="bool"),
        policies=dict(type="list", elements="dict"),
        resource=dict(type="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciAutoscalingConfiguration(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
