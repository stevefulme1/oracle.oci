# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI PostgreSQL Database Systems."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_postgresql_db_system
short_description: Manage PostgreSQL Database Systems in OCI
description:
    - Create, update, and delete PostgreSQL Database Systems in Oracle Cloud Infrastructure.
    - OCI Database with PostgreSQL is a fully managed PostgreSQL-compatible database service.
    - This module uses the OCI Python SDK C(oci.psql.PostgresqlClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the PostgreSQL DB System.
            - Required when creating a new PostgreSQL DB System.
        type: str
    db_system_id:
        description:
            - The OCID of an existing PostgreSQL DB System.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the PostgreSQL DB System.
            - Required when creating a new PostgreSQL DB System.
        type: str
    db_version:
        description:
            - The major version of PostgreSQL (e.g. 14, 15, 16).
            - Required when creating a new PostgreSQL DB System.
        type: str
    shape:
        description:
            - The name of the shape for the DB System instances.
            - Required when creating a new PostgreSQL DB System.
        type: str
    instance_count:
        description:
            - Number of instances in the DB System (1 for standalone, more for HA).
            - Required when creating a new PostgreSQL DB System.
        type: int
    storage_details:
        description:
            - Storage details for the PostgreSQL DB System.
            - Required when creating a new PostgreSQL DB System.
        type: dict
    network_details:
        description:
            - Network details for the PostgreSQL DB System.
            - Required when creating a new PostgreSQL DB System.
        type: dict
    credentials:
        description:
            - Initial credentials for the PostgreSQL admin user.
            - Required when creating a new PostgreSQL DB System.
        type: dict
    state:
        description:
            - The desired state of the PostgreSQL DB System.
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
- name: Create a PostgreSQL DB System
  stevefulme1.oci_cloud.oci_postgresql_db_system:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My PostgreSQL DB"
    db_version: "16"
    shape: "PostgreSQL.VM.Standard.E4.Flex.2.32GB"
    instance_count: 1
    storage_details:
      system_type: "OCI_OPTIMIZED_STORAGE"
      is_regionally_durable: true
      availability_domain: "Uocm:US-ASHBURN-AD-1"
    network_details:
      subnet_id: "ocid1.subnet.oc1..example"
    credentials:
      username: "admin"
      password_details:
        password_type: "PLAIN_TEXT"
        password: "ExamplePassword123#"
    state: present

- name: Update a PostgreSQL DB System display name
  stevefulme1.oci_cloud.oci_postgresql_db_system:
    db_system_id: "ocid1.postgresqldbsystem.oc1..example"
    display_name: "Updated PostgreSQL DB"
    state: present

- name: Delete a PostgreSQL DB System
  stevefulme1.oci_cloud.oci_postgresql_db_system:
    db_system_id: "ocid1.postgresqldbsystem.oc1..example"
    state: absent
"""

RETURN = r"""
postgresql_db_system:
    description: Details of the PostgreSQL DB System.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.postgresqldbsystem.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My PostgreSQL DB"
        lifecycle_state: "ACTIVE"
        db_version: "16"
        instance_count: 1
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.psql import PostgresqlClient
    from oci.psql.models import (
        CreateDbSystemDetails,
        UpdateDbSystemDetails,
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
        db_system_id=dict(type="str"),
        display_name=dict(type="str"),
        db_version=dict(type="str"),
        shape=dict(type="str"),
        instance_count=dict(type="int"),
        storage_details=dict(type="dict"),
        network_details=dict(type="dict"),
        credentials=dict(type="dict", no_log=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_postgresql_db_system(client, db_system_id):
    """Get an existing PostgreSQL DB System by OCID."""
    try:
        response = call_with_retry(client.get_db_system, db_system_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_postgresql_db_system(client, compartment_id, display_name):
    """Find a PostgreSQL DB System by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_db_systems,
            compartment_id=compartment_id,
        )
        for dbs in response.data.items:
            if dbs.lifecycle_state in DEAD_STATES:
                continue
            if display_name and dbs.display_name == display_name:
                return get_postgresql_db_system(client, dbs.id)
    except ServiceError:
        pass
    return None


def create_postgresql_db_system(module, client):
    """Create a new PostgreSQL DB System."""
    params = module.params
    create_details = CreateDbSystemDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        db_version=params["db_version"],
        shape=params["shape"],
        instance_count=params["instance_count"],
        storage_details=params["storage_details"],
        network_details=params["network_details"],
        credentials=params.get("credentials"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_db_system, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_db_system,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_postgresql_db_system(module, client, existing):
    """Update an existing PostgreSQL DB System."""
    params = module.params
    update_details = UpdateDbSystemDetails(
        display_name=params.get("display_name"),
        instance_count=params.get("instance_count"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_db_system,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_db_system,
        existing.id,
        target_states=READY_STATES,
    )
    return resource


def delete_postgresql_db_system(module, client, existing):
    """Delete a PostgreSQL DB System."""
    call_with_retry(client.delete_db_system, existing.id)
    wait_for_resource(
        module,
        client.get_db_system,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "instance_count",
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

    client = create_service_client(module, PostgresqlClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("db_system_id"):
        existing = get_postgresql_db_system(client, params["db_system_id"])
    elif params.get("compartment_id"):
        existing = find_postgresql_db_system(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_postgresql_db_system(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "display_name", "db_version", "shape",
                    "instance_count", "storage_details", "network_details"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a PostgreSQL DB System.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_postgresql_db_system(module, client)
        module.exit_json(changed=True, postgresql_db_system=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_postgresql_db_system(module, client, existing)
        module.exit_json(changed=True, postgresql_db_system=to_dict(resource))
        return

    module.exit_json(changed=False, postgresql_db_system=to_dict(existing))


if __name__ == "__main__":
    main()
