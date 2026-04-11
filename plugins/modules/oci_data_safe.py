# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Data Safe configuration."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_data_safe
short_description: Manage Data Safe configuration in OCI
description:
    - Enable or disable Data Safe in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.data_safe.DataSafeClient).
    - Simple enable/disable resource.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment for Data Safe configuration.
            - Required.
        type: str
        required: true
    is_enabled:
        description:
            - Whether Data Safe should be enabled.
        type: bool
        default: true
    state:
        description:
            - The desired state of Data Safe.
        type: str
        choices:
            - present
            - absent
        default: present
    wait:
        description:
            - Whether to wait for the resource to reach the desired state.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach the desired state.
        type: int
        default: 1200
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Enable Data Safe
  oracle.oci.oci_data_safe:
    compartment_id: "ocid1.compartment.oc1..example"
    is_enabled: true
    state: present

- name: Disable Data Safe
  oracle.oci.oci_data_safe:
    compartment_id: "ocid1.compartment.oc1..example"
    is_enabled: false
    state: present
"""

RETURN = r"""
data_safe_configuration:
    description: Details of the Data Safe configuration.
    returned: On success.
    type: dict
    sample:
        is_enabled: true
        compartment_id: "ocid1.compartment.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.data_safe import DataSafeClient
    from oci.data_safe.models import EnableDataSafeConfigurationDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str", required=True),
        is_enabled=dict(type="bool", default=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return resource


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DataSafeClient)
    params = module.params
    compartment_id = params["compartment_id"]

    # Get current configuration
    try:
        response = call_with_retry(
            client.get_data_safe_configuration, compartment_id=compartment_id,
        )
        current = response.data
    except ServiceError:
        current = None

    desired_enabled = params.get("is_enabled", True)
    if params["state"] == "absent":
        desired_enabled = False

    current_enabled = getattr(current, "is_enabled", False) if current else False

    if current_enabled == desired_enabled:
        module.exit_json(changed=False, data_safe_configuration=to_dict(current))
        return

    if module.check_mode:
        module.exit_json(changed=True)
        return

    enable_details = EnableDataSafeConfigurationDetails(
        is_enabled=desired_enabled,
        compartment_id=compartment_id,
    )
    call_with_retry(client.enable_data_safe_configuration, enable_details)

    # Re-fetch the configuration
    response = call_with_retry(
        client.get_data_safe_configuration, compartment_id=compartment_id,
    )
    module.exit_json(changed=True, data_safe_configuration=to_dict(response.data))


if __name__ == "__main__":
    main()
