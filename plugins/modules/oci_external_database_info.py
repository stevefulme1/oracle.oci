# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI external database connector information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_external_database_info
short_description: Retrieve information about OCI external database connectors
description:
    - Retrieve details about one or more external database connectors in Oracle Cloud Infrastructure.
    - Use I(external_database_connector_id) to get a single resource, or I(compartment_id) to list resources.
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
    external_database_connector_id:
        description:
            - The OCID of a specific external database connector to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    display_name:
        description:
            - Filter results by display name.
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
- name: List all external database connectors in a compartment
  stevefulme1.oci_cloud.oci_external_database_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific external database connector by ID
  stevefulme1.oci_cloud.oci_external_database_info:
    external_database_connector_id: "ocid1.external_database_connector.oc1..example"
  register: result
"""

RETURN = r"""
external_database_connectors:
    description: List of external database connector details.
    returned: always
    type: list
    elements: dict
"""

try:
    import oci.database
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
    """List external database connectors in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("display_name"):
        kwargs["display_name"] = module.params["display_name"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_external_database_connectors,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single external database connector by ID."""
    resource_id = module.params["external_database_connector_id"]
    try:
        response = client.get_external_database_connector(resource_id)
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
        external_database_connector_id=dict(type="str"),
        display_name=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "external_database_connector_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.database.DatabaseClient)

    if module.params.get("external_database_connector_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, external_database_connectors=resources)


if __name__ == "__main__":
    main()
