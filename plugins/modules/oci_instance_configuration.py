# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI instance configurations."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_instance_configuration
short_description: Manage OCI Instance Configurations
description:
    - Create, update, and delete instance configurations in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new instance configuration.
        type: str
    instance_configuration_id:
        description:
            - The OCID of the instance configuration.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the instance configuration.
        type: str
    instance_details:
        description:
            - Instance launch details for the configuration.
        type: dict
    state:
        description:
            - The desired state of the instance configuration.
        type: str
        choices:
            - present
            - absent
        default: present
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a instance configuration
  stevefulme1.oci_cloud.oci_instance_configuration:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-instance-configuration"
    state: present

- name: Delete a instance configuration
  stevefulme1.oci_cloud.oci_instance_configuration:
    instance_configuration_id: "ocid1.instance_configuration.oc1..example"
    state: absent
"""

RETURN = r"""
instance_configuration:
    description: Details of the instance configuration.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.instance_configuration.oc1..example"
        display_name: "my-instance-configuration"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.core import ComputeManagementClient
    from oci.core.models import (
        CreateInstanceConfigurationDetails,
        UpdateInstanceConfigurationDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    """Build module argument spec."""
    module_args = dict(
        compartment_id=dict(type="str"),
        instance_configuration_id=dict(type="str"),
        display_name=dict(type="str"),
        instance_details=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get a instance configuration by OCID."""
    try:
        response = call_with_retry(client.get_instance_configuration, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a instance configuration by display name in a compartment."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_instance_configurations, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if getattr(item, "lifecycle_state", None) in DEAD_STATES:
                continue
            if display_name and getattr(item, "display_name", None) == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    """Create a new instance configuration."""
    params = module.params
    create_details = CreateInstanceConfigurationDetails(
        compartment_id=params.get("compartment_id"),
        display_name=params.get("display_name"),
        instance_details=params.get("instance_details"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_instance_configuration, create_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_instance_configuration, resource.id, target_states=READY_STATES,
        )
    return resource


def update_resource(module, client, existing):
    """Update an existing instance configuration."""
    params = module.params
    update_details = UpdateInstanceConfigurationDetails(
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_instance_configuration, existing.id, update_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_instance_configuration, resource.id, target_states=READY_STATES,
        )
    return resource


def delete_resource(module, client, existing):
    """Delete a instance configuration."""
    call_with_retry(client.delete_instance_configuration, existing.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_instance_configuration, existing.id, target_states=DEAD_STATES,
        )


def needs_update(params, existing):
    """Check if resource attributes differ from desired state."""
    updatable = ["display_name"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ComputeManagementClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("instance_configuration_id"):
        existing = get_resource(client, params["instance_configuration_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("display_name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, instance_configuration=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, instance_configuration=to_dict(resource))
        return

    module.exit_json(changed=False, instance_configuration=to_dict(existing))


if __name__ == "__main__":
    main()
