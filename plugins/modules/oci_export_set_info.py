# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI export set information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_export_set_info
short_description: Retrieve information about OCI export sets
description:
    - Retrieve details about one or more export sets in Oracle Cloud Infrastructure.
    - Use I(export_set_id) to get a single resource, or I(compartment_id) to list resources.
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
    export_set_id:
        description:
            - The OCID of a specific export set to retrieve.
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
- name: List all export sets in a compartment
  stevefulme1.oci_cloud.oci_export_set_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific export set by ID
  stevefulme1.oci_cloud.oci_export_set_info:
    export_set_id: "ocid1.export_set.oc1..example"
  register: result
"""

RETURN = r"""
export_sets:
    description: List of export set details.
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
    """List export sets in a compartment."""
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
            client.list_export_sets,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single export set by ID."""
    resource_id = module.params["export_set_id"]
    try:
        response = client.get_export_set(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        export_set_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
        availability_domain=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "export_set_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.file_storage.FileStorageClient)

    if module.params.get("export_set_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, export_sets=resources)


if __name__ == "__main__":
    main()
