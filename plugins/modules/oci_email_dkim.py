# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI dkims."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_email_dkim
short_description: Manage OCI Email DKIM records
description:
    - Create, update, and delete DKIM signing keys for email domains.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the dkim.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new dkim.
        type: str
    dkim_id:
        description:
            - The OCID of the dkim.
            - Required for update and delete operations.
        type: str
    email_domain_id:
        description:
            - Email Domain Id for the dkim.
        type: str
    name:
        description:
            - Name for the dkim.
        type: str
    description:
        description:
            - Description for the dkim.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a dkim
  stevefulme1.oci_cloud.oci_email_dkim:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a dkim
  stevefulme1.oci_cloud.oci_email_dkim:
    dkim_id: "ocid1.dkim.oc1..example"
    state: absent
"""

RETURN = r"""
dkim:
    description: Details of the dkim.
    returned: on success
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        compartment_id=dict(type="str"),
        dkim_id=dict(type="str"),
        email_domain_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module.fail_json(msg="oci_email_dkim module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
