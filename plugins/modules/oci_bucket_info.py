# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI bucket information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_bucket_info
short_description: Retrieve information about OCI buckets
description:
    - Retrieve details about one or more buckets in Oracle Cloud Infrastructure.
    - Use I(bucket_name) to get a single resource, or I(compartment_id) to list resources.
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
    bucket_name:
        description:
            - The OCID of a specific bucket to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
"""

EXAMPLES = r"""
- name: List all buckets in a compartment
  stevefulme1.oci_cloud.oci_bucket_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific bucket by ID
  stevefulme1.oci_cloud.oci_bucket_info:
    bucket_name: "ocid1.bucket.oc1..example"
  register: result
"""

RETURN = r"""
buckets:
    description: List of bucket details.
    returned: always
    type: list
    elements: dict
"""

try:
    import oci.object_storage
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
    """List buckets in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_buckets,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single bucket by ID."""
    resource_id = module.params["bucket_name"]
    try:
        response = client.get_bucket(resource_id)
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
        bucket_name=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "bucket_name"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.object_storage.ObjectStorageClient)

    if module.params.get("bucket_name"):
        resources = get_resource(client, module)
    else:
        resources = list_resources(client, module)

    module.exit_json(changed=False, buckets=resources)


if __name__ == "__main__":
    main()
