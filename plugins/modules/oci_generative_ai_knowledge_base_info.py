# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI Generative AI Knowledge Base information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_generative_ai_knowledge_base_info
short_description: Retrieve information about OCI Generative AI Knowledge Bases
description:
    - Retrieve details about one or more Generative AI Knowledge Bases in Oracle Cloud Infrastructure.
    - Use I(knowledge_base_id) to get a single resource, or I(compartment_id) to list resources.
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
    knowledge_base_id:
        description:
            - The OCID of a specific knowledge base to retrieve.
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
- name: List all knowledge bases in a compartment
  stevefulme1.oci_cloud.oci_generative_ai_knowledge_base_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific knowledge base by ID
  stevefulme1.oci_cloud.oci_generative_ai_knowledge_base_info:
    knowledge_base_id: "ocid1.generativeaiagentknowledgebase.oc1..example"
  register: result
"""

RETURN = r"""
knowledge_bases:
    description: List of Generative AI Knowledge Base details.
    returned: always
    type: list
    elements: dict
    sample:
        - id: "ocid1.generativeaiagentknowledgebase.oc1..example"
          display_name: "product-docs-kb"
          lifecycle_state: "ACTIVE"
"""

try:
    import oci.generative_ai_agent
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
    """List knowledge bases in a compartment."""
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
    try:
        response = oci.pagination.list_call_get_all_results(
            client.list_knowledge_bases,
            compartment_id,
            **kwargs,
        )
        return [to_dict(item) for item in response.data]
    except oci.exceptions.ServiceError as e:
        module.fail_json(msg=str(e))


def get_resource(client, module):
    """Get a single knowledge base by ID."""
    resource_id = module.params["knowledge_base_id"]
    try:
        response = client.get_knowledge_base(resource_id)
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
        knowledge_base_id=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "knowledge_base_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="oci python sdk required for this module.")

    client = create_service_client(module, oci.generative_ai_agent.GenerativeAiAgentClient)

    if module.params.get("knowledge_base_id"):
        result = get_resource(client, module)
    else:
        result = list_resources(client, module)

    module.exit_json(changed=False, knowledge_bases=result)


if __name__ == "__main__":
    main()
