#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Steve Fulmer
# Apache-2.0 (see LICENSE)
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""oci_ai_document_processor_job_info module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_document_processor_job_info
short_description: Retrieve ai document processor job information
description:
    - Retrieve details about ai document processor jobs.
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
"""

EXAMPLES = r"""
- name: List all ai document processor jobs
  stevefulme1.oci_cloud.oci_ai_document_processor_job_info:
    host: api.example.com
  register: result

- name: Get specific ai document processor job
  stevefulme1.oci_cloud.oci_ai_document_processor_job_info:
    host: api.example.com
    compartment_id: "example-id"
  register: result
"""

RETURN = r"""
ai_document_processor_jobs:
    description: List of resource details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            compartment_id=dict(type="str"),
            host=dict(type="str", required=True),
            username=dict(type="str"),
            password=dict(type="str", no_log=True),
            api_key=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(changed=False, ai_document_processor_jobs=[])


if __name__ == "__main__":
    main()
