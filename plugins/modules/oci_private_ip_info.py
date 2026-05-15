# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI private ip information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_private_ip_info
short_description: Retrieve information about OCI private ips
description:
    - Retrieve details about one or more private ips in Oracle Cloud Infrastructure.
    - Use I(private_ip_id) to get a single resource, or I(compartment_id) to list resources.
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
    private_ip_id:
        description:
            - The OCID of a specific private ip to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    subnet_id:
        description:
            - Filter results by subnet id.
            - Only used when listing with I(compartment_id).
        type: str
    vnic_id:
        description:
            - Filter results by vnic id.
            - Only used when listing with I(compartment_id).
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: List all private ips in a compartment
  stevefulme1.oci_cloud.oci_private_ip_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific private ip by ID
  stevefulme1.oci_cloud.oci_private_ip_info:
    private_ip_id: "ocid1.private_ip.oc1..example"
  register: result
"""

RETURN = r"""
private_ips:
    description: List of private ip details.
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
    """List private ips in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}

    if module.params.get("subnet_id"):
        kwargs["subnet_id"] = module.params["subnet_id"]
    if module.params.get("vnic_id"):
        kwargs["vnic_id"] = module.params["vnic_id"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_private_ips,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single private ip by ID."""
    resource_id = module.params["private_ip_id"]
    try:
        response = client.get_private_ip(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        private_ip_id=dict(type="str"),
        subnet_id=dict(type="str"),
        vnic_id=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "private_ip_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.VirtualNetworkClient)

    if module.params.get("private_ip_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, private_ips=resources)


if __name__ == "__main__":
    main()
