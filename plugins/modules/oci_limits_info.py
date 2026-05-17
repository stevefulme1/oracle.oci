# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI limit values information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_limits_info
short_description: List OCI service limits
description:
    - Retrieve service limits and usage for a compartment.
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
    service_name:
        description:
            - The target service name to list limits for.
        type: str
        required: true
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: List limit values
  stevefulme1.oci_cloud.oci_limits_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result
"""

RETURN = r"""
limit_values:
    description: List of limit values details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.limits import LimitsClient
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
        service_name=dict(type="str", required=True),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LimitsClient)
    params = module.params

    try:
        response = call_with_retry(client.list_limit_values, compartment_id=params["compartment_id"], service_name=params["service_name"])
        results = [to_dict(item) for item in response.data]
        module.exit_json(changed=False, limit_values=results)
    except ServiceError as e:
        module.fail_json(msg=f"Failed to list limit_values: {e.message}")


if __name__ == "__main__":
    main()
