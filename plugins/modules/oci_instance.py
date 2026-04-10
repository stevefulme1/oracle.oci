#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI compute instances."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_instance
short_description: Manage OCI compute instances
description:
  - Launch, update, and terminate compute instances in Oracle Cloud Infrastructure.
  - Uses the OCI Compute service via C(oci.core.ComputeClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the instance in.
      - Required when creating a new instance.
    type: str
  availability_domain:
    description:
      - The availability domain of the instance.
      - Required when creating a new instance.
    type: str
  shape:
    description:
      - The shape of the instance (e.g. VM.Standard.E4.Flex).
      - Required when creating a new instance.
    type: str
  image_id:
    description:
      - The OCID of the image to use for the instance boot volume.
      - Required when creating a new instance.
    type: str
  display_name:
    description:
      - A user-friendly name for the instance. Does not have to be unique.
    type: str
  subnet_id:
    description:
      - The OCID of the subnet where the VNIC will be created.
      - Required when creating a new instance.
    type: str
  shape_config:
    description:
      - Configuration options for flexible shapes.
    type: dict
    suboptions:
      ocpus:
        description: The total number of OCPUs.
        type: float
      memory_in_gbs:
        description: The total amount of memory in gigabytes.
        type: float
  metadata:
    description:
      - Custom metadata key/value pairs for the instance.
      - Common keys include C(ssh_authorized_keys) and C(user_data).
    type: dict
  instance_id:
    description:
      - The OCID of the instance. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the instance.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Launch a compute instance
  oracle.oci.oci_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    shape: "VM.Standard.E4.Flex"
    image_id: "ocid1.image.oc1.phx.example"
    subnet_id: "ocid1.subnet.oc1.phx.example"
    display_name: "my-instance"
    shape_config:
      ocpus: 2
      memory_in_gbs: 32
    metadata:
      ssh_authorized_keys: "ssh-rsa AAAA..."
    state: present

- name: Update instance display name
  oracle.oci.oci_instance:
    instance_id: "ocid1.instance.oc1.phx.example"
    display_name: "renamed-instance"
    state: present

- name: Terminate a compute instance
  oracle.oci.oci_instance:
    instance_id: "ocid1.instance.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The instance details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.instance.oc1.phx.example"
    display_name: "my-instance"
    lifecycle_state: "RUNNING"
    shape: "VM.Standard.E4.Flex"
    availability_domain: "Uocm:PHX-AD-1"
    compartment_id: "ocid1.compartment.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_RUNNING,
    LIFECYCLE_TERMINATED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
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


class OciInstance(OciResourceBase):
    """Manage OCI compute instances."""

    def __init__(self, module):
        self.client_class = oci.core.ComputeClient
        super().__init__(module)

    def get_resource(self):
        instance_id = self.module.params.get("instance_id")
        if not instance_id:
            return None
        try:
            response = self.client.get_instance(instance_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_TERMINATED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        params = self.module.params
        source_details = oci.core.models.InstanceSourceViaImageDetails(
            image_id=params["image_id"],
        )
        create_vnic_details = oci.core.models.CreateVnicDetails(
            subnet_id=params["subnet_id"],
        )

        kwargs = dict(
            compartment_id=params["compartment_id"],
            availability_domain=params["availability_domain"],
            shape=params["shape"],
            source_details=source_details,
            create_vnic_details=create_vnic_details,
        )

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        if params.get("metadata"):
            kwargs["metadata"] = params["metadata"]

        if params.get("shape_config"):
            sc = params["shape_config"]
            kwargs["shape_config"] = oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=sc.get("ocpus"),
                memory_in_gbs=sc.get("memory_in_gbs"),
            )

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        launch_details = oci.core.models.LaunchInstanceDetails(**kwargs)
        response = call_with_retry(self.client.launch_instance, launch_details)
        instance = response.data

        if self.module.params.get("wait", True):
            instance = wait_for_resource(
                self.module,
                self.client.get_instance,
                instance.id,
                target_states={LIFECYCLE_RUNNING},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return instance

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        if params.get("shape"):
            kwargs["shape"] = params["shape"]

        if params.get("shape_config"):
            sc = params["shape_config"]
            kwargs["shape_config"] = oci.core.models.UpdateInstanceShapeConfigDetails(
                ocpus=sc.get("ocpus"),
                memory_in_gbs=sc.get("memory_in_gbs"),
            )

        if params.get("metadata"):
            kwargs["metadata"] = params["metadata"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.core.models.UpdateInstanceDetails(**kwargs)
        response = call_with_retry(
            self.client.update_instance, resource.id, update_details,
        )
        instance = response.data

        if self.module.params.get("wait", True):
            instance = wait_for_resource(
                self.module,
                self.client.get_instance,
                instance.id,
                target_states={LIFECYCLE_RUNNING},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_TERMINATED},
            )
        return instance

    def delete_resource(self, resource):
        call_with_retry(self.client.terminate_instance, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_instance,
                resource.id,
                target_states={LIFECYCLE_TERMINATED},
            )

    def _updatable_attributes(self):
        return ["display_name", "shape", "metadata"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        shape=dict(type="str"),
        image_id=dict(type="str"),
        display_name=dict(type="str"),
        subnet_id=dict(type="str"),
        shape_config=dict(
            type="dict",
            options=dict(
                ocpus=dict(type="float"),
                memory_in_gbs=dict(type="float"),
            ),
        ),
        metadata=dict(type="dict"),
        instance_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain", "shape", "image_id", "subnet_id"), True),
            ("state", "absent", ("instance_id",)),
        ],
    )

    oci_instance = OciInstance(module)
    oci_instance.run()


if __name__ == "__main__":
    main()
