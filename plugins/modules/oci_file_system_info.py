# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI file system information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_file_system_info
short_description: Retrieve information about OCI file systems
description:
    - Retrieve details about one or more file systems in Oracle Cloud Infrastructure.
    - Use I(file_system_id) to get a single resource, or I(compartment_id) to list resources.
    - This is a read-only module that does not modify any resources.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to list resources from.
            - Required when listing resources.
        type: str
    file_system_id:
        description:
            - The OCID of a specific file system to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    display_name:
        description:
            - Filter results by display name.
            - Only used when listing with I(compartment_id).
        type: str
    lifecycle_state:
        description:
            - Filter results by lifecycle state.
            - Only used when listing with I(compartment_id).
        type: str
    availability_domain:
        description:
            - Filter results by availability domain.
            - Only used when listing with I(compartment_id).
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: List all file systems in a compartment
  stevefulme1.oci_cloud.oci_file_system_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific file system by ID
  stevefulme1.oci_cloud.oci_file_system_info:
    file_system_id: "ocid1.file_system.oc1..example"
  register: result
"""

RETURN = r"""
file_systems:
    description: List of file system details.
    returned: always
    type: list
    elements: dict
"""

try:
    import oci.file_storage
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
        OCI_COMMON_ARGS,
        create_service_client,
        to_dict,
    )
except ImportError:
    from ansible.module_utils.basic import missing_required_lib
    OCI_COMMON_ARGS = {}


def list_resources(client, module):
    """List file systems in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}

        if module.params.get("display_name"):
            kwargs["display_name"] = module.params["display_name"]
        if module.params.get("lifecycle_state"):
            kwargs["lifecycle_state"] = module.params["lifecycle_state"]
        if module.params.get("availability_domain"):
            kwargs["availability_domain"] = module.params["availability_domain"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_file_systems,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single file system by ID."""
    resource_id = module.params["file_system_id"]
    try:
        response = client.get_file_system(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        file_system_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
        availability_domain=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "file_system_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.file_storage.FileStorageClient)

    if module.params.get("file_system_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, file_systems=resources)


if __name__ == "__main__":
    main()
