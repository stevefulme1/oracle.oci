# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI usage summaries information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_usage_info
short_description: Retrieve OCI usage and cost data
description:
    - Query usage data for cost tracking and billing analysis.
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
    time_usage_started:
        description:
            - Start time for usage query in RFC3339 format.
        type: str
        required: true
    time_usage_ended:
        description:
            - End time for usage query in RFC3339 format.
        type: str
        required: true
    granularity:
        description:
            - The usage granularity.
        type: str
        default: DAILY
        choices:
            - HOURLY
            - DAILY
            - MONTHLY
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: List usage summaries
  stevefulme1.oci_cloud.oci_usage_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result
"""

RETURN = r"""
usage_summaries:
    description: List of usage summaries details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.usage_api import UsageapiClient
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
        time_usage_started=dict(type="str", required=True),
        time_usage_ended=dict(type="str", required=True),
        granularity=dict(type="str", default="DAILY", choices=["HOURLY", "DAILY", "MONTHLY"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, UsageapiClient)
    params = module.params

    try:
        from oci.usage_api.models import RequestSummarizedUsagesDetails
        request_details = RequestSummarizedUsagesDetails(
            tenant_id=params["compartment_id"],
            time_usage_started=params["time_usage_started"],
            time_usage_ended=params["time_usage_ended"],
            granularity=params.get("granularity", "DAILY"),
        )
        response = call_with_retry(client.request_summarized_usages, request_details)
        results = [to_dict(item) for item in response.data.items]
        module.exit_json(changed=False, usage_summaries=results)
    except ServiceError as e:
        module.fail_json(msg=f"Failed to query usage data: {e.message}")


if __name__ == "__main__":
    main()
