# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Disaster Recovery Plans."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_disaster_recovery_plan
short_description: Manage Disaster Recovery Plans in OCI
description:
    - Create, update, and delete Disaster Recovery Plans in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.disaster_recovery.DisasterRecoveryClient).
version_added: "2.1.0"
author:
    - Oracle (@oracle)
options:
    dr_plan_id:
        description:
            - The OCID of an existing DR plan.
            - Required for update and delete operations.
        type: str
    dr_protection_group_id:
        description:
            - The OCID of the DR protection group the plan belongs to.
            - Required when creating a new DR plan.
        type: str
    display_name:
        description:
            - The display name of the DR plan.
        type: str
    plan_type:
        description:
            - The type of the DR plan.
        type: str
        choices:
            - SWITCHOVER
            - FAILOVER
    plan_groups:
        description:
            - The list of groups in the DR plan.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the DR plan.
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
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a Disaster Recovery Plan
  stevefulme1.oci_cloud.oci_disaster_recovery_plan:
    dr_protection_group_id: "ocid1.drprotectiongroup.oc1..example"
    display_name: "my-switchover-plan"
    plan_type: "SWITCHOVER"
    state: present

- name: Delete a Disaster Recovery Plan
  stevefulme1.oci_cloud.oci_disaster_recovery_plan:
    dr_plan_id: "ocid1.drplan.oc1..example"
    state: absent
"""

RETURN = r"""
dr_plan:
    description: Details of the DR Plan.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.drplan.oc1..example"
        display_name: "my-switchover-plan"
        lifecycle_state: "ACTIVE"
        type: "SWITCHOVER"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.disaster_recovery import DisasterRecoveryClient
    from oci.disaster_recovery.models import (
        CreateDrPlanDetails,
        UpdateDrPlanDetails,
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
    module_args = dict(
        dr_plan_id=dict(type="str"),
        dr_protection_group_id=dict(type="str"),
        display_name=dict(type="str"),
        plan_type=dict(type="str", choices=["SWITCHOVER", "FAILOVER"]),
        plan_groups=dict(type="list", elements="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_dr_plan, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, dr_protection_group_id, display_name):
    if not dr_protection_group_id:
        return None
    try:
        response = call_with_retry(
            client.list_dr_plans, dr_protection_group_id=dr_protection_group_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateDrPlanDetails(
        dr_protection_group_id=params["dr_protection_group_id"],
        display_name=params.get("display_name"),
        type=params.get("plan_type"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_dr_plan, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_dr_plan, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateDrPlanDetails(
        display_name=params.get("display_name"),
        plan_groups=params.get("plan_groups"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_dr_plan, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_dr_plan, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_dr_plan, existing.id)
    wait_for_resource(
        module, client.get_dr_plan, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
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
        required_if=[
            ("state", "present", ("dr_protection_group_id",), True),
            ("state", "absent", ("dr_plan_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DisasterRecoveryClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("dr_plan_id"):
        existing = get_resource(client, params["dr_plan_id"])
    elif params.get("dr_protection_group_id"):
        existing = find_resource(client, params["dr_protection_group_id"], params.get("display_name"))

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
        module.exit_json(changed=True, dr_plan=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, dr_plan=to_dict(resource))
        return

    module.exit_json(changed=False, dr_plan=to_dict(existing))


if __name__ == "__main__":
    main()
