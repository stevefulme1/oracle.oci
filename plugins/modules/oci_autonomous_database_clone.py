# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for cloning OCI Autonomous Databases."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_autonomous_database_clone
short_description: Clone an Autonomous Database in OCI
description:
    - Create a clone of an existing Autonomous Database.
    - Supports full clones (data + metadata) and metadata-only clones.
    - Can also manage the lifecycle of an existing cloned database (delete).
    - Uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment for the cloned Autonomous Database.
            - Required when creating a clone (I(state=present)).
        type: str
    source_autonomous_database_id:
        description:
            - The OCID of the source Autonomous Database to clone from.
            - Required when creating a clone (I(state=present)).
        type: str
    autonomous_database_id:
        description:
            - The OCID of an existing cloned Autonomous Database.
            - Required for delete operations (I(state=absent)) or to check
              if the clone already exists.
        type: str
    clone_type:
        description:
            - The type of clone to create.
            - C(FULL) creates a full clone with data and metadata.
            - C(METADATA) creates a metadata-only clone without data.
        type: str
        choices:
            - FULL
            - METADATA
        default: FULL
    display_name:
        description:
            - The user-friendly display name for the cloned database.
        type: str
    db_name:
        description:
            - The database name for the clone. Must begin with a letter and
              contain only alphanumeric characters.
            - Required when creating a clone.
        type: str
    admin_password:
        description:
            - The ADMIN password for the cloned database.
            - Required when creating a clone.
        type: str
    cpu_core_count:
        description:
            - The number of OCPU cores for the cloned database.
        type: int
    data_storage_size_in_tbs:
        description:
            - The data storage size in terabytes for the cloned database.
        type: int
    is_free_tier:
        description:
            - Whether the cloned database is an Always Free resource.
        type: bool
        default: false
    state:
        description:
            - The desired state of the cloned Autonomous Database.
            - C(present) will create the clone if it does not exist.
            - C(absent) will delete the clone if it exists.
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
- name: Create a full clone of an Autonomous Database
  stevefulme1.oci_cloud.oci_autonomous_database_clone:
    compartment_id: "ocid1.compartment.oc1..example"
    source_autonomous_database_id: "ocid1.autonomousdatabase.oc1..source"
    clone_type: FULL
    db_name: "myclonedb"
    display_name: "My Clone Database"
    admin_password: "ClonePass123#"
    cpu_core_count: 1
    data_storage_size_in_tbs: 1
    state: present

- name: Create a metadata-only clone
  stevefulme1.oci_cloud.oci_autonomous_database_clone:
    compartment_id: "ocid1.compartment.oc1..example"
    source_autonomous_database_id: "ocid1.autonomousdatabase.oc1..source"
    clone_type: METADATA
    db_name: "metaonlyclone"
    display_name: "Metadata Only Clone"
    admin_password: "ClonePass123#"
    is_free_tier: true
    state: present

- name: Delete a cloned Autonomous Database
  stevefulme1.oci_cloud.oci_autonomous_database_clone:
    autonomous_database_id: "ocid1.autonomousdatabase.oc1..clone"
    state: absent
"""

RETURN = r"""
autonomous_database:
    description: Details of the cloned Autonomous Database.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.autonomousdatabase.oc1..clone"
        compartment_id: "ocid1.compartment.oc1..example"
        db_name: "myclonedb"
        display_name: "My Clone Database"
        lifecycle_state: "AVAILABLE"
        cpu_core_count: 1
        data_storage_size_in_tbs: 1
        is_free_tier: false
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import CreateAutonomousDatabaseCloneDetails
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
        source_autonomous_database_id=dict(type="str"),
        autonomous_database_id=dict(type="str"),
        clone_type=dict(
            type="str",
            choices=["FULL", "METADATA"],
            default="FULL",
        ),
        display_name=dict(type="str"),
        db_name=dict(type="str"),
        admin_password=dict(type="str", no_log=True),
        cpu_core_count=dict(type="int"),
        data_storage_size_in_tbs=dict(type="int"),
        is_free_tier=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_autonomous_database(client, autonomous_database_id):
    """Get an existing Autonomous Database by OCID."""
    try:
        response = call_with_retry(client.get_autonomous_database, autonomous_database_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_clone_by_name(client, compartment_id, db_name, display_name):
    """Find an existing clone by compartment, db_name, or display_name."""
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


def create_clone(module, client):
    """Create a clone of an Autonomous Database."""
    params = module.params

    clone_details = CreateAutonomousDatabaseCloneDetails(
        compartment_id=params["compartment_id"],
        source_id=params["source_autonomous_database_id"],
        clone_type=params["clone_type"],
        db_name=params["db_name"],
        display_name=params.get("display_name") or params["db_name"],
        admin_password=params["admin_password"],
        cpu_core_count=params.get("cpu_core_count"),
        data_storage_size_in_tbs=params.get("data_storage_size_in_tbs"),
        is_free_tier=params.get("is_free_tier"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_autonomous_database, clone_details)
    adb = response.data

    adb = wait_for_resource(
        module,
        client.get_autonomous_database,
        adb.id,
        target_states=READY_STATES,
    )
    return adb


def delete_autonomous_database(module, client, existing):
    """Delete a cloned Autonomous Database."""
    call_with_retry(client.delete_autonomous_database, existing.id)
    wait_for_resource(
        module,
        client.get_autonomous_database,
        existing.id,
        target_states=DEAD_STATES,
    )


def main():
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "source_autonomous_database_id", "db_name", "admin_password")),
            ("state", "absent", ("autonomous_database_id",)),
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
        existing = find_clone_by_name(
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
    if existing is not None and existing.lifecycle_state not in DEAD_STATES:
        # Clone already exists, return it as-is (clones are not updatable via this module)
        module.exit_json(changed=False, autonomous_database=to_dict(existing))
        return

    # Validate required params for create
    for req in ("compartment_id", "source_autonomous_database_id", "db_name", "admin_password"):
        if not params.get(req):
            module.fail_json(
                msg="Parameter '{0}' is required to create a clone.".format(req)
            )

    if module.check_mode:
        module.exit_json(changed=True)

    resource = create_clone(module, client)
    module.exit_json(changed=True, autonomous_database=to_dict(resource))


if __name__ == "__main__":
    main()
