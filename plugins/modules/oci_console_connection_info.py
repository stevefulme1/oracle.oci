# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI instance console connection information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_console_connection_info
short_description: Retrieve information about OCI instance console connections
description:
    - Retrieve details about one or more instance console connections in Oracle Cloud Infrastructure.
    - Use I(instance_console_connection_id) to get a single resource, or I(compartment_id) to list resources.
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
    instance_console_connection_id:
        description:
            - The OCID of a specific instance console connection to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
"""

EXAMPLES = r"""
- name: List all instance console connections in a compartment
  stevefulme1.oci_cloud.oci_console_connection_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific instance console connection by ID
  stevefulme1.oci_cloud.oci_console_connection_info:
    instance_console_connection_id: "ocid1.instance_console_connection.oc1..example"
  register: result
"""

RETURN = r"""
instance_console_connections:
    description: List of instance console connection details.
    returned: always
    type: list
    elements: dict
"""

try:
    import oci.core
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
    """List instance console connections in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}

    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_instance_console_connections,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single instance console connection by ID."""
    resource_id = module.params["instance_console_connection_id"]
    try:
        response = client.get_instance_console_connection(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        instance_console_connection_id=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "instance_console_connection_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.ComputeClient)

    if module.params.get("instance_console_connection_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, instance_console_connections=resources)


if __name__ == "__main__":
    main()
