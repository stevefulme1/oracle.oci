# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI recommendations information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_cloud_advisor_recommendation_info
short_description: List OCI Cloud Advisor recommendations
description:
    - Retrieve cost optimization and security recommendations.
    - This is a read-only module that does not modify any resources.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: List recommendations
  stevefulme1.oci_cloud.oci_cloud_advisor_recommendation_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result
"""

RETURN = r"""
recommendations:
    description: List of recommendations details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.optimizer import OptimizerClient
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry


def main():
    module_args = dict(
        compartment_id=dict(type="str", required=True),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, OptimizerClient)
    params = module.params

    try:
        response = call_with_retry(client.list_recommendations, compartment_id=params["compartment_id"], compartment_id_in_subtree=True)
        results = [to_dict(item) for item in response.data]
        module.exit_json(changed=False, recommendations=results)
    except ServiceError as e:
        module.fail_json(msg=f"Failed to list recommendations: {e.message}")


if __name__ == "__main__":
    main()
