#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Mount Targets."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_mount_target
short_description: Manage OCI Mount Targets
description:
    - Create, update, and delete mount targets in Oracle Cloud Infrastructure File Storage.
    - Uses the FileStorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the mount target.
            - Required when creating a new mount target.
        type: str
    availability_domain:
        description:
            - The availability domain for the mount target.
            - Required when creating a new mount target.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet in which to create the mount target.
            - Required when creating a new mount target.
        type: str
    display_name:
        description:
            - A user-friendly name for the mount target.
        type: str
    mount_target_id:
        description:
            - The OCID of an existing mount target.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the mount target.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a mount target
  oracle.oci.oci_mount_target:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    subnet_id: "ocid1.subnet.oc1..example"
    display_name: "my-mount-target"
    state: present

- name: Update a mount target name
  oracle.oci.oci_mount_target:
    mount_target_id: "ocid1.mounttarget.oc1..example"
    display_name: "renamed-mount-target"
    state: present

- name: Delete a mount target
  oracle.oci.oci_mount_target:
    mount_target_id: "ocid1.mounttarget.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the mount target.
    returned: on success
    type: dict
    sample:
        id: "ocid1.mounttarget.oc1..example"
        display_name: "my-mount-target"
        lifecycle_state: "ACTIVE"
        subnet_id: "ocid1.subnet.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.file_storage import FileStorageClient
    from oci.file_storage.models import CreateMountTargetDetails, UpdateMountTargetDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciMountTarget(OciResourceBase):
    """Manage OCI Mount Targets."""

    client_class = FileStorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        mt_id = self.module.params.get("mount_target_id")
        if not mt_id:
            return None
        try:
            return call_with_retry(self.client.get_mount_target, mt_id).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateMountTargetDetails(
            compartment_id=self.module.params["compartment_id"],
            availability_domain=self.module.params["availability_domain"],
            subnet_id=self.module.params["subnet_id"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(self.client.create_mount_target, details)
        return wait_for_resource(
            self.module,
            self.client.get_mount_target,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateMountTargetDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(self.client.update_mount_target, resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_mount_target,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_mount_target, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_mount_target,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        subnet_id=dict(type="str"),
        display_name=dict(type="str"),
        mount_target_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain", "subnet_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciMountTarget(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
