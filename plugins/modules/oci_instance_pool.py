#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI instance pools."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_instance_pool
short_description: Manage OCI instance pools
description:
  - Create, update, and terminate instance pools in Oracle Cloud Infrastructure.
  - Instance pools manage a group of compute instances as a single resource.
  - Uses C(oci.core.ComputeManagementClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the instance pool in.
      - Required when creating a new pool.
    type: str
  instance_configuration_id:
    description:
      - The OCID of the instance configuration to use for instances in this pool.
      - Required when creating a new pool.
    type: str
  size:
    description:
      - The number of instances to maintain in the pool.
      - Required when creating a new pool.
    type: int
  placement_configurations:
    description:
      - List of placement configurations for pool instances.
      - Each entry specifies an availability domain and subnet.
    type: list
    elements: dict
    suboptions:
      availability_domain:
        description: The availability domain to place instances in.
        type: str
        required: true
      primary_subnet_id:
        description: The OCID of the primary subnet for instances.
        type: str
        required: true
      fault_domains:
        description: List of fault domains to place instances in.
        type: list
        elements: str
  display_name:
    description:
      - A user-friendly name for the instance pool.
    type: str
  pool_id:
    description:
      - The OCID of the instance pool. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the instance pool.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an instance pool
  oracle.oci.oci_instance_pool:
    compartment_id: "ocid1.compartment.oc1..example"
    instance_configuration_id: "ocid1.instanceconfiguration.oc1.phx.example"
    size: 3
    display_name: "my-pool"
    placement_configurations:
      - availability_domain: "Uocm:PHX-AD-1"
        primary_subnet_id: "ocid1.subnet.oc1.phx.example"
    state: present

- name: Scale an instance pool
  oracle.oci.oci_instance_pool:
    pool_id: "ocid1.instancepool.oc1.phx.example"
    size: 5
    state: present

- name: Terminate an instance pool
  oracle.oci.oci_instance_pool:
    pool_id: "ocid1.instancepool.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The instance pool details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.instancepool.oc1.phx.example"
    display_name: "my-pool"
    lifecycle_state: "RUNNING"
    size: 3
    compartment_id: "ocid1.compartment.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_RUNNING,
    LIFECYCLE_TERMINATED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciInstancePool(OciResourceBase):
    """Manage OCI instance pools."""

    def __init__(self, module):
        self.client_class = oci.core.ComputeManagementClient
        super().__init__(module)

    def get_resource(self):
        pool_id = self.module.params.get("pool_id")
        if not pool_id:
            return None
        try:
            response = self.client.get_instance_pool(pool_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_TERMINATED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _build_placement_configs(self):
        """Build placement configuration model list from params."""
        configs = self.module.params.get("placement_configurations") or []
        result = []
        for pc in configs:
            kwargs = dict(
                availability_domain=pc["availability_domain"],
                primary_subnet_id=pc["primary_subnet_id"],
            )
            if pc.get("fault_domains"):
                kwargs["fault_domains"] = pc["fault_domains"]
            result.append(
                oci.core.models.CreateInstancePoolPlacementConfigurationDetails(**kwargs)
            )
        return result

    def create_resource(self):
        params = self.module.params
        kwargs = dict(
            compartment_id=params["compartment_id"],
            instance_configuration_id=params["instance_configuration_id"],
            size=params["size"],
            placement_configurations=self._build_placement_configs(),
        )

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.core.models.CreateInstancePoolDetails(**kwargs)
        response = call_with_retry(self.client.create_instance_pool, create_details)
        pool = response.data

        if self.module.params.get("wait", True):
            pool = wait_for_resource(
                self.module,
                self.client.get_instance_pool,
                pool.id,
                target_states={LIFECYCLE_RUNNING},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return pool

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        if params.get("size") is not None:
            kwargs["size"] = params["size"]

        if params.get("instance_configuration_id"):
            kwargs["instance_configuration_id"] = params["instance_configuration_id"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.core.models.UpdateInstancePoolDetails(**kwargs)
        response = call_with_retry(
            self.client.update_instance_pool, resource.id, update_details,
        )
        pool = response.data

        if self.module.params.get("wait", True):
            pool = wait_for_resource(
                self.module,
                self.client.get_instance_pool,
                pool.id,
                target_states={LIFECYCLE_RUNNING},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return pool

    def delete_resource(self, resource):
        call_with_retry(self.client.terminate_instance_pool, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_instance_pool,
                resource.id,
                target_states={LIFECYCLE_TERMINATED},
            )

    def _updatable_attributes(self):
        return ["display_name", "size", "instance_configuration_id"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        instance_configuration_id=dict(type="str"),
        size=dict(type="int"),
        placement_configurations=dict(
            type="list",
            elements="dict",
            options=dict(
                availability_domain=dict(type="str", required=True),
                primary_subnet_id=dict(type="str", required=True),
                fault_domains=dict(type="list", elements="str"),
            ),
        ),
        display_name=dict(type="str"),
        pool_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present",
             ("compartment_id", "instance_configuration_id", "size", "placement_configurations"),
             True),
            ("state", "absent", ("pool_id",)),
        ],
    )

    oci_pool = OciInstancePool(module)
    oci_pool.run()


if __name__ == "__main__":
    main()
