# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Autonomous Databases."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_autonomous_database
short_description: Manage Autonomous Databases in OCI
description:
    - Create, update, and delete Autonomous Databases in Oracle Cloud Infrastructure.
    - Supports Autonomous Transaction Processing (ATP), Autonomous Data Warehouse (ADW),
      Autonomous JSON Database (AJD), and APEX Application Development.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the Autonomous Database.
            - Required when creating a new Autonomous Database.
        type: str
    autonomous_database_id:
        description:
            - The OCID of an existing Autonomous Database.
            - Required for update and delete operations.
        type: str
    db_name:
        description:
            - The database name. Must begin with a letter and contain only alphanumeric characters.
            - Required when creating a new Autonomous Database.
        type: str
    display_name:
        description:
            - The user-friendly name for the Autonomous Database.
        type: str
    admin_password:
        description:
            - The password for the ADMIN user.
            - Required when creating a new Autonomous Database.
        type: str
        no_log: true
    cpu_core_count:
        description:
            - The number of OCPU cores to be made available to the database.
            - Required when creating a new Autonomous Database (unless I(is_free_tier) is true).
        type: int
    data_storage_size_in_tbs:
        description:
            - The size, in terabytes, of the data volume to attach to the database.
            - Required when creating a new Autonomous Database (unless I(is_free_tier) is true).
        type: int
    db_workload:
        description:
            - The Autonomous Database workload type.
        type: str
        choices:
            - OLTP
            - DW
            - AJD
            - APEX
        default: OLTP
    is_free_tier:
        description:
            - Whether this is an Always Free resource.
        type: bool
        default: false
    is_auto_scaling_enabled:
        description:
            - Whether auto scaling is enabled for the Autonomous Database OCPU core count.
        type: bool
        default: false
    state:
        description:
            - The desired state of the Autonomous Database.
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
- name: Create an Autonomous Database (ATP)
  oracle.oci.oci_autonomous_database:
    compartment_id: "ocid1.compartment.oc1..example"
    db_name: "myatpdb"
    display_name: "My ATP Database"
    admin_password: "ExamplePassword123#"
    cpu_core_count: 1
    data_storage_size_in_tbs: 1
    db_workload: OLTP
    is_auto_scaling_enabled: true
    state: present

- name: Create a free-tier Autonomous Data Warehouse
  oracle.oci.oci_autonomous_database:
    compartment_id: "ocid1.compartment.oc1..example"
    db_name: "freedw"
    display_name: "Free ADW"
    admin_password: "ExamplePassword123#"
    db_workload: DW
    is_free_tier: true
    state: present

- name: Update an Autonomous Database display name and scaling
  oracle.oci.oci_autonomous_database:
    compartment_id: "ocid1.compartment.oc1..example"
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..example"
    display_name: "Updated ATP Database"
    cpu_core_count: 2
    is_auto_scaling_enabled: true
    state: present

- name: Delete an Autonomous Database
  oracle.oci.oci_autonomous_database:
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..example"
    state: absent
"""

RETURN = r"""
autonomous_database:
    description: Details of the Autonomous Database.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.autonomousdatabase.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        db_name: "myatpdb"
        display_name: "My ATP Database"
        lifecycle_state: "AVAILABLE"
        cpu_core_count: 1
        data_storage_size_in_tbs: 1
        db_workload: "OLTP"
        is_free_tier: false
        is_auto_scaling_enabled: true
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateAutonomousDatabaseDetails,
        UpdateAutonomousDatabaseDetails,
    )
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


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        autonomous_database_id=dict(type="str"),
        db_name=dict(type="str"),
        display_name=dict(type="str"),
        admin_password=dict(type="str", no_log=True),
        cpu_core_count=dict(type="int"),
        data_storage_size_in_tbs=dict(type="int"),
        db_workload=dict(
            type="str",
            choices=["OLTP", "DW", "AJD", "APEX"],
            default="OLTP",
        ),
        is_free_tier=dict(type="bool", default=False),
        is_auto_scaling_enabled=dict(type="bool", default=False),
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


def get_autonomous_database(client, autonomous_database_id):
    """Get an existing Autonomous Database by OCID."""
    try:
        response = call_with_retry(client.get_autonomous_database, autonomous_database_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_autonomous_database(client, compartment_id, db_name, display_name):
    """Find an Autonomous Database by compartment, db_name, or display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_autonomous_databases,
            compartment_id=compartment_id,
        )
        for adb in response.data:
            if adb.lifecycle_state in DEAD_STATES:
                continue
            if db_name and adb.db_name == db_name:
                return adb
            if display_name and adb.display_name == display_name:
                return adb
    except ServiceError:
        pass
    return None


def create_autonomous_database(module, client):
    """Create a new Autonomous Database."""
    params = module.params
    create_details = CreateAutonomousDatabaseDetails(
        compartment_id=params["compartment_id"],
        db_name=params["db_name"],
        display_name=params.get("display_name") or params["db_name"],
        admin_password=params["admin_password"],
        cpu_core_count=params.get("cpu_core_count"),
        data_storage_size_in_tbs=params.get("data_storage_size_in_tbs"),
        db_workload=params.get("db_workload"),
        is_free_tier=params.get("is_free_tier"),
        is_auto_scaling_enabled=params.get("is_auto_scaling_enabled"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_autonomous_database, create_details)
    adb = response.data

    adb = wait_for_resource(
        module,
        client.get_autonomous_database,
        adb.id,
        target_states=READY_STATES,
    )
    return adb


def update_autonomous_database(module, client, existing):
    """Update an existing Autonomous Database."""
    params = module.params
    update_details = UpdateAutonomousDatabaseDetails(
        display_name=params.get("display_name"),
        cpu_core_count=params.get("cpu_core_count"),
        data_storage_size_in_tbs=params.get("data_storage_size_in_tbs"),
        is_auto_scaling_enabled=params.get("is_auto_scaling_enabled"),
        admin_password=params.get("admin_password"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_autonomous_database,
        existing.id,
        update_details,
    )
    adb = response.data

    adb = wait_for_resource(
        module,
        client.get_autonomous_database,
        adb.id,
        target_states=READY_STATES,
    )
    return adb


def delete_autonomous_database(module, client, existing):
    """Delete an Autonomous Database."""
    call_with_retry(client.delete_autonomous_database, existing.id)
    wait_for_resource(
        module,
        client.get_autonomous_database,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "cpu_core_count",
        "data_storage_size_in_tbs",
        "is_auto_scaling_enabled",
    ]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    # Check tags
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
        required_if=[
            ("state", "present", ("compartment_id", "db_name", "admin_password"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("autonomous_database_id"):
        existing = get_autonomous_database(client, params["autonomous_database_id"])
    elif params.get("compartment_id"):
        existing = find_autonomous_database(
            client,
            params["compartment_id"],
            params.get("db_name"),
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_autonomous_database(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        # Validate required params for create
        for req in ("compartment_id", "db_name", "admin_password"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an Autonomous Database.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_autonomous_database(module, client)
        module.exit_json(changed=True, autonomous_database=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_autonomous_database(module, client, existing)
        module.exit_json(changed=True, autonomous_database=to_dict(resource))
        return

    module.exit_json(changed=False, autonomous_database=to_dict(existing))


if __name__ == "__main__":
    main()
