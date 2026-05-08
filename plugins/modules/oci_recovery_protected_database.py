# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Database Recovery Protected Databases."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_recovery_protected_database
short_description: Manage Database Recovery Protected Databases in OCI
description:
    - Create, update, and delete Database Recovery Protected Databases in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.recovery.DatabaseRecoveryClient).
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the protected database.
            - Required when creating a new protected database.
        type: str
    protected_database_id:
        description:
            - The OCID of an existing protected database.
            - Required for update and delete operations.
        type: str
    db_unique_name:
        description:
            - The unique name of the database.
            - Required when creating a new protected database.
        type: str
    database_size:
        description:
            - The size category of the database.
            - Required when creating a new protected database.
        type: str
        choices:
            - XS
            - S
            - M
            - L
            - XL
            - XXL
            - AUTO
    protection_policy_id:
        description:
            - The OCID of the protection policy to apply.
            - Required when creating a new protected database.
        type: str
    display_name:
        description:
            - The display name of the protected database.
        type: str
    password:
        description:
            - The password for the protected database.
        type: str
    recovery_service_subnets:
        description:
            - A list of recovery service subnets associated with the protected database.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the protected database.
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
- name: Create a protected database
  stevefulme1.oci_cloud.oci_recovery_protected_database:
    compartment_id: "ocid1.compartment.oc1..example"
    db_unique_name: "mydb_unique"
    database_size: "M"
    protection_policy_id: "ocid1.protectionpolicy.oc1..example"
    display_name: "my-protected-db"
    state: present

- name: Delete a protected database
  stevefulme1.oci_cloud.oci_recovery_protected_database:
    protected_database_id: "ocid1.protecteddatabase.oc1..example"
    state: absent
"""

RETURN = r"""
protected_database:
    description: Details of the protected database.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.protecteddatabase.oc1..example"
        display_name: "my-protected-db"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.recovery import DatabaseRecoveryClient
    from oci.recovery.models import (
        CreateProtectedDatabaseDetails,
        UpdateProtectedDatabaseDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

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
    module_args = dict(
        compartment_id=dict(type="str"),
        protected_database_id=dict(type="str"),
        db_unique_name=dict(type="str"),
        database_size=dict(type="str", choices=["XS", "S", "M", "L", "XL", "XXL", "AUTO"]),
        protection_policy_id=dict(type="str"),
        display_name=dict(type="str"),
        password=dict(type="str", no_log=True),
        recovery_service_subnets=dict(type="list", elements="dict"),
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
        response = call_with_retry(client.get_protected_database, resource_id)
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
            client.list_protected_databases, compartment_id=compartment_id,
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
    create_details = CreateProtectedDatabaseDetails(
        compartment_id=params["compartment_id"],
        db_unique_name=params["db_unique_name"],
        database_size=params["database_size"],
        protection_policy_id=params["protection_policy_id"],
        display_name=params.get("display_name"),
        password=params.get("password"),
        recovery_service_subnets=params.get("recovery_service_subnets"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_protected_database, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_protected_database, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateProtectedDatabaseDetails(
        display_name=params.get("display_name"),
        database_size=params.get("database_size"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_protected_database, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_protected_database, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_protected_database, existing.id)
    wait_for_resource(
        module, client.get_protected_database, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "database_size"]
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
            ("state", "present", ("compartment_id", "db_unique_name", "database_size", "protection_policy_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseRecoveryClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("protected_database_id"):
        existing = get_resource(client, params["protected_database_id"])
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
        for req in ("compartment_id", "db_unique_name", "database_size", "protection_policy_id"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a protected database.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, protected_database=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, protected_database=to_dict(resource))
        return

    module.exit_json(changed=False, protected_database=to_dict(existing))


if __name__ == "__main__":
    main()
