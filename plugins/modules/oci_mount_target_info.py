# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI mount target information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_mount_target_info
short_description: Retrieve information about OCI mount targets
description:
    - Retrieve details about one or more mount targets in Oracle Cloud Infrastructure.
    - Use I(mount_target_id) to get a single resource, or I(compartment_id) to list resources.
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
    mount_target_id:
        description:
            - The OCID of a specific mount target to retrieve.
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
    limit:
        description:
            - Maximum number of results to return.
        type: int
        default: 1000
    page:
        description:
            - Pagination token from a previous list call.
        type: str
    max_results:
        description:
            - Maximum total number of results to return.
        type: int
        default: 1000
"""

EXAMPLES = r    limit:
        description:
            - Maximum number of results to return.
        type: int
        default: 1000
    page:
        description:
            - Pagination token from a previous list call.
        type: str
    max_results:
        description:
            - Maximum total number of results to return.
        type: int
        default: 1000
"""
- name: List all mount targets in a compartment
  stevefulme1.oci_cloud.oci_mount_target_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific mount target by ID
  stevefulme1.oci_cloud.oci_mount_target_info:
    mount_target_id: "ocid1.mount_target.oc1..example"
  register: result
"""

RETURN = r"""
mount_targets:
    description: List of mount target details.
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
    OCI_COMMON_ARGS = {}


def list_resources(client, module):
    """List mount targets in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("display_name"):
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]
    if module.params.get("availability_domain"):
        kwargs["availability_domain"] = module.params["availability_domain"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_mount_targets,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single mount target by ID."""
    resource_id = module.params["mount_target_id"]
    try:
        response = client.get_mount_target(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        limit=dict(type="int", default=1000),
        page=dict(type="str"),
        max_results=dict(type="int", default=1000),
        compartment_id=dict(type="str"),
        mount_target_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
        availability_domain=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "mount_target_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.file_storage.FileStorageClient)

    if module.params.get("mount_target_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, mount_targets=resources)


if __name__ == "__main__":
    main()
