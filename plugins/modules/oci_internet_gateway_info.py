# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI internet gateway information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_internet_gateway_info
short_description: Retrieve information about OCI internet gateways
description:
    - Retrieve details about one or more internet gateways in Oracle Cloud Infrastructure.
    - Use I(ig_id) to get a single resource, or I(compartment_id) to list resources.
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
    ig_id:
        description:
            - The OCID of a specific internet gateway to retrieve.
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
    vcn_id:
        description:
            - Filter results by vcn id.
            - Only used when listing with I(compartment_id).
        type: str
"""

EXAMPLES = r"""
- name: List all internet gateways in a compartment
  stevefulme1.oci_cloud.oci_internet_gateway_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific internet gateway by ID
  stevefulme1.oci_cloud.oci_internet_gateway_info:
    ig_id: "ocid1.internet_gateway.oc1..example"
  register: result
"""

RETURN = r"""
internet_gateways:
    description: List of internet gateway details.
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
    """List internet gateways in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}

    if module.params.get("display_name"):
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]
    if module.params.get("vcn_id"):
        kwargs["vcn_id"] = module.params["vcn_id"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_internet_gateways,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single internet gateway by ID."""
    resource_id = module.params["ig_id"]
    try:
        response = client.get_internet_gateway(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        ig_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
        vcn_id=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "ig_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.VirtualNetworkClient)

    if module.params.get("ig_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, internet_gateways=resources)


if __name__ == "__main__":
    main()
