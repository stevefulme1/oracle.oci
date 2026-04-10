#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OKE node pool facts."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_oke_node_pool_facts
short_description: Retrieve facts about OKE node pools
description:
  - Retrieve details about one or more node pools in Oracle Kubernetes Engine (OKE).
  - Use I(node_pool_id) to get a single node pool, or I(compartment_id) and I(cluster_id) to list node pools.
  - This is a read-only module that does not modify any resources.
  - Uses C(oci.container_engine.ContainerEngineClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to list node pools from.
      - Required when listing node pools.
    type: str
  cluster_id:
    description:
      - The OCID of the cluster to list node pools from.
      - Required when listing node pools with I(compartment_id).
    type: str
  node_pool_id:
    description:
      - The OCID of a specific node pool to retrieve.
      - When specified, returns a single node pool instead of a list.
    type: str
  name:
    description:
      - Filter node pools by name.
      - Only used when listing node pools with I(compartment_id).
    type: str
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: List all node pools for a cluster
  oracle.oci.oci_oke_node_pool_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    cluster_id: "ocid1.cluster.oc1.phx.example"
  register: result

- name: Get a specific node pool by ID
  oracle.oci.oci_oke_node_pool_facts:
    node_pool_id: "ocid1.nodepool.oc1.phx.example"
  register: result

- name: List node pools filtered by name
  oracle.oci.oci_oke_node_pool_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    cluster_id: "ocid1.cluster.oc1.phx.example"
    name: "pool-1"
  register: result
"""

RETURN = r"""
node_pools:
  description: List of node pool details.
  returned: on success
  type: list
  elements: dict
  sample:
    - id: "ocid1.nodepool.oc1.phx.example"
      name: "pool-1"
      lifecycle_state: "ACTIVE"
      cluster_id: "ocid1.cluster.oc1.phx.example"
      compartment_id: "ocid1.compartment.oc1..example"
      node_shape: "VM.Standard.E4.Flex"
      node_config_details:
        size: 3
      kubernetes_version: "v1.28.2"
      freeform_tags: {}
      defined_tags: {}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource object to a serializable dict."""
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
                result[key] = to_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    to_dict(item) if hasattr(item, "__dict__") else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    return resource


def list_node_pools(client, module):
    """List node pools in a compartment/cluster with optional filters."""
    compartment_id = module.params["compartment_id"]
    kwargs = dict(compartment_id=compartment_id)

    if module.params.get("cluster_id"):
        kwargs["cluster_id"] = module.params["cluster_id"]
    if module.params.get("name"):
        kwargs["name"] = module.params["name"]

    node_pools = []
    response = client.list_node_pools(**kwargs)
    node_pools.extend(response.data)

    while response.has_next_page:
        response = client.list_node_pools(**kwargs, page=response.next_page)
        node_pools.extend(response.data)

    return [to_dict(np) for np in node_pools]


def get_node_pool(client, module):
    """Get a single node pool by ID."""
    node_pool_id = module.params["node_pool_id"]
    try:
        response = client.get_node_pool(node_pool_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        raise


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cluster_id=dict(type="str"),
        node_pool_id=dict(type="str"),
        name=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "node_pool_id"),
        ],
        required_by={
            "compartment_id": "cluster_id",
        },
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.container_engine.ContainerEngineClient)

    if module.params.get("node_pool_id"):
        node_pools = get_node_pool(client, module)
    else:
        node_pools = list_node_pools(client, module)

    module.exit_json(changed=False, node_pools=node_pools)


if __name__ == "__main__":
    main()
