# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI Generative AI Dedicated Cluster information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_generative_ai_dedicated_cluster_info
short_description: Retrieve information about OCI Generative AI Dedicated Clusters
description:
    - Retrieve details about one or more Generative AI Dedicated Clusters in Oracle Cloud Infrastructure.
    - Use I(dedicated_ai_cluster_id) to get a single resource, or I(compartment_id) to list resources.
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
    dedicated_ai_cluster_id:
        description:
            - The OCID of a specific dedicated AI cluster to retrieve.
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
    type:
        description:
            - Filter results by cluster type (HOSTING or FINE_TUNING).
            - Only used when listing with I(compartment_id).
        type: str
        choices:
            - HOSTING
            - FINE_TUNING
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
- name: List all dedicated AI clusters in a compartment
  stevefulme1.oci_cloud.oci_generative_ai_dedicated_cluster_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific dedicated AI cluster by ID
  stevefulme1.oci_cloud.oci_generative_ai_dedicated_cluster_info:
    dedicated_ai_cluster_id: "ocid1.generativeaidedicatedaicluster.oc1..example"
  register: result

- name: List HOSTING clusters
  stevefulme1.oci_cloud.oci_generative_ai_dedicated_cluster_info:
    compartment_id: "ocid1.compartment.oc1..example"
    type: HOSTING
  register: result
"""

RETURN = r"""
dedicated_ai_clusters:
    description: List of Generative AI Dedicated Cluster details.
    returned: always
    type: list
    elements: dict
    sample:
        - id: "ocid1.generativeaidedicatedaicluster.oc1..example"
          display_name: "my-hosting-cluster"
          lifecycle_state: "ACTIVE"
          type: "HOSTING"
          unit_count: 1
"""

try:
    import oci.generative_ai
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
    """List dedicated AI clusters in a compartment."""
    compartment_id = module.params["compartment_id"]
    kwargs = {}
    if module.params.get("limit"):
        kwargs["limit"] = module.params["limit"]
    if module.params.get("page"):
        kwargs["page"] = module.params["page"]

    if module.params.get("display_name"):
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]
    if module.params.get("type"):
        kwargs["type"] = module.params["type"]
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_dedicated_ai_clusters,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single dedicated AI cluster by ID."""
    resource_id = module.params["dedicated_ai_cluster_id"]
    try:
        response = client.get_dedicated_ai_cluster(resource_id)
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
        dedicated_ai_cluster_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
        type=dict(type="str", choices=["HOSTING", "FINE_TUNING"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "dedicated_ai_cluster_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="oci python sdk required for this module.")

    client = create_service_client(module, oci.generative_ai.GenerativeAiClient)

    if module.params.get("dedicated_ai_cluster_id"):
        result = get_resource(client, module)
    else:
        result = list_resources(client, module)

    module.exit_json(changed=False, dedicated_ai_clusters=result)


if __name__ == "__main__":
    main()
