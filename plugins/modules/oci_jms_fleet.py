# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Java Management Service Fleet."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oci_jms_fleet
short_description: Manage a Fleet resource in Oracle Cloud Infrastructure
description:
    - This module allows the user to create, update and delete a Fleet resource in Oracle Cloud Infrastructure
    - For I(state=present), creates a new Fleet.
version_added: "2.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required for create using I(state=present).
        type: str
    display_name:
        description:
            - The name of the Fleet. The name must be unique.
            - Required for create using I(state=present).
            - This parameter is updatable.
        type: str
    description:
        description:
            - The description of the Fleet.
            - This parameter is updatable.
        type: str
    inventory_log:
        description:
            - Inventory log configuration.
        type: dict
    operation_log:
        description:
            - Operation log configuration.
        type: dict
    fleet_id:
        description:
            - The OCID of the Fleet.
            - Required for update using I(state=present).
            - Required for delete using I(state=absent).
        type: str
        aliases: ["id"]
    state:
        description:
            - The state of the Fleet.
            - Use I(state=present) to create or update a Fleet.
            - Use I(state=absent) to delete a Fleet.
        type: str
        required: false
        default: 'present'
        choices: ["present", "absent"]
extends_documentation_fragment: [
    stevefulme1.oci_cloud.oracle,
    stevefulme1.oci_cloud.oracle_creatable_resource,
    stevefulme1.oci_cloud.oracle_wait_options
]
"""

EXAMPLES = """
- name: Create fleet
  oci_jms_fleet:
    compartment_id: "{{ compartment_id }}"
    display_name: "my_fleet"
    description: "Fleet for production Java applications"

- name: Update fleet
  oci_jms_fleet:
    fleet_id: "{{ fleet_id }}"
    display_name: "updated_fleet_name"
    description: "Updated description"

- name: Delete fleet
  oci_jms_fleet:
    fleet_id: "{{ fleet_id }}"
    state: absent
"""

RETURN = """
fleet:
    description:
        - Details of the Fleet resource acted upon by the current operation
    returned: on success
    type: complex
    contains:
        id:
            description:
                - The OCID of the Fleet.
            returned: on success
            type: str
            sample: "ocid1.fleet.oc1..exampleuniqueID"
        compartment_id:
            description:
                - The OCID of the compartment.
            returned: on success
            type: str
            sample: "ocid1.compartment.oc1..exampleuniqueID"
        display_name:
            description:
                - The name of the Fleet.
            returned: on success
            type: str
            sample: my_fleet
        description:
            description:
                - The description of the Fleet.
            returned: on success
            type: str
            sample: Fleet for production Java applications
        time_created:
            description:
                - The creation date and time of the Fleet.
            returned: on success
            type: str
            sample: "2013-10-20T19:20:30+01:00"
        lifecycle_state:
            description:
                - The lifecycle state of the Fleet.
            returned: on success
            type: str
            sample: ACTIVE
    sample: {
        "id": "ocid1.fleet.oc1..exampleuniqueID",
        "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
        "display_name": "my_fleet",
        "description": "Fleet for production Java applications",
        "time_created": "2013-10-20T19:20:30+01:00",
        "lifecycle_state": "ACTIVE"
    }
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.jms import JavaManagementServiceClient
    from oci.jms.models import CreateFleetDetails, UpdateFleetDetails

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    return dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        inventory_log=dict(type="dict"),
        operation_log=dict(type="dict"),
        fleet_id=dict(type="str", aliases=["id"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )


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


def get_resource(client, module):
    try:
        return call_with_retry(client.get_fleet, fleet_id=module.params["fleet_id"])
    except Exception as e:
        if "NotAuthorizedOrNotFound" in str(e) or "404" in str(e):
            return None
        raise


def find_resource(client, module):
    compartment_id = module.params.get("compartment_id")
    display_name = module.params.get("display_name")
    if not compartment_id or not display_name:
        return None
    try:
        fleets = call_with_retry(client.list_fleets, compartment_id=compartment_id).data
        for fleet in fleets:
            if fleet.display_name == display_name and fleet.lifecycle_state not in DEAD_STATES:
                return call_with_retry(client.get_fleet, fleet_id=fleet.id)
    except Exception:
        pass
    return None


def create_resource(client, module):
    create_details = CreateFleetDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        description=module.params.get("description"),
        inventory_log=module.params.get("inventory_log"),
        operation_log=module.params.get("operation_log"),
    )
    result = call_with_retry(client.create_fleet, create_fleet_details=create_details)
    resource = wait_for_resource(client.get_fleet, result.data.id, READY_STATES, module)
    return resource


def update_resource(client, module):
    update_details = UpdateFleetDetails(
        display_name=module.params.get("display_name"),
        description=module.params.get("description"),
    )
    call_with_retry(
        client.update_fleet,
        fleet_id=module.params["fleet_id"],
        update_fleet_details=update_details
    )
    resource = wait_for_resource(client.get_fleet, module.params["fleet_id"], READY_STATES, module)
    return resource


def delete_resource(client, module):
    call_with_retry(client.delete_fleet, fleet_id=module.params["fleet_id"])
    wait_for_resource(client.get_fleet, module.params["fleet_id"], DEAD_STATES, module)


def needs_update(resource, module):
    if module.params.get("display_name") and resource.data.display_name != module.params["display_name"]:
        return True
    if module.params.get("description") is not None and resource.data.description != module.params["description"]:
        return True
    return False


def main():
    module = AnsibleModule(argument_spec=dict(**get_module_args(), **OCI_COMMON_ARGS), supports_check_mode=True)

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg="oci python sdk is required for this module")

    client = create_service_client(module, JavaManagementServiceClient)

    state = module.params["state"]
    fleet_id = module.params.get("fleet_id")

    if fleet_id:
        resource = get_resource(client, module)
    else:
        resource = find_resource(client, module)

    if state == "present":
        if resource:
            if needs_update(resource, module):
                if module.check_mode:
                    module.exit_json(changed=True, fleet=to_dict(resource.data))
                resource = update_resource(client, module)
                module.exit_json(changed=True, fleet=to_dict(resource.data))
            else:
                module.exit_json(changed=False, fleet=to_dict(resource.data))
        else:
            if module.check_mode:
                module.exit_json(changed=True, fleet={})
            resource = create_resource(client, module)
            module.exit_json(changed=True, fleet=to_dict(resource.data))
    elif state == "absent":
        if resource:
            if module.check_mode:
                module.exit_json(changed=True)
            delete_resource(client, module)
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


if __name__ == "__main__":
    main()
