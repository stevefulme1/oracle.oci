# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI dedicated vm hosts."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dedicated_vm_host
short_description: Manage OCI Dedicated Vm Hosts
description:
    - Create, update, and delete dedicated vm hosts in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
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
    display_name:
        description:
            - The display name of the dedicated vm host.
        type: str
    availability_domain:
        description:
            - The availability domain of the dedicated VM host.
        type: str
    dedicated_vm_host_shape:
        description:
            - The dedicated VM host shape.
        type: str
    fault_domain:
        description:
            - The fault domain for the dedicated VM host.
        type: str
    state:
        description:
            - The desired state of the dedicated vm host.
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
- name: Create a dedicated vm host
  stevefulme1.oci_cloud.oci_dedicated_vm_host:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-dedicated-vm-host"
    state: present

- name: Delete a dedicated vm host
  stevefulme1.oci_cloud.oci_dedicated_vm_host:
    dedicated_vm_host_id: "ocid1.dedicated_vm_host.oc1..example"
    state: absent
"""

RETURN = r"""
dedicated_vm_host:
    description: Details of the dedicated vm host.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dedicated_vm_host.oc1..example"
        display_name: "my-dedicated-vm-host"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.core import ComputeClient
    from oci.core.models import (
    CreateDedicatedVmHostDetails,
    UpdateDedicatedVmHostDetails,
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
        dedicated_vm_host_id=dict(type="str"),
        display_name=dict(type="str"),
        availability_domain=dict(type="str"),
        dedicated_vm_host_shape=dict(type="str"),
        fault_domain=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get a dedicated vm host by OCID."""
    try:
        response = call_with_retry(client.get_dedicated_vm_host, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a dedicated vm host by display name in a compartment."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_dedicated_vm_hosts, compartment_id=compartment_id,
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
    """Create a new dedicated vm host."""
    params = module.params
    create_details = CreateDedicatedVmHostDetails(
        compartment_id=params.get("compartment_id"),
        availability_domain=params.get("availability_domain"),
        dedicated_vm_host_shape=params.get("dedicated_vm_host_shape"),
        display_name=params.get("display_name"),
        fault_domain=params.get("fault_domain"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_dedicated_vm_host, create_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_dedicated_vm_host, resource.id, target_states=READY_STATES,
        )
    return resource


def update_resource(module, client, existing):
    """Update an existing dedicated vm host."""
    params = module.params
    update_details = UpdateDedicatedVmHostDetails(
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_dedicated_vm_host, existing.id, update_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_dedicated_vm_host, resource.id, target_states=READY_STATES,
        )
    return resource


def delete_resource(module, client, existing):
    """Delete a dedicated vm host."""
    call_with_retry(client.delete_dedicated_vm_host, existing.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_dedicated_vm_host, existing.id, target_states=DEAD_STATES,
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

    client = create_service_client(module, ComputeClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("dedicated_vm_host_id"):
        existing = get_resource(client, params["dedicated_vm_host_id"])
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
        module.exit_json(changed=True, dedicated_vm_host=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, dedicated_vm_host=to_dict(resource))
        return

    module.exit_json(changed=False, dedicated_vm_host=to_dict(existing))


if __name__ == "__main__":
    main()
