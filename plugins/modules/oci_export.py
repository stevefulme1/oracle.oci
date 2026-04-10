# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI File System Exports."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_export
short_description: Manage OCI File System Exports
description:
    - Create, update, and delete file system exports in Oracle Cloud Infrastructure File Storage.
    - Exports make a file system accessible via a mount target.
    - Uses the FileStorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    export_set_id:
        description:
            - The OCID of the export set for the export.
            - Required when creating a new export.
        type: str
    file_system_id:
        description:
            - The OCID of the file system to export.
            - Required when creating a new export.
        type: str
    path:
        description:
            - The export path. Must begin with a forward slash.
            - Required when creating a new export.
        type: str
    export_options:
        description:
            - A list of export options controlling NFS client access.
            - Each item is a dict with keys C(source), C(require_privileged_source_port), and C(access).
        type: list
        elements: dict
        suboptions:
            source:
                description:
                    - CIDR block or IP address for the client source.
                type: str
                required: true
            require_privileged_source_port:
                description:
                    - Whether to require a privileged source port.
                type: bool
                default: true
            access:
                description:
                    - The access level granted to the client.
                type: str
                default: READ_ONLY
                choices: [READ_WRITE, READ_ONLY]
    export_id:
        description:
            - The OCID of an existing export.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the export.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a file system export
  oracle.oci.oci_export:
    export_set_id: "ocid1.exportset.oc1..example"
    file_system_id: "ocid1.filesystem.oc1..example"
    path: "/shared"
    export_options:
      - source: "10.0.0.0/16"
        require_privileged_source_port: true
        access: READ_WRITE
      - source: "0.0.0.0/0"
        require_privileged_source_port: true
        access: READ_ONLY
    state: present

- name: Update export options
  oracle.oci.oci_export:
    export_id: "ocid1.export.oc1..example"
    export_options:
      - source: "10.0.0.0/8"
        access: READ_WRITE
    state: present

- name: Delete an export
  oracle.oci.oci_export:
    export_id: "ocid1.export.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the export.
    returned: on success
    type: dict
    sample:
        id: "ocid1.export.oc1..example"
        export_set_id: "ocid1.exportset.oc1..example"
        file_system_id: "ocid1.filesystem.oc1..example"
        path: "/shared"
        lifecycle_state: "ACTIVE"
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
    from oci.file_storage.models import (
        ClientOptions,
        CreateExportDetails,
        UpdateExportDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def build_client_options(export_options_list):
    """Convert a list of dicts to a list of ClientOptions objects."""
    if not export_options_list:
        return None
    result = []
    for opt in export_options_list:
        result.append(
            ClientOptions(
                source=opt["source"],
                require_privileged_source_port=opt.get("require_privileged_source_port", True),
                access=opt.get("access", "READ_ONLY"),
            )
        )
    return result


class OciExport(OciResourceBase):
    """Manage OCI File System Exports."""

    client_class = FileStorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        export_id = self.module.params.get("export_id")
        if not export_id:
            return None
        try:
            return call_with_retry(self.client.get_export, export_id).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        export_options = build_client_options(self.module.params.get("export_options"))
        details = CreateExportDetails(
            export_set_id=self.module.params["export_set_id"],
            file_system_id=self.module.params["file_system_id"],
            path=self.module.params["path"],
            export_options=export_options,
        )
        response = call_with_retry(self.client.create_export, details)
        return wait_for_resource(
            self.module,
            self.client.get_export,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        export_options = build_client_options(self.module.params.get("export_options"))
        details = UpdateExportDetails(
            export_options=export_options if export_options is not None else resource.export_options,
        )
        call_with_retry(self.client.update_export, resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_export,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_export, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_export,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def needs_update(self, resource):
        """Check if export options differ from desired state."""
        desired_options = self.module.params.get("export_options")
        if desired_options is None:
            return False

        current_options = resource.export_options or []
        if len(desired_options) != len(current_options):
            return True

        for desired, current in zip(desired_options, current_options):
            if desired.get("source") != getattr(current, "source", None):
                return True
            if desired.get("access", "READ_ONLY") != getattr(current, "access", None):
                return True
            if desired.get("require_privileged_source_port", True) != getattr(
                current, "require_privileged_source_port", None
            ):
                return True
        return False

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        export_set_id=dict(type="str"),
        file_system_id=dict(type="str"),
        path=dict(type="str"),
        export_options=dict(
            type="list",
            elements="dict",
            options=dict(
                source=dict(type="str", required=True),
                require_privileged_source_port=dict(type="bool", default=True),
                access=dict(
                    type="str",
                    default="READ_ONLY",
                    choices=["READ_WRITE", "READ_ONLY"],
                ),
            ),
        ),
        export_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("export_set_id", "file_system_id", "path"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciExport(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
