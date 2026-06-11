# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OKE cluster information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_oke_cluster_info
short_description: Retrieve information about OKE clusters
description:
    - Retrieve details about one or more OKE (Oracle Kubernetes Engine) clusters in Oracle Cloud Infrastructure.
    - Use I(cluster_id) to get a single resource, or I(compartment_id) to list resources.
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
            - The OCID of a specific cluster to retrieve.
            - When specified, returns a single resource instead of a list.
        type: str
    name:
        description:
            - Filter results by cluster name.
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
- name: List all OKE clusters in a compartment
  stevefulme1.oci_cloud.oci_oke_cluster_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific cluster by ID
  stevefulme1.oci_cloud.oci_oke_cluster_info:
    cluster_id: "ocid1.cluster.oc1.phx.example"
  register: result

- name: List clusters by name
  stevefulme1.oci_cloud.oci_oke_cluster_info:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-k8s-cluster"
  register: result
"""

RETURN = r"""
clusters:
    description: List of OKE cluster details.
    returned: always
    type: list
    elements: dict
    sample:
        - id: "ocid1.cluster.oc1.phx.example"
          name: "my-k8s-cluster"
          lifecycle_state: "ACTIVE"
          kubernetes_version: "v1.28.2"
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
    """List OKE clusters in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("name"):
        kwargs["name"] = module.params["name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_clusters,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single OKE cluster by ID."""
    resource_id = module.params["cluster_id"]
    try:
        response = client.get_cluster(resource_id)
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
        name=dict(type="str"),
        lifecycle_state=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "cluster_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="oci python sdk required for this module.")

    client = create_service_client(module, oci.container_engine.ContainerEngineClient)

    if module.params.get("cluster_id"):
        result = get_resource(client, module)
    else:
        result = list_resources(client, module)

    module.exit_json(changed=False, clusters=result)


if __name__ == "__main__":
    main()
