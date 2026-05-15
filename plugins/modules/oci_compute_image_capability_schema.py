# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI compute image capability schemas."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_compute_image_capability_schema
short_description: Manage OCI Compute Image Capability Schemas
description:
    - Create, update, and delete compute image capability schemas.
    - Uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    state:
        description:
            - The desired state of the compute image capability schema.
        type: str
        default: present
        choices:
            - present
            - absent
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new compute image capability schema.
        type: str
    compute_image_capability_schema_id:
        description:
            - The OCID of the compute image capability schema.
            - Required for update and delete operations.
        type: str
    compartment_id:
        description:
            - Compartment Id for the compute image capability schema.
        type: str
    compute_global_image_capability_schema_version_name:
        description:
            - Compute Global Image Capability Schema Version Name for the compute image capability schema.
        type: str
    display_name:
        description:
            - Display Name for the compute image capability schema.
        type: str
    image_id:
        description:
            - Image Id for the compute image capability schema.
        type: str
    schema_data:
        description:
            - Schema Data for the compute image capability schema.
        type: str
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a compute image capability schema
  stevefulme1.oci_cloud.oci_compute_image_capability_schema:
    compartment_id: "ocid1.compartment.oc1..example"
    state: present

- name: Delete a compute image capability schema
  stevefulme1.oci_cloud.oci_compute_image_capability_schema:
    compute_image_capability_schema_id: "ocid1.compute_image_capability_schema.oc1..example"
    state: absent
"""

RETURN = r"""
compute_image_capability_schema:
    description: Details of the compute image capability schema.
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
        compute_image_capability_schema_id=dict(type="str"),
        compartment_id=dict(type="str"),
        compute_global_image_capability_schema_version_name=dict(type="str"),
        display_name=dict(type="str"),
        image_id=dict(type="str"),
        schema_data=dict(type="str"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    module.fail_json(msg="oci_compute_image_capability_schema module is a stub. Full implementation requires OCI SDK integration.")


if __name__ == "__main__":
    main()
