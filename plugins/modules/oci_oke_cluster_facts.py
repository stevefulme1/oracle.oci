# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OKE cluster facts."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_oke_cluster_facts
short_description: Retrieve facts about OKE clusters
description:
  - Retrieve details about one or more Oracle Kubernetes Engine (OKE) clusters.
  - Use I(cluster_id) to get a single cluster, or I(compartment_id) to list clusters.
  - This is a read-only module that does not modify any resources.
  - Uses C(oci.container_engine.ContainerEngineClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to list clusters from.
      - Required when listing clusters.
    type: str
  cluster_id:
    description:
      - The OCID of a specific cluster to retrieve.
      - When specified, returns a single cluster instead of a list.
    type: str
  name:
    description:
      - Filter clusters by name.
      - Only used when listing clusters with I(compartment_id).
    type: str
  lifecycle_state:
    description:
      - Filter clusters by lifecycle state.
      - Only used when listing clusters with I(compartment_id).
    type: str
    choices:
      - CREATING
      - ACTIVE
      - FAILED
      - DELETING
      - DELETED
      - UPDATING
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: List all OKE clusters in a compartment
  stevefulme1.oci_cloud.oci_oke_cluster_facts:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific cluster by ID
  stevefulme1.oci_cloud.oci_oke_cluster_facts:
    cluster_id: "ocid1.cluster.oc1.phx.example"
  register: result

- name: List active clusters in a compartment
  stevefulme1.oci_cloud.oci_oke_cluster_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    lifecycle_state: "ACTIVE"
  register: result

- name: List clusters filtered by name
  stevefulme1.oci_cloud.oci_oke_cluster_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-k8s-cluster"
  register: result
"""

RETURN = r"""
clusters:
  description: List of cluster details.
  returned: on success
  type: list
  elements: dict
  sample:
    - id: "ocid1.cluster.oc1.phx.example"
      name: "my-k8s-cluster"
      lifecycle_state: "ACTIVE"
      kubernetes_version: "v1.28.2"
      vcn_id: "ocid1.vcn.oc1.phx.example"
      compartment_id: "ocid1.compartment.oc1..example"
      endpoint_config: {}
      options: {}
      metadata: {}
      freeform_tags: {}
      defined_tags: {}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def list_clusters(client, module):
    """List clusters in a compartment with optional filters."""
    compartment_id = module.params["compartment_id"]
    kwargs = dict(compartment_id=compartment_id)

    if module.params.get("name"):
        kwargs["name"] = module.params["name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = [module.params["lifecycle_state"]]

    clusters = []
    response = client.list_clusters(**kwargs)
    clusters.extend(response.data)

    while response.has_next_page:
        response = client.list_clusters(**kwargs, page=response.next_page)
        clusters.extend(response.data)

    return [to_dict(cluster) for cluster in clusters]


def get_cluster(client, module):
    """Get a single cluster by ID."""
    cluster_id = module.params["cluster_id"]
    try:
        response = client.get_cluster(cluster_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        raise


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cluster_id=dict(type="str"),
        name=dict(type="str"),
        lifecycle_state=dict(
            type="str",
            choices=[
                "CREATING",
                "ACTIVE",
                "FAILED",
                "DELETING",
                "DELETED",
                "UPDATING",
            ],
        ),
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
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.container_engine.ContainerEngineClient)

    if module.params.get("cluster_id"):
        clusters = get_cluster(client, module)
    else:
        clusters = list_clusters(client, module)

    module.exit_json(changed=False, clusters=clusters)


if __name__ == "__main__":
    main()
