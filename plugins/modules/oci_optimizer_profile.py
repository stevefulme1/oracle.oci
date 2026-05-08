# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Optimizer Profile."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oci_optimizer_profile
short_description: Manage an Optimizer Profile resource in Oracle Cloud Infrastructure
description:
    - This module allows the user to create, update and delete an Optimizer Profile resource in OCI
    - For I(state=present), creates a new Optimizer Profile.
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
            - The display name of the Optimizer Profile.
            - This parameter is updatable.
        type: str
    description:
        description:
            - The description of the Optimizer Profile.
            - This parameter is updatable.
        type: str
    levels_configuration:
        description:
            - The configuration for recommendation levels.
        type: dict
    target_compartments:
        description:
            - The target compartments configuration.
        type: dict
    target_tags:
        description:
            - The target tags configuration.
        type: dict
    profile_id:
        description:
            - The OCID of the Optimizer Profile.
            - Required for update using I(state=present).
            - Required for delete using I(state=absent).
        type: str
        aliases: ["id"]
    state:
        description:
            - The state of the Optimizer Profile.
            - Use I(state=present) to create or update an Optimizer Profile.
            - Use I(state=absent) to delete an Optimizer Profile.
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
- name: Create optimizer profile
  oci_optimizer_profile:
    compartment_id: "{{ compartment_id }}"
    display_name: "My Optimizer Profile"
    description: "Profile for cost optimization"

- name: Update optimizer profile
  oci_optimizer_profile:
    profile_id: "{{ profile_id }}"
    display_name: "Updated Optimizer Profile"
    description: "Updated description"

- name: Delete optimizer profile
  oci_optimizer_profile:
    profile_id: "{{ profile_id }}"
    state: absent
"""

RETURN = """
profile:
    description:
        - Details of the Optimizer Profile resource acted upon by the current operation
    returned: on success
    type: complex
    contains:
        id:
            description:
                - The OCID of the Optimizer Profile.
            returned: on success
            type: str
            sample: "ocid1.profile.oc1..exampleuniqueID"
        compartment_id:
            description:
                - The OCID of the compartment.
            returned: on success
            type: str
            sample: "ocid1.compartment.oc1..exampleuniqueID"
        display_name:
            description:
                - The display name of the Optimizer Profile.
            returned: on success
            type: str
            sample: My Optimizer Profile
        description:
            description:
                - The description of the Optimizer Profile.
            returned: on success
            type: str
            sample: Profile for cost optimization
        time_created:
            description:
                - The creation date and time of the Optimizer Profile.
            returned: on success
            type: str
            sample: "2013-10-20T19:20:30+01:00"
        lifecycle_state:
            description:
                - The lifecycle state of the Optimizer Profile.
            returned: on success
            type: str
            sample: ACTIVE
    sample: {
        "id": "ocid1.profile.oc1..exampleuniqueID",
        "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
        "display_name": "My Optimizer Profile",
        "description": "Profile for cost optimization",
        "time_created": "2013-10-20T19:20:30+01:00",
        "lifecycle_state": "ACTIVE"
    }
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.optimizer import OptimizerClient
    from oci.optimizer.models import CreateProfileDetails, UpdateProfileDetails

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
        levels_configuration=dict(type="dict"),
        target_compartments=dict(type="dict"),
        target_tags=dict(type="dict"),
        profile_id=dict(type="str", aliases=["id"]),
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
        return call_with_retry(client.get_profile, profile_id=module.params["profile_id"])
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
        profiles = call_with_retry(client.list_profiles, compartment_id=compartment_id).data
        for profile in profiles:
            if profile.display_name == display_name and profile.lifecycle_state not in DEAD_STATES:
                return call_with_retry(client.get_profile, profile_id=profile.id)
    except Exception:
        pass
    return None


def create_resource(client, module):
    create_details = CreateProfileDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params.get("display_name"),
        description=module.params.get("description"),
        levels_configuration=module.params.get("levels_configuration"),
        target_compartments=module.params.get("target_compartments"),
        target_tags=module.params.get("target_tags"),
    )
    result = call_with_retry(client.create_profile, create_profile_details=create_details)
    resource = wait_for_resource(client.get_profile, result.data.id, READY_STATES, module)
    return resource


def update_resource(client, module):
    update_details = UpdateProfileDetails(
        display_name=module.params.get("display_name"),
        description=module.params.get("description"),
    )
    call_with_retry(
        client.update_profile,
        profile_id=module.params["profile_id"],
        update_profile_details=update_details
    )
    resource = wait_for_resource(client.get_profile, module.params["profile_id"], READY_STATES, module)
    return resource


def delete_resource(client, module):
    call_with_retry(client.delete_profile, profile_id=module.params["profile_id"])
    wait_for_resource(client.get_profile, module.params["profile_id"], DEAD_STATES, module)


def needs_update(resource, module):
    if (module.params.get("display_name") and
            resource.data.display_name != module.params["display_name"]):
        return True
    if (module.params.get("description") is not None and
            resource.data.description != module.params["description"]):
        return True
    return False


def main():
    module = AnsibleModule(argument_spec=dict(**get_module_args(), **OCI_COMMON_ARGS), supports_check_mode=True)

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg="oci python sdk is required for this module")

    client = create_service_client(module, OptimizerClient)

    state = module.params["state"]
    profile_id = module.params.get("profile_id")

    if profile_id:
        resource = get_resource(client, module)
    else:
        resource = find_resource(client, module)

    if state == "present":
        if resource:
            if needs_update(resource, module):
                if module.check_mode:
                    module.exit_json(changed=True, profile=to_dict(resource.data))
                resource = update_resource(client, module)
                module.exit_json(changed=True, profile=to_dict(resource.data))
            else:
                module.exit_json(changed=False, profile=to_dict(resource.data))
        else:
            if module.check_mode:
                module.exit_json(changed=True, profile={})
            resource = create_resource(client, module)
            module.exit_json(changed=True, profile=to_dict(resource.data))
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
