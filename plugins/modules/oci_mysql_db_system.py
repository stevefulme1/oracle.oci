# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI MySQL Database Systems."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_mysql_db_system
short_description: Manage MySQL Database Systems in OCI
description:
    - Create, update, and delete MySQL Database Systems in Oracle Cloud Infrastructure.
    - MySQL Database Service is a fully managed database service powered by the
      MySQL Enterprise Edition.
    - This module uses the OCI Python SDK C(oci.mysql.DbSystemClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the MySQL DB System.
            - Required when creating a new MySQL DB System.
        type: str
    db_system_id:
        description:
            - The OCID of an existing MySQL DB System.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the MySQL DB System.
        type: str
    admin_username:
        description:
            - The name of the administrator user for the MySQL DB System.
            - Required when creating a new MySQL DB System.
        type: str
    admin_password:
        description:
            - The password for the administrator user.
            - Required when creating a new MySQL DB System.
        type: str
    shape_name:
        description:
            - The name of the shape (e.g. MySQL.VM.Standard.E3.1.8GB).
            - Required when creating a new MySQL DB System.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet for the MySQL DB System.
            - Required when creating a new MySQL DB System.
        type: str
    availability_domain:
        description:
            - The availability domain where the MySQL DB System will be created.
            - Required when creating a new MySQL DB System.
        type: str
    data_storage_size_in_gbs:
        description:
            - The initial data storage size in GB for the MySQL DB System.
        type: int
    mysql_version:
        description:
            - The specific MySQL version identifier (e.g. 8.0.32).
        type: str
    state:
        description:
            - The desired state of the MySQL DB System.
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
- name: Create a MySQL DB System
  oracle.oci.oci_mysql_db_system:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My MySQL DB"
    admin_username: "adminuser"
    admin_password: "ExamplePassword123#"
    shape_name: "MySQL.VM.Standard.E3.1.8GB"
    subnet_id: "ocid1.subnet.oc1..example"
    availability_domain: "Uocm:US-ASHBURN-AD-1"
    data_storage_size_in_gbs: 50
    state: present

- name: Update a MySQL DB System display name
  oracle.oci.oci_mysql_db_system:
    db_system_id: "ocid1.mysqldbsystem.oc1..example"
    display_name: "Updated MySQL DB"
    state: present

- name: Delete a MySQL DB System
  oracle.oci.oci_mysql_db_system:
    db_system_id: "ocid1.mysqldbsystem.oc1..example"
    state: absent
"""

RETURN = r"""
mysql_db_system:
    description: Details of the MySQL DB System.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.mysqldbsystem.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My MySQL DB"
        lifecycle_state: "ACTIVE"
        shape_name: "MySQL.VM.Standard.E3.1.8GB"
        data_storage_size_in_gbs: 50
        mysql_version: "8.0.32"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.mysql import DbSystemClient
    from oci.mysql.models import (
        CreateDbSystemDetails,
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
        display_name=dict(type="str"),
        admin_username=dict(type="str"),
        admin_password=dict(type="str", no_log=True),
        shape_name=dict(type="str"),
        subnet_id=dict(type="str"),
        availability_domain=dict(type="str"),
        data_storage_size_in_gbs=dict(type="int"),
        mysql_version=dict(type="str"),
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


def get_mysql_db_system(client, db_system_id):
    """Get an existing MySQL DB System by OCID."""
    try:
        response = call_with_retry(client.get_db_system, db_system_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_mysql_db_system(client, compartment_id, display_name):
    """Find a MySQL DB System by compartment and display_name."""
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
    except ServiceError:
        pass
    return None


def create_mysql_db_system(module, client):
    """Create a new MySQL DB System."""
    params = module.params
    create_details = CreateDbSystemDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        admin_username=params["admin_username"],
        admin_password=params["admin_password"],
        shape_name=params["shape_name"],
        subnet_id=params["subnet_id"],
        availability_domain=params["availability_domain"],
        data_storage_size_in_gbs=params.get("data_storage_size_in_gbs"),
        mysql_version=params.get("mysql_version"),
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


def update_mysql_db_system(module, client, existing):
    """Update an existing MySQL DB System."""
    params = module.params
    update_details = UpdateDbSystemDetails(
        display_name=params.get("display_name"),
        data_storage_size_in_gbs=params.get("data_storage_size_in_gbs"),
        mysql_version=params.get("mysql_version"),
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
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_mysql_db_system(module, client, existing):
    """Delete a MySQL DB System."""
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
        "data_storage_size_in_gbs",
        "mysql_version",
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

    client = create_service_client(module, DbSystemClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("db_system_id"):
        existing = get_mysql_db_system(client, params["db_system_id"])
    elif params.get("compartment_id"):
        existing = find_mysql_db_system(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_mysql_db_system(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "admin_username", "admin_password",
                    "shape_name", "subnet_id", "availability_domain"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a MySQL DB System.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_mysql_db_system(module, client)
        module.exit_json(changed=True, mysql_db_system=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_mysql_db_system(module, client, existing)
        module.exit_json(changed=True, mysql_db_system=to_dict(resource))
        return

    module.exit_json(changed=False, mysql_db_system=to_dict(existing))


if __name__ == "__main__":
    main()
