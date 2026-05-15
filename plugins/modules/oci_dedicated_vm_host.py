# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI dedicated vm hosts."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dedicated_vm_host
short_description: Manage OCI Dedicated Virtual Machine Hosts
description:
    - Create, update, and delete dedicated VM hosts for isolated compute workloads.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the dedicated vm host.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new dedicated vm host.
        type: str
    dedicated_vm_host_id:
        description:
            - The OCID of the dedicated vm host.
            - Required for update and delete operations.
        type: str
    compartment_id:
        description:
            - Compartment Id for the dedicated vm host.
        type: str
    availability_domain:
        description:
            - Availability Domain for the dedicated vm host.
        type: str
    dedicated_vm_host_shape:
        description:
            - Dedicated Vm Host Shape for the dedicated vm host.
        type: str
    display_name:
        description:
            - Display Name for the dedicated vm host.
        type: str
    fault_domain:
        description:
            - Fault Domain for the dedicated vm host.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a dedicated vm host
  stevefulme1.oci_cloud.oci_dedicated_vm_host:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a dedicated vm host
  stevefulme1.oci_cloud.oci_dedicated_vm_host:
    dedicated_vm_host_id: "ocid1.dedicated_vm_host.oc1..example"
    state: absent
"""

RETURN = r"""
dedicated_vm_host:
    description: Details of the dedicated vm host.
    returned: on success
    type: dict
"""

try:
    import oci.core
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
        state=dict(type="str", default="present", choices=["present", "absent"]),
        compartment_id=dict(type="str"),
        dedicated_vm_host_id=dict(type="str"),
        compartment_id=dict(type="str"),
        availability_domain=dict(type="str"),
        dedicated_vm_host_shape=dict(type="str"),
        display_name=dict(type="str"),
        fault_domain=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    module.fail_json(msg="oci_dedicated_vm_host module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
