#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI container instances."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_container_instance
short_description: Manage OCI container instances
description:
  - Create, update, and delete container instances in Oracle Cloud Infrastructure.
  - Container instances run OCI containers without managing the underlying infrastructure.
  - Uses C(oci.container_instances.ContainerInstanceClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the container instance in.
      - Required when creating a new container instance.
    type: str
  availability_domain:
    description:
      - The availability domain to place the container instance in.
      - Required when creating a new container instance.
    type: str
  display_name:
    description:
      - A user-friendly name for the container instance.
    type: str
  shape:
    description:
      - The shape of the container instance (e.g. CI.Standard.E4.Flex).
      - Required when creating a new container instance.
    type: str
  shape_config:
    description:
      - Shape configuration for the container instance.
    type: dict
    suboptions:
      ocpus:
        description: The total number of OCPUs.
        type: float
      memory_in_gbs:
        description: The total amount of memory in GBs.
        type: float
  containers:
    description:
      - List of containers to run in the container instance.
      - Required when creating a new container instance.
    type: list
    elements: dict
    suboptions:
      image_url:
        description: The container image URL (e.g. docker.io/library/nginx:latest).
        type: str
        required: true
      display_name:
        description: A user-friendly name for the container.
        type: str
      command:
        description: An optional command to override the container entrypoint.
        type: list
        elements: str
      environment_variables:
        description: Environment variables to set in the container.
        type: dict
  vnics:
    description:
      - List of VNIC configurations for the container instance.
      - Required when creating a new container instance.
    type: list
    elements: dict
    suboptions:
      subnet_id:
        description: The OCID of the subnet for the VNIC.
        type: str
        required: true
      display_name:
        description: A user-friendly name for the VNIC.
        type: str
      is_public_ip_assigned:
        description: Whether a public IP should be assigned.
        type: bool
        default: false
  container_instance_id:
    description:
      - The OCID of the container instance. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the container instance.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a container instance
  oracle.oci.oci_container_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-container-instance"
    shape: "CI.Standard.E4.Flex"
    shape_config:
      ocpus: 1
      memory_in_gbs: 4
    containers:
      - image_url: "docker.io/library/nginx:latest"
        display_name: "nginx"
        environment_variables:
          NGINX_PORT: "8080"
    vnics:
      - subnet_id: "ocid1.subnet.oc1.phx.example"
    state: present

- name: Update container instance display name
  oracle.oci.oci_container_instance:
    container_instance_id: "ocid1.containerinstance.oc1.phx.example"
    display_name: "renamed-container"
    state: present

- name: Delete a container instance
  oracle.oci.oci_container_instance:
    container_instance_id: "ocid1.containerinstance.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The container instance details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.containerinstance.oc1.phx.example"
    display_name: "my-container-instance"
    lifecycle_state: "ACTIVE"
    shape: "CI.Standard.E4.Flex"
    availability_domain: "Uocm:PHX-AD-1"
    container_count: 1
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
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


class OciContainerInstance(OciResourceBase):
    """Manage OCI container instances."""

    def __init__(self, module):
        self.client_class = oci.container_instances.ContainerInstanceClient
        super().__init__(module)

    def get_resource(self):
        ci_id = self.module.params.get("container_instance_id")
        if not ci_id:
            return None
        try:
            response = self.client.get_container_instance(ci_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_DELETED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _build_containers(self):
        """Build container details from params."""
        containers_param = self.module.params.get("containers") or []
        result = []
        for c in containers_param:
            kwargs = dict(image_url=c["image_url"])
            if c.get("display_name"):
                kwargs["display_name"] = c["display_name"]
            if c.get("command"):
                kwargs["command"] = c["command"]
            if c.get("environment_variables"):
                kwargs["environment_variables"] = c["environment_variables"]
            result.append(
                oci.container_instances.models.CreateContainerDetails(**kwargs)
            )
        return result

    def _build_vnics(self):
        """Build VNIC details from params."""
        vnics_param = self.module.params.get("vnics") or []
        result = []
        for v in vnics_param:
            kwargs = dict(subnet_id=v["subnet_id"])
            if v.get("display_name"):
                kwargs["display_name"] = v["display_name"]
            if v.get("is_public_ip_assigned") is not None:
                kwargs["is_public_ip_assigned"] = v["is_public_ip_assigned"]
            result.append(
                oci.container_instances.models.CreateContainerVnicDetails(**kwargs)
            )
        return result

    def create_resource(self):
        params = self.module.params

        kwargs = dict(
            compartment_id=params["compartment_id"],
            availability_domain=params["availability_domain"],
            shape=params["shape"],
            containers=self._build_containers(),
            vnics=self._build_vnics(),
        )

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        if params.get("shape_config"):
            sc = params["shape_config"]
            kwargs["shape_config"] = oci.container_instances.models.CreateContainerInstanceShapeConfigDetails(
                ocpus=sc.get("ocpus"),
                memory_in_gbs=sc.get("memory_in_gbs"),
            )

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.container_instances.models.CreateContainerInstanceDetails(**kwargs)
        response = call_with_retry(
            self.client.create_container_instance, create_details,
        )
        ci = response.data

        if self.module.params.get("wait", True):
            ci = wait_for_resource(
                self.module,
                self.client.get_container_instance,
                ci.id,
                target_states={LIFECYCLE_ACTIVE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_DELETED},
            )
        return ci

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.container_instances.models.UpdateContainerInstanceDetails(**kwargs)
        call_with_retry(
            self.client.update_container_instance, resource.id, update_details,
        )

        if self.module.params.get("wait", True):
            return wait_for_resource(
                self.module,
                self.client.get_container_instance,
                resource.id,
                target_states={LIFECYCLE_ACTIVE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_DELETED},
            )
        return self.client.get_container_instance(resource.id).data

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_container_instance, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_container_instance,
                resource.id,
                target_states={LIFECYCLE_DELETED},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        shape=dict(type="str"),
        shape_config=dict(
            type="dict",
            options=dict(
                ocpus=dict(type="float"),
                memory_in_gbs=dict(type="float"),
            ),
        ),
        containers=dict(
            type="list",
            elements="dict",
            options=dict(
                image_url=dict(type="str", required=True),
                display_name=dict(type="str"),
                command=dict(type="list", elements="str"),
                environment_variables=dict(type="dict"),
            ),
        ),
        vnics=dict(
            type="list",
            elements="dict",
            options=dict(
                subnet_id=dict(type="str", required=True),
                display_name=dict(type="str"),
                is_public_ip_assigned=dict(type="bool", default=False),
            ),
        ),
        container_instance_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain", "shape", "containers", "vnics"), True),
            ("state", "absent", ("container_instance_id",)),
        ],
    )

    oci_ci = OciContainerInstance(module)
    oci_ci.run()


if __name__ == "__main__":
    main()
