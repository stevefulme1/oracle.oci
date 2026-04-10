# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Database backups."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_db_backup
short_description: Manage database backups in OCI
description:
    - Create and delete database backups in Oracle Cloud Infrastructure.
    - Supports both incremental and full backup types.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    database_id:
        description:
            - The OCID of the database to back up.
            - Required when creating a new backup.
        type: str
    backup_id:
        description:
            - The OCID of an existing backup.
            - Required for delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name of the backup.
            - Required when creating a new backup.
        type: str
    type:
        description:
            - The type of backup to create.
        type: str
        choices:
            - INCREMENTAL
            - FULL
        default: INCREMENTAL
    state:
        description:
            - The desired state of the backup.
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
- name: Create a full database backup
  oracle.oci.oci_db_backup:
    database_id: "ocid1.database.oc1..example"
    display_name: "Weekly Full Backup"
    type: FULL
    state: present

- name: Create an incremental database backup
  oracle.oci.oci_db_backup:
    database_id: "ocid1.database.oc1..example"
    display_name: "Daily Incremental Backup"
    type: INCREMENTAL
    state: present

- name: Delete a database backup
  oracle.oci.oci_db_backup:
    backup_id: "ocid1.dbbackup.oc1..example"
    state: absent

- name: Create a backup without waiting for completion
  oracle.oci.oci_db_backup:
    database_id: "ocid1.database.oc1..example"
    display_name: "Async Backup"
    type: FULL
    wait: false
    state: present
"""

RETURN = r"""
db_backup:
    description: Details of the database backup.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dbbackup.oc1..example"
        database_id: "ocid1.database.oc1..example"
        display_name: "Weekly Full Backup"
        lifecycle_state: "ACTIVE"
        type: "FULL"
        time_started: "2024-01-15T10:00:00Z"
        time_ended: "2024-01-15T10:30:00Z"
        database_size_in_gbs: 50
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import CreateBackupDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

# Backup-specific lifecycle states
BACKUP_ACTIVE_STATES = READY_STATES | {"ACTIVE"}
BACKUP_DELETED_STATES = DEAD_STATES | {"DELETED"}


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        database_id=dict(type="str"),
        backup_id=dict(type="str"),
        display_name=dict(type="str"),
        type=dict(
            type="str",
            choices=["INCREMENTAL", "FULL"],
            default="INCREMENTAL",
        ),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    """Convert OCI SDK object to a serializable dict."""
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


def get_backup(client, backup_id):
    """Get an existing backup by OCID."""
    try:
        response = call_with_retry(client.get_backup, backup_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_backup(client, database_id, display_name):
    """Find a backup by database_id and display_name."""
    if not database_id:
        return None
    try:
        response = call_with_retry(
            client.list_backups,
            database_id=database_id,
        )
        for backup in response.data:
            if backup.lifecycle_state in BACKUP_DELETED_STATES:
                continue
            if display_name and backup.display_name == display_name:
                return backup
    except ServiceError:
        pass
    return None


def create_backup(module, client):
    """Create a new database backup."""
    params = module.params

    create_details = CreateBackupDetails(
        database_id=params["database_id"],
        display_name=params["display_name"],
        type=params.get("type"),
    )

    response = call_with_retry(client.create_backup, create_details)
    backup = response.data

    backup = wait_for_resource(
        module,
        client.get_backup,
        backup.id,
        target_states=BACKUP_ACTIVE_STATES,
    )
    return backup


def delete_backup(module, client, existing):
    """Delete a database backup."""
    call_with_retry(client.delete_backup, existing.id)
    wait_for_resource(
        module,
        client.get_backup,
        existing.id,
        target_states=BACKUP_DELETED_STATES,
    )


def main():
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("database_id", "display_name")),
            ("state", "absent", ("backup_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("backup_id"):
        existing = get_backup(client, params["backup_id"])
    elif params.get("database_id") and params.get("display_name"):
        existing = find_backup(client, params["database_id"], params["display_name"])

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_backup(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is not None:
        # Backups are immutable -- if one with the same name exists, return it
        module.exit_json(changed=False, db_backup=to_dict(existing))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    resource = create_backup(module, client)
    module.exit_json(changed=True, db_backup=to_dict(resource))


if __name__ == "__main__":
    main()
