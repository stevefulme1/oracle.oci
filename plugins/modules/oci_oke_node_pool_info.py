# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OKE node pool information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_oke_node_pool_info
short_description: Retrieve information about OKE node pools
description:
    - Retrieve details about one or more OKE node pools in Oracle Cloud Infrastructure.
    - Use I(node_pool_id) to get a single resource, or I(compartment_id) to list resources.
    - This is a read-only module that does not modify any resources.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to list resources from.
            - Required when listing resources.
        type: str
    cluster_id:
        description:
            - The OCID of the cluster to filter node pools by.
            - Only used when listing with I(compartment_id).
        type: str
    node_pool_id:
        description:
            - The OCID of a specific node pool to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    name:
        description:
            - Filter results by node pool name.
            - Only used when listing with I(compartment_id).
        type: str
    lifecycle_state:
        description:
            - Filter results by lifecycle state.
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
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: List all node pools in a compartment
  stevefulme1.oci_cloud.oci_oke_node_pool_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: List node pools for a specific cluster
  stevefulme1.oci_cloud.oci_oke_node_pool_info:
    compartment_id: "ocid1.compartment.oc1..example"
    cluster_id: "ocid1.cluster.oc1.phx.example"
  register: result

- name: Get a specific node pool by ID
  stevefulme1.oci_cloud.oci_oke_node_pool_info:
    node_pool_id: "ocid1.nodepool.oc1.phx.example"
  register: result
"""

RETURN = r"""
node_pools:
    description: List of OKE node pool details.
    returned: always
    type: list
    elements: dict
    sample:
        - id: "ocid1.nodepool.oc1.phx.example"
          name: "pool-1"
          lifecycle_state: "ACTIVE"
          node_shape: "VM.Standard.E4.Flex"
          size: 3
"""

try:
    import oci.container_engine
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
    """List OKE node pools in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("cluster_id"):
        kwargs["cluster_id"] = module.params["cluster_id"]
    if module.params.get("name"):
        kwargs["name"] = module.params["name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_node_pools,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single OKE node pool by ID."""
    resource_id = module.params["node_pool_id"]
    try:
        response = client.get_node_pool(resource_id)
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
        cluster_id=dict(type="str"),
        node_pool_id=dict(type="str"),
        name=dict(type="str"),
        lifecycle_state=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "node_pool_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="oci python sdk required for this module.")

    client = create_service_client(module, oci.container_engine.ContainerEngineClient)

    if module.params.get("node_pool_id"):
        result = get_resource(client, module)
    else:
        result = list_resources(client, module)

    module.exit_json(changed=False, node_pools=result)


if __name__ == "__main__":
    main()
