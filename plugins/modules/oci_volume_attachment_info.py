# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI volume attachment information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_volume_attachment_info
short_description: Retrieve information about OCI volume attachments
description:
    - Retrieve details about one or more volume attachments in Oracle Cloud Infrastructure.
    - Use I(volume_attachment_id) to get a single resource, or I(compartment_id) to list resources.
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
    volume_attachment_id:
        description:
            - The OCID of a specific volume attachment to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    availability_domain:
        description:
            - Filter results by availability domain.
            - Only used when listing with I(compartment_id).
        type: str
    instance_id:
        description:
            - Filter results by instance id.
            - Only used when listing with I(compartment_id).
        type: str
"""

EXAMPLES = r"""
- name: List all volume attachments in a compartment
  stevefulme1.oci_cloud.oci_volume_attachment_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific volume attachment by ID
  stevefulme1.oci_cloud.oci_volume_attachment_info:
    volume_attachment_id: "ocid1.volume_attachment.oc1..example"
  register: result
"""

RETURN = r"""
volume_attachments:
    description: List of volume attachment details.
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
    """List volume attachments in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}

    if module.params.get("availability_domain"):
        kwargs["availability_domain"] = module.params["availability_domain"]
    if module.params.get("instance_id"):
        kwargs["instance_id"] = module.params["instance_id"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_volume_attachments,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single volume attachment by ID."""
    resource_id = module.params["volume_attachment_id"]
    try:
        response = client.get_volume_attachment(resource_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        module.fail_json(msg=str(e))


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        volume_attachment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        instance_id=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "volume_attachment_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.ComputeClient)

    if module.params.get("volume_attachment_id"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, volume_attachments=resources)


if __name__ == "__main__":
    main()
