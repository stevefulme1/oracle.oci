# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI availability domain information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_availability_domain_info
short_description: List OCI availability domains
description:
    - Retrieve information about availability domains in a compartment.
    - This is a read-only module that does not modify any resources.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
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
"""

EXAMPLES = r    limit:
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
"""
- name: List availability domains
  stevefulme1.oci_cloud.oci_availability_domain_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result
"""

RETURN = r"""
availability_domains:
    description: List of availability domain details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        limit=dict(type="int", default=1000),
        page=dict(type="str"),
        max_results=dict(type="int", default=1000),
        compartment_id=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module.fail_json(
        msg="oci_availability_domain_info module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
