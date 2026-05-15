# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI operations insights warehouses."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_operations_insights
short_description: Manage OCI Operations Insights
description:
    - Enable and manage Operations Insights for capacity planning and performance analysis.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the operations insights warehouse.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new operations insights warehouse.
        type: str
    operations_insights_warehouse_id:
        description:
            - The OCID of the operations insights warehouse.
            - Required for update and delete operations.
        type: str
    compartment_id:
        description:
            - Compartment Id for the operations insights warehouse.
        type: str
    display_name:
        description:
            - Display Name for the operations insights warehouse.
        type: str
    cpu_allocated:
        description:
            - Cpu Allocated for the operations insights warehouse.
        type: str
    storage_allocated_in_gbs:
        description:
            - Storage Allocated In Gbs for the operations insights warehouse.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a operations insights warehouse
  stevefulme1.oci_cloud.oci_operations_insights:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a operations insights warehouse
  stevefulme1.oci_cloud.oci_operations_insights:
    operations_insights_warehouse_id: "ocid1.operations_insights_warehouse.oc1..example"
    state: absent
"""

RETURN = r"""
operations_insights_warehouse:
    description: Details of the operations insights warehouse.
    returned: on success
    type: dict
"""

try:
    import oci.opsi
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
        operations_insights_warehouse_id=dict(type="str"),
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        cpu_allocated=dict(type="str"),
        storage_allocated_in_gbs=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    module.fail_json(msg="oci_operations_insights module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
