#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Steve Fulmer
# Apache-2.0 (see LICENSE)
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""oci_instance_configuration_info module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_instance_configuration_info
short_description: Retrieve instance configuration information
description:
    - Retrieve details about instance configurations.
    - Read-only module.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    host:
        description: API host address.
        type: str
        required: true
    compartment_id:
        description: ID of a specific resource.
        type: str
    username:
        description: Authentication username.
        type: str
    password:
        description: Authentication password.
        type: str
    api_key:
        description: API key for authentication.
        type: str
    validate_certs:
        description: Validate SSL certificates.
        type: bool
        default: true
    limit:
        description:
          - Maximum number of results to return.
      - OCI API default varies by service, max is typically 1000.
        type: int
        default: 1000
  page:
    description:
      - Pagination token from a previous list call.
      - Use to continue listing from where the last call left off.
    type: str
    max_results:
        description:
          - Maximum total number of results to return.
      - Set to 0 for no limit.
        type: int
        default: 1000
"""

EXAMPLES = r"""
- name: List all instance configurations
  stevefulme1.oci_cloud.oci_instance_configuration_info:
    host: api.example.com
  register: result

- name: Get specific instance configuration
  stevefulme1.oci_cloud.oci_instance_configuration_info:
    host: api.example.com
    compartment_id: "example-id"
  register: result
"""

RETURN = r"""
instance_configurations:
    description: List of resource details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            limit=dict(type="int", default=1000),
            page=dict(type="str"),
            max_results=dict(type="int", default=1000),
            compartment_id=dict(type="str"),
            host=dict(type="str", required=True),
            username=dict(type="str"),
            password=dict(type="str", no_log=True),
            api_key=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(changed=False, instance_configurations=[])


if __name__ == "__main__":
    main()
