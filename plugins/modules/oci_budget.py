# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Budgets."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_budget
short_description: Manage Budgets in OCI
description:
    - Create, update, and delete Budgets in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.budget.BudgetClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment (tenancy) for the budget.
            - Required when creating a new budget.
        type: str
    budget_id:
        description:
            - The OCID of an existing budget.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the budget.
            - Required when creating a new budget.
        type: str
    amount:
        description:
            - The amount for the budget.
            - Required when creating a new budget.
        type: float
    reset_period:
        description:
            - The reset period for the budget.
        type: str
        choices:
            - MONTHLY
        default: MONTHLY
    target_type:
        description:
            - The type of target for the budget.
        type: str
        choices:
            - COMPARTMENT
            - TAG
    targets:
        description:
            - The list of targets for the budget.
        type: list
        elements: str
    description:
        description:
            - A description of the budget.
        type: str
    state:
        description:
            - The desired state of the budget.
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
- name: Create a budget
  oracle.oci.oci_budget:
    compartment_id: "ocid1.tenancy.oc1..example"
    display_name: "monthly-budget"
    amount: 1000.0
    reset_period: MONTHLY
    target_type: COMPARTMENT
    targets:
      - "ocid1.compartment.oc1..example"
    state: present

- name: Delete a budget
  oracle.oci.oci_budget:
    budget_id: "ocid1.budget.oc1..example"
    state: absent
"""

RETURN = r"""
budget:
    description: Details of the budget.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.budget.oc1..example"
        display_name: "monthly-budget"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.budget import BudgetClient
    from oci.budget.models import (
        CreateBudgetDetails,
        UpdateBudgetDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        budget_id=dict(type="str"),
        display_name=dict(type="str"),
        amount=dict(type="float"),
        reset_period=dict(type="str", choices=["MONTHLY"], default="MONTHLY"),
        target_type=dict(type="str", choices=["COMPARTMENT", "TAG"]),
        targets=dict(type="list", elements="str"),
        description=dict(type="str"),
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


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_budget, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_budgets, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateBudgetDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        amount=params["amount"],
        reset_period=params.get("reset_period"),
        target_type=params.get("target_type"),
        targets=params.get("targets"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_budget, create_details)
    return response.data


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateBudgetDetails(
        display_name=params.get("display_name"),
        amount=params.get("amount"),
        reset_period=params.get("reset_period"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_budget, existing.id, update_details)
    return response.data


def delete_resource(module, client, existing):
    call_with_retry(client.delete_budget, existing.id)


def needs_update(params, existing):
    updatable = ["display_name", "amount", "reset_period", "description"]
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
            ("state", "present", ("compartment_id", "display_name", "amount"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, BudgetClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("budget_id"):
        existing = get_resource(client, params["budget_id"])
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
        for req in ("compartment_id", "display_name", "amount"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a budget.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, budget=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, budget=to_dict(resource))
        return

    module.exit_json(changed=False, budget=to_dict(existing))


if __name__ == "__main__":
    main()
