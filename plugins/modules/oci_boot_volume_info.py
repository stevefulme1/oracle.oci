# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI boot volume information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_boot_volume_info
short_description: Retrieve information about OCI boot volumes
description:
    - Retrieve details about one or more boot volumes in Oracle Cloud Infrastructure.
    - Use I(boot_volume_id) to get a single resource, or I(compartment_id) to list resources.
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
    boot_volume_id:
        description:
            - The OCID of a specific boot volume to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    availability_domain:
        description:
            - Filter results by availability domain.
            - Only used when listing with I(compartment_id).
        type: str
"""

EXAMPLES = r"""
- name: List all boot volumes in a compartment
  stevefulme1.oci_cloud.oci_boot_volume_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific boot volume by ID
  stevefulme1.oci_cloud.oci_boot_volume_info:
    boot_volume_id: "ocid1.boot_volume.oc1..example"
  register: result
"""

RETURN = r"""
boot_volumes:
    description: List of boot volume details.
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
    """List boot volumes in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("availability_domain"):
        kwargs["availability_domain"] = module.params["availability_domain"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_boot_volumes,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single boot volume by ID."""
    resource_id = module.params["boot_volume_id"]
    try:
        response = client.get_boot_volume(resource_id)
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
        boot_volume_id=dict(type="str"),
        availability_domain=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "boot_volume_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.BlockstorageClient)

    if module.params.get("boot_volume_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, boot_volumes=resources)


if __name__ == "__main__":
    main()
