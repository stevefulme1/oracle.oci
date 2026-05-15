# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI resolvers."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dns_resolver
short_description: Manage OCI DNS resolvers
description:
    - Create, update, and delete DNS resolvers.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the resolver.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new resolver.
        type: str
    resolver_id:
        description:
            - The OCID of the resolver.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - Display Name for the resolver.
        type: str
    attached_vcn_id:
        description:
            - Attached Vcn Id for the resolver.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a resolver
  stevefulme1.oci_cloud.oci_dns_resolver:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a resolver
  stevefulme1.oci_cloud.oci_dns_resolver:
    resolver_id: "ocid1.resolver.oc1..example"
    state: absent
"""

RETURN = r"""
resolver:
    description: Details of the resolver.
    returned: on success
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        compartment_id=dict(type="str"),
        resolver_id=dict(type="str"),
        display_name=dict(type="str"),
        attached_vcn_id=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module.fail_json(msg="oci_dns_resolver module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
