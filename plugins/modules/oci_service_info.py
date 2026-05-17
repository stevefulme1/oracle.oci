# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI services information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_service_info
short_description: List OCI services
description:
    - Retrieve information about available OCI services for service gateways.
    - This is a read-only module that does not modify any resources.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: List services
  stevefulme1.oci_cloud.oci_service_info:
  register: result
"""

RETURN = r"""
services:
    description: List of services details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.core import VirtualNetworkClient
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
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, VirtualNetworkClient)

    try:
        response = call_with_retry(client.list_services)
        results = [to_dict(item) for item in response.data]
        module.exit_json(changed=False, services=results)
    except ServiceError as e:
        module.fail_json(msg=f"Failed to list services: {e.message}")


if __name__ == "__main__":
    main()
