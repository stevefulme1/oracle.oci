# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Database Migration Service migrations."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_database_migration
short_description: Manage Database Migrations in OCI
description:
    - Create, update, and delete Database Migrations in Oracle Cloud Infrastructure.
    - OCI Database Migration Service (DMS) provides a managed cloud service for
      migrating databases to Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.database_migration.DatabaseMigrationClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the migration.
            - Required when creating a new migration.
        type: str
    migration_id:
        description:
            - The OCID of an existing migration.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the migration.
        type: str
    type:
        description:
            - The type of the migration (ONLINE or OFFLINE).
            - Required when creating a new migration.
        type: str
        choices:
            - ONLINE
            - OFFLINE
    source_database_connection_id:
        description:
            - The OCID of the source database connection.
            - Required when creating a new migration.
        type: str
    target_database_connection_id:
        description:
            - The OCID of the target database connection.
            - Required when creating a new migration.
        type: str
    state:
        description:
            - The desired state of the migration.
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
- name: Create an online database migration
  stevefulme1.oci_cloud.oci_database_migration:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My Online Migration"
    type: ONLINE
    source_database_connection_id: "ocid1.databaseconnection.oc1..source"
    target_database_connection_id: "ocid1.databaseconnection.oc1..target"
    state: present

- name: Create an offline database migration
  stevefulme1.oci_cloud.oci_database_migration:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My Offline Migration"
    type: OFFLINE
    source_database_connection_id: "ocid1.databaseconnection.oc1..source"
    target_database_connection_id: "ocid1.databaseconnection.oc1..target"
    state: present

- name: Update a migration display name
  stevefulme1.oci_cloud.oci_database_migration:
    migration_id: "ocid1.odmsmigration.oc1..example"
    display_name: "Updated Migration"
    state: present

- name: Delete a migration
  stevefulme1.oci_cloud.oci_database_migration:
    migration_id: "ocid1.odmsmigration.oc1..example"
    state: absent
"""

RETURN = r"""
database_migration:
    description: Details of the Database Migration.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.odmsmigration.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My Online Migration"
        lifecycle_state: "ACTIVE"
        type: "ONLINE"
        source_database_connection_id: "ocid1.databaseconnection.oc1..source"
        target_database_connection_id: "ocid1.databaseconnection.oc1..target"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database_migration import DatabaseMigrationClient
    from oci.database_migration.models import (
        CreateMigrationDetails,
        UpdateMigrationDetails,
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
        migration_id=dict(type="str"),
        display_name=dict(type="str"),
        type=dict(type="str", choices=["ONLINE", "OFFLINE"]),
        source_database_connection_id=dict(type="str"),
        target_database_connection_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_migration(client, migration_id):
    """Get an existing migration by OCID."""
    try:
        response = call_with_retry(client.get_migration, migration_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_migration(client, compartment_id, display_name):
    """Find a migration by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_migrations,
            compartment_id=compartment_id,
        )
        for mig in response.data.items:
            if mig.lifecycle_state in DEAD_STATES:
                continue
            if display_name and mig.display_name == display_name:
                return get_migration(client, mig.id)
    except ServiceError:
        pass
    return None


def create_migration(module, client):
    """Create a new migration."""
    params = module.params
    create_details = CreateMigrationDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        type=params["type"],
        source_database_connection_id=params["source_database_connection_id"],
        target_database_connection_id=params["target_database_connection_id"],
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_migration, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_migration,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_migration(module, client, existing):
    """Update an existing migration."""
    params = module.params
    update_details = UpdateMigrationDetails(
        display_name=params.get("display_name"),
        type=params.get("type"),
        source_database_connection_id=params.get("source_database_connection_id"),
        target_database_connection_id=params.get("target_database_connection_id"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_migration,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_migration,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_migration(module, client, existing):
    """Delete a migration."""
    call_with_retry(client.delete_migration, existing.id)
    wait_for_resource(
        module,
        client.get_migration,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "type",
        "source_database_connection_id",
        "target_database_connection_id",
    ]
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

    client = create_service_client(module, DatabaseMigrationClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("migration_id"):
        existing = get_migration(client, params["migration_id"])
    elif params.get("compartment_id"):
        existing = find_migration(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_migration(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "type", "source_database_connection_id",
                    "target_database_connection_id"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a migration.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_migration(module, client)
        module.exit_json(changed=True, database_migration=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_migration(module, client, existing)
        module.exit_json(changed=True, database_migration=to_dict(resource))
        return

    module.exit_json(changed=False, database_migration=to_dict(existing))


if __name__ == "__main__":
    main()
