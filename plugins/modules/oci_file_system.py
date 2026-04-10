# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI File Systems."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_file_system
short_description: Manage OCI File Systems
description:
    - Create, update, and delete file systems in Oracle Cloud Infrastructure File Storage.
    - Uses the FileStorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the file system.
            - Required when creating a new file system.
        type: str
    availability_domain:
        description:
            - The availability domain for the file system.
            - Required when creating a new file system.
        type: str
    display_name:
        description:
            - A user-friendly name for the file system.
        type: str
    file_system_id:
        description:
            - The OCID of an existing file system.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the file system.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a file system
  oracle.oci.oci_file_system:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-file-system"
    state: present

- name: Update a file system name
  oracle.oci.oci_file_system:
    file_system_id: "ocid1.filesystem.oc1..example"
    display_name: "renamed-file-system"
    state: present

- name: Delete a file system
  oracle.oci.oci_file_system:
    file_system_id: "ocid1.filesystem.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the file system.
    returned: on success
    type: dict
    sample:
        id: "ocid1.filesystem.oc1..example"
        display_name: "my-file-system"
        lifecycle_state: "ACTIVE"
        availability_domain: "Uocm:PHX-AD-1"
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
    from oci.file_storage.models import CreateFileSystemDetails, UpdateFileSystemDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciFileSystem(OciResourceBase):
    """Manage OCI File Systems."""

    client_class = FileStorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        fs_id = self.module.params.get("file_system_id")
        if not fs_id:
            return None
        try:
            return call_with_retry(self.client.get_file_system, fs_id).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateFileSystemDetails(
            compartment_id=self.module.params["compartment_id"],
            availability_domain=self.module.params["availability_domain"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(self.client.create_file_system, details)
        return wait_for_resource(
            self.module,
            self.client.get_file_system,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateFileSystemDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(self.client.update_file_system, resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_file_system,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_file_system, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_file_system,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        file_system_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciFileSystem(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
