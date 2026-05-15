# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI senders."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_email_sender
short_description: Manage OCI Email senders
description:
    - Create and delete approved email senders.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the sender.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new sender.
        type: str
    sender_id:
        description:
            - The OCID of the sender.
            - Required for update and delete operations.
        type: str
    email_address:
        description:
            - Email Address for the sender.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a sender
  stevefulme1.oci_cloud.oci_email_sender:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a sender
  stevefulme1.oci_cloud.oci_email_sender:
    sender_id: "ocid1.sender.oc1..example"
    state: absent
"""

RETURN = r"""
sender:
    description: Details of the sender.
    returned: on success
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        compartment_id=dict(type="str"),
        sender_id=dict(type="str"),
        email_address=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module.fail_json(msg="oci_email_sender module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
