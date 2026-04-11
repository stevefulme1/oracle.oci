# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Pluggable Databases."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_pluggable_database
short_description: Manage Pluggable Databases in OCI
description:
    - Create, update, and delete Pluggable Databases (PDBs) in Oracle Cloud Infrastructure.
    - A Pluggable Database is a portable collection of schemas, schema objects,
      and nonschema objects within an Oracle Multitenant container database (CDB).
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
    pluggable_database_id:
        description:
            - The OCID of an existing Pluggable Database.
            - Required for update and delete operations.
        type: str
    container_database_id:
        description:
            - The OCID of the CDB (Container Database) to create the PDB in.
            - Required when creating a new Pluggable Database.
        type: str
    pdb_name:
        description:
            - The name for the Pluggable Database.
            - Required when creating a new Pluggable Database.
        type: str
    pdb_admin_password:
        description:
            - The password for the PDB admin user.
            - Required when creating a new Pluggable Database.
        type: str
    state:
        description:
            - The desired state of the Pluggable Database.
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
- name: Create a Pluggable Database
  oracle.oci.oci_pluggable_database:
    container_database_id: "ocid1.database.oc1..example"
    pdb_name: "mypdb"
    pdb_admin_password: "ExamplePassword123#"
    state: present

- name: Delete a Pluggable Database
  oracle.oci.oci_pluggable_database:
    pluggable_database_id: "ocid1.pluggabledatabase.oc1..example"
    state: absent
"""

RETURN = r"""
pluggable_database:
    description: Details of the Pluggable Database.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.pluggabledatabase.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        pdb_name: "mypdb"
        lifecycle_state: "AVAILABLE"
        container_database_id: "ocid1.database.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreatePluggableDatabaseDetails,
        UpdatePluggableDatabaseDetails,
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
        pluggable_database_id=dict(type="str"),
        container_database_id=dict(type="str"),
        pdb_name=dict(type="str"),
        pdb_admin_password=dict(type="str", no_log=True),
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


def get_pluggable_database(client, pluggable_database_id):
    """Get an existing Pluggable Database by OCID."""
    try:
        response = call_with_retry(client.get_pluggable_database, pluggable_database_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_pluggable_database(client, compartment_id, container_database_id, pdb_name):
    """Find a Pluggable Database by compartment, container DB, and PDB name."""
    if not compartment_id:
        return None
    try:
        kwargs = dict(compartment_id=compartment_id)
        if container_database_id:
            kwargs["database_id"] = container_database_id
        response = call_with_retry(
            client.list_pluggable_databases,
            **kwargs,
        )
        for pdb in response.data:
            if pdb.lifecycle_state in DEAD_STATES:
                continue
            if pdb_name and pdb.pdb_name == pdb_name:
                return pdb
    except ServiceError:
        pass
    return None


def create_pluggable_database(module, client):
    """Create a new Pluggable Database."""
    params = module.params
    create_details = CreatePluggableDatabaseDetails(
        container_database_id=params["container_database_id"],
        pdb_name=params["pdb_name"],
        pdb_admin_password=params.get("pdb_admin_password"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_pluggable_database, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_pluggable_database,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_pluggable_database(module, client, existing):
    """Update an existing Pluggable Database."""
    params = module.params
    update_details = UpdatePluggableDatabaseDetails(
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_pluggable_database,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_pluggable_database,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_pluggable_database(module, client, existing):
    """Delete a Pluggable Database."""
    call_with_retry(client.delete_pluggable_database, existing.id)
    wait_for_resource(
        module,
        client.get_pluggable_database,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
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
    if params.get("pluggable_database_id"):
        existing = get_pluggable_database(client, params["pluggable_database_id"])
    elif params.get("compartment_id"):
        existing = find_pluggable_database(
            client,
            params["compartment_id"],
            params.get("container_database_id"),
            params.get("pdb_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_pluggable_database(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("container_database_id", "pdb_name"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a Pluggable Database.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_pluggable_database(module, client)
        module.exit_json(changed=True, pluggable_database=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_pluggable_database(module, client, existing)
        module.exit_json(changed=True, pluggable_database=to_dict(resource))
        return

    module.exit_json(changed=False, pluggable_database=to_dict(existing))


if __name__ == "__main__":
    main()
