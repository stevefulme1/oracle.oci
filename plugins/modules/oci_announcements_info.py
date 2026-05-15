# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI announcement information."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_announcements_info
short_description: List OCI platform announcements
description:
    - Retrieve service announcements, maintenance windows, and incidents.
    - This is a read-only module that does not modify any resources.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: List announcements
  stevefulme1.oci_cloud.oci_announcements_info:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result
"""

RETURN = r"""
announcements:
    description: List of announcement details.
    returned: always
    type: list
    elements: dict
"""

try:
    import oci.announcements_service
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


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    module.fail_json(msg="oci_announcements_info module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
