# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Database Homes."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_db_home
short_description: Manage Database Homes in OCI
description:
    - Create, update, and delete Database Homes in Oracle Cloud Infrastructure.
    - A Database Home is a directory where Oracle Database software is installed.
      It is associated with a DB System or VM Cluster.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the Database Home.
        type: str
    db_home_id:
        description:
            - The OCID of an existing Database Home.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the Database Home.
        type: str
    db_system_id:
        description:
            - The OCID of the DB System to create the Database Home in.
            - One of I(db_system_id) or I(vm_cluster_id) is required for create.
        type: str
    vm_cluster_id:
        description:
            - The OCID of the VM Cluster to create the Database Home in.
            - One of I(db_system_id) or I(vm_cluster_id) is required for create.
        type: str
    db_version:
        description:
            - The Oracle Database version (e.g. 19.0.0.0, 21.0.0.0).
            - Required when creating a new Database Home.
        type: str
    source:
        description:
            - The source of the Database Home.
        type: str
        choices:
            - NONE
            - DB_BACKUP
            - VM_CLUSTER_NEW
        default: NONE
    database:
        description:
            - Database configuration for the Database Home.
            - Required when creating a new Database Home.
        type: dict
        suboptions:
            admin_password:
                description:
                    - The password for the SYS, SYSTEM, and PDB admin accounts.
                type: str
                required: true
            db_name:
                description:
                    - The name of the database.
                type: str
                required: true
    state:
        description:
            - The desired state of the Database Home.
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
- name: Create a Database Home on a DB System
  stevefulme1.oci_cloud.oci_db_home:
    db_system_id: "ocid1.dbsystem.oc1..example"
    display_name: "My DB Home"
    db_version: "19.0.0.0"
    database:
      db_name: "mydb"
      admin_password: "ExamplePassword123#"
    state: present

- name: Create a Database Home on a VM Cluster
  stevefulme1.oci_cloud.oci_db_home:
    vm_cluster_id: "ocid1.vmcluster.oc1..example"
    display_name: "My VM DB Home"
    db_version: "19.0.0.0"
    source: VM_CLUSTER_NEW
    database:
      db_name: "vmdb"
      admin_password: "ExamplePassword123#"
    state: present

- name: Update a Database Home display name
  stevefulme1.oci_cloud.oci_db_home:
    db_home_id: "ocid1.dbhome.oc1..example"
    display_name: "Updated DB Home"
    state: present

- name: Delete a Database Home
  stevefulme1.oci_cloud.oci_db_home:
    db_home_id: "ocid1.dbhome.oc1..example"
    state: absent
"""

RETURN = r"""
db_home:
    description: Details of the Database Home.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dbhome.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My DB Home"
        lifecycle_state: "AVAILABLE"
        db_version: "19.0.0.0"
        db_system_id: "ocid1.dbsystem.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateDbHomeDetails,
        CreateDatabaseDetails,
        UpdateDbHomeDetails,
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
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        db_home_id=dict(type="str"),
        display_name=dict(type="str"),
        db_system_id=dict(type="str"),
        vm_cluster_id=dict(type="str"),
        db_version=dict(type="str"),
        source=dict(
            type="str",
            choices=["NONE", "DB_BACKUP", "VM_CLUSTER_NEW"],
            default="NONE",
        ),
        database=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_db_home(client, db_home_id):
    """Get an existing Database Home by OCID."""
    try:
        response = call_with_retry(client.get_db_home, db_home_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_db_home(client, compartment_id, db_system_id, vm_cluster_id, display_name):
    """Find a Database Home by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        kwargs = dict(compartment_id=compartment_id)
        if db_system_id:
            kwargs["db_system_id"] = db_system_id
        if vm_cluster_id:
            kwargs["vm_cluster_id"] = vm_cluster_id
        response = call_with_retry(client.list_db_homes, **kwargs)
        for dbh in response.data:
            if dbh.lifecycle_state in DEAD_STATES:
                continue
            if display_name and dbh.display_name == display_name:
                return dbh
    except ServiceError:
        pass
    return None


def create_db_home(module, client):
    """Create a new Database Home."""
    params = module.params
    db_params = params.get("database", {})

    database_details = CreateDatabaseDetails(
        db_name=db_params["db_name"],
        admin_password=db_params["admin_password"],
    )

    create_details = CreateDbHomeDetails(
        display_name=params.get("display_name"),
        db_system_id=params.get("db_system_id"),
        vm_cluster_id=params.get("vm_cluster_id"),
        db_version=params["db_version"],
        source=params.get("source", "NONE"),
        database=database_details,
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_db_home, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_db_home,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_db_home(module, client, existing):
    """Update an existing Database Home."""
    params = module.params
    update_details = UpdateDbHomeDetails(
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_db_home,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_db_home,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_db_home(module, client, existing):
    """Delete a Database Home."""
    call_with_retry(client.delete_db_home, existing.id)
    wait_for_resource(
        module,
        client.get_db_home,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
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
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("db_home_id"):
        existing = get_db_home(client, params["db_home_id"])
    elif params.get("compartment_id"):
        existing = find_db_home(
            client,
            params["compartment_id"],
            params.get("db_system_id"),
            params.get("vm_cluster_id"),
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_db_home(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        if not params.get("db_system_id") and not params.get("vm_cluster_id"):
            module.fail_json(msg="One of 'db_system_id' or 'vm_cluster_id' is required to create a Database Home.")
        for req in ("db_version", "database"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a Database Home.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_db_home(module, client)
        module.exit_json(changed=True, db_home=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_db_home(module, client, existing)
        module.exit_json(changed=True, db_home=to_dict(resource))
        return

    module.exit_json(changed=False, db_home=to_dict(existing))


if __name__ == "__main__":
    main()
