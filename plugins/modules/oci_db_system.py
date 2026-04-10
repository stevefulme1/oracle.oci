#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DB Systems (DBCS)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_db_system
short_description: Manage DB Systems (DBCS) in OCI
description:
    - Create, update, and terminate DB Systems in Oracle Cloud Infrastructure.
    - A DB System is a set of compute and storage resources running Oracle Database software
      in Oracle Cloud Infrastructure (DBCS).
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the DB System.
            - Required when creating a new DB System.
        type: str
    db_system_id:
        description:
            - The OCID of an existing DB System.
            - Required for update and delete operations.
        type: str
    availability_domain:
        description:
            - The availability domain where the DB System will be created.
            - Required when creating a new DB System.
        type: str
    shape:
        description:
            - The shape of the DB System (e.g. VM.Standard2.1, VM.Standard.E4.Flex).
            - Required when creating a new DB System.
        type: str
    ssh_public_keys:
        description:
            - The public SSH keys for access to the DB System.
            - Required when creating a new DB System.
        type: list
        elements: str
    subnet_id:
        description:
            - The OCID of the subnet for the DB System.
            - Required when creating a new DB System.
        type: str
    hostname:
        description:
            - The hostname for the DB System.
            - Required when creating a new DB System.
        type: str
    db_home:
        description:
            - Details for the DB Home, which includes the database configuration.
            - Required when creating a new DB System.
        type: dict
        suboptions:
            db_version:
                description:
                    - The Oracle Database version (e.g. 19.0.0.0, 21.0.0.0).
                type: str
                required: true
            database:
                description:
                    - Database configuration within the DB Home.
                type: dict
                required: true
                suboptions:
                    db_name:
                        description:
                            - The name of the database.
                        type: str
                        required: true
                    admin_password:
                        description:
                            - The password for the SYS, SYSTEM, and PDB admin accounts.
                        type: str
                        required: true
    display_name:
        description:
            - The user-friendly name for the DB System.
        type: str
    node_count:
        description:
            - The number of nodes in the DB System. For single-node use 1, for RAC use 2.
        type: int
        default: 1
    data_storage_size_in_gb:
        description:
            - The initial data storage size in GB. Must be a multiple of 256.
        type: int
    license_model:
        description:
            - The Oracle license model for the DB System.
        type: str
        choices:
            - LICENSE_INCLUDED
            - BRING_YOUR_OWN_LICENSE
        default: LICENSE_INCLUDED
    state:
        description:
            - The desired state of the DB System.
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
- name: Create a single-node DB System
  oracle.oci.oci_db_system:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:US-ASHBURN-AD-1"
    shape: "VM.Standard2.1"
    ssh_public_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAA..."
    subnet_id: "ocid1.subnet.oc1..example"
    hostname: "mydbhost"
    display_name: "My DB System"
    db_home:
      db_version: "19.0.0.0"
      database:
        db_name: "mydb"
        admin_password: "ExamplePassword123#"
    data_storage_size_in_gb: 256
    license_model: LICENSE_INCLUDED
    state: present

- name: Create a 2-node RAC DB System
  oracle.oci.oci_db_system:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:US-ASHBURN-AD-1"
    shape: "VM.Standard2.2"
    ssh_public_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAA..."
    subnet_id: "ocid1.subnet.oc1..example"
    hostname: "racdb"
    display_name: "RAC DB System"
    node_count: 2
    db_home:
      db_version: "19.0.0.0"
      database:
        db_name: "racdb"
        admin_password: "ExamplePassword123#"
    data_storage_size_in_gb: 512
    license_model: BRING_YOUR_OWN_LICENSE
    state: present

- name: Update a DB System display name and SSH keys
  oracle.oci.oci_db_system:
    db_system_id: "ocid1.dbsystem.oc1..example"
    display_name: "Updated DB System Name"
    ssh_public_keys:
      - "ssh-rsa NEWKEY..."
    state: present

- name: Terminate a DB System
  oracle.oci.oci_db_system:
    db_system_id: "ocid1.dbsystem.oc1..example"
    state: absent
"""

RETURN = r"""
db_system:
    description: Details of the DB System.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dbsystem.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My DB System"
        lifecycle_state: "AVAILABLE"
        shape: "VM.Standard2.1"
        hostname: "mydbhost"
        node_count: 1
        data_storage_size_in_gb: 256
        license_model: "LICENSE_INCLUDED"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateDbHomeDetails,
        CreateDatabaseDetails,
        LaunchDbSystemDetails,
        UpdateDbSystemDetails,
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
        db_system_id=dict(type="str"),
        availability_domain=dict(type="str"),
        shape=dict(type="str"),
        ssh_public_keys=dict(type="list", elements="str", no_log=False),
        subnet_id=dict(type="str"),
        hostname=dict(type="str"),
        db_home=dict(type="dict"),
        display_name=dict(type="str"),
        node_count=dict(type="int", default=1),
        data_storage_size_in_gb=dict(type="int"),
        license_model=dict(
            type="str",
            choices=["LICENSE_INCLUDED", "BRING_YOUR_OWN_LICENSE"],
            default="LICENSE_INCLUDED",
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


def get_db_system(client, db_system_id):
    """Get an existing DB System by OCID."""
    try:
        response = call_with_retry(client.get_db_system, db_system_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_db_system(client, compartment_id, display_name, hostname):
    """Find a DB System by compartment and display_name or hostname."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_db_systems,
            compartment_id=compartment_id,
        )
        for dbs in response.data:
            if dbs.lifecycle_state in DEAD_STATES:
                continue
            if display_name and dbs.display_name == display_name:
                return dbs
            if hostname and dbs.hostname == hostname:
                return dbs
    except ServiceError:
        pass
    return None


def build_db_home_details(db_home_params):
    """Build CreateDbHomeDetails from module params."""
    db_params = db_home_params.get("database", {})

    database_details = CreateDatabaseDetails(
        db_name=db_params["db_name"],
        admin_password=db_params["admin_password"],
    )

    return CreateDbHomeDetails(
        db_version=db_home_params["db_version"],
        database=database_details,
    )


def create_db_system(module, client):
    """Create a new DB System."""
    params = module.params

    launch_details = LaunchDbSystemDetails(
        compartment_id=params["compartment_id"],
        availability_domain=params["availability_domain"],
        shape=params["shape"],
        ssh_public_keys=params["ssh_public_keys"],
        subnet_id=params["subnet_id"],
        hostname=params["hostname"],
        display_name=params.get("display_name") or params["hostname"],
        db_home=build_db_home_details(params["db_home"]),
        node_count=params.get("node_count", 1),
        data_storage_size_in_gb=params.get("data_storage_size_in_gb"),
        license_model=params.get("license_model"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.launch_db_system, launch_details)
    db_system = response.data

    db_system = wait_for_resource(
        module,
        client.get_db_system,
        db_system.id,
        target_states=READY_STATES,
    )
    return db_system


def update_db_system(module, client, existing):
    """Update an existing DB System."""
    params = module.params

    update_details = UpdateDbSystemDetails(
        display_name=params.get("display_name"),
        ssh_public_keys=params.get("ssh_public_keys"),
        data_storage_size_in_gb=params.get("data_storage_size_in_gb"),
        license_model=params.get("license_model"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_db_system,
        existing.id,
        update_details,
    )
    db_system = response.data

    db_system = wait_for_resource(
        module,
        client.get_db_system,
        db_system.id,
        target_states=READY_STATES,
    )
    return db_system


def terminate_db_system(module, client, existing):
    """Terminate a DB System."""
    call_with_retry(client.terminate_db_system, existing.id)
    wait_for_resource(
        module,
        client.get_db_system,
        existing.id,
        target_states=DEAD_STATES | {"TERMINATED"},
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "data_storage_size_in_gb",
        "license_model",
    ]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    # Check ssh_public_keys
    if params.get("ssh_public_keys") is not None:
        current_keys = getattr(existing, "ssh_public_keys", None) or []
        if sorted(params["ssh_public_keys"]) != sorted(current_keys):
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
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("db_system_id"):
        existing = get_db_system(client, params["db_system_id"])
    elif params.get("compartment_id"):
        existing = find_db_system(
            client,
            params["compartment_id"],
            params.get("display_name"),
            params.get("hostname"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        terminate_db_system(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "availability_domain", "shape", "ssh_public_keys",
                    "subnet_id", "hostname", "db_home"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a DB System.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_db_system(module, client)
        module.exit_json(changed=True, db_system=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_db_system(module, client, existing)
        module.exit_json(changed=True, db_system=to_dict(resource))
        return

    module.exit_json(changed=False, db_system=to_dict(existing))


if __name__ == "__main__":
    main()
