# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI NoSQL Database tables."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_nosql_table
short_description: Manage NoSQL Database tables in OCI
description:
    - Create, update, and delete NoSQL Database tables in Oracle Cloud Infrastructure.
    - Oracle NoSQL Database Cloud Service provides on-demand throughput and storage-based
      provisioning for document, columnar, and key-value data models.
    - This module uses the OCI Python SDK C(oci.nosql.NosqlClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the NoSQL table.
            - Required when creating a new NoSQL table.
        type: str
    table_name_or_id:
        description:
            - The table name or OCID of an existing NoSQL table.
            - Required for update and delete operations.
        type: str
    name:
        description:
            - The name of the NoSQL table.
            - Required when creating a new NoSQL table.
        type: str
    ddl_statement:
        description:
            - The DDL statement to create or alter the table.
            - Required when creating a new NoSQL table.
        type: str
    table_limits:
        description:
            - Throughput and storage limits for the table.
        type: dict
        suboptions:
            max_read_units:
                description:
                    - Maximum sustained read throughput limit for the table.
                type: int
            max_write_units:
                description:
                    - Maximum sustained write throughput limit for the table.
                type: int
            max_storage_in_gbs:
                description:
                    - Maximum storage in GB for the table.
                type: int
    state:
        description:
            - The desired state of the NoSQL table.
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
- name: Create a NoSQL table
  stevefulme1.oci_cloud.oci_nosql_table:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my_table"
    ddl_statement: >
      CREATE TABLE my_table (id INTEGER, name STRING, PRIMARY KEY(id))
    table_limits:
      max_read_units: 50
      max_write_units: 50
      max_storage_in_gbs: 25
    state: present

- name: Update NoSQL table limits
  stevefulme1.oci_cloud.oci_nosql_table:
    table_name_or_id: "ocid1.nosqltable.oc1..example"
    table_limits:
      max_read_units: 100
      max_write_units: 100
      max_storage_in_gbs: 50
    state: present

- name: Delete a NoSQL table
  stevefulme1.oci_cloud.oci_nosql_table:
    table_name_or_id: "ocid1.nosqltable.oc1..example"
    state: absent
"""

RETURN = r"""
nosql_table:
    description: Details of the NoSQL table.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.nosqltable.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        name: "my_table"
        lifecycle_state: "ACTIVE"
        table_limits:
            max_read_units: 50
            max_write_units: 50
            max_storage_in_gbs: 25
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.nosql import NosqlClient
    from oci.nosql.models import (
        CreateTableDetails,
        UpdateTableDetails,
        TableLimits,
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
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        table_name_or_id=dict(type="str"),
        name=dict(type="str"),
        ddl_statement=dict(type="str"),
        table_limits=dict(type="dict"),
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


def get_nosql_table(client, table_name_or_id):
    """Get an existing NoSQL table by name or OCID."""
    try:
        response = call_with_retry(client.get_table, table_name_or_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_nosql_table(client, compartment_id, name):
    """Find a NoSQL table by compartment and name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_tables,
            compartment_id=compartment_id,
        )
        for table in response.data:
            if table.lifecycle_state in DEAD_STATES:
                continue
            if name and table.name == name:
                return get_nosql_table(client, table.id)
    except ServiceError:
        pass
    return None


def build_table_limits(limits_dict):
    """Build a TableLimits object from a dict."""
    if not limits_dict:
        return None
    return TableLimits(
        max_read_units=limits_dict.get("max_read_units", 0),
        max_write_units=limits_dict.get("max_write_units", 0),
        max_storage_in_gbs=limits_dict.get("max_storage_in_gbs", 0),
    )


def create_nosql_table(module, client):
    """Create a new NoSQL table."""
    params = module.params
    create_details = CreateTableDetails(
        compartment_id=params["compartment_id"],
        name=params["name"],
        ddl_statement=params["ddl_statement"],
        table_limits=build_table_limits(params.get("table_limits")),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    call_with_retry(client.create_table, create_details)
    # create_table returns a work request; get the table by name
    table = wait_for_resource(
        module,
        client.get_table,
        params["name"],
        target_states=READY_STATES,
    )
    return table


def update_nosql_table(module, client, existing):
    """Update an existing NoSQL table."""
    params = module.params
    update_details = UpdateTableDetails(
        table_limits=build_table_limits(params.get("table_limits")),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    call_with_retry(
        client.update_table,
        existing.id,
        update_details,
    )

    table = wait_for_resource(
        module,
        client.get_table,
        existing.id,
        target_states=READY_STATES,
    )
    return table


def delete_nosql_table(module, client, existing):
    """Delete a NoSQL table."""
    call_with_retry(client.delete_table, existing.id)
    wait_for_resource(
        module,
        client.get_table,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    # Check table_limits
    if params.get("table_limits") is not None:
        desired_limits = params["table_limits"]
        current_limits = getattr(existing, "table_limits", None)
        if current_limits:
            for attr in ("max_read_units", "max_write_units", "max_storage_in_gbs"):
                desired_val = desired_limits.get(attr)
                if desired_val is not None:
                    current_val = getattr(current_limits, attr, None)
                    if current_val != desired_val:
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

    client = create_service_client(module, NosqlClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("table_name_or_id"):
        existing = get_nosql_table(client, params["table_name_or_id"])
    elif params.get("compartment_id"):
        existing = find_nosql_table(
            client,
            params["compartment_id"],
            params.get("name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_nosql_table(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "name", "ddl_statement"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a NoSQL table.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_nosql_table(module, client)
        module.exit_json(changed=True, nosql_table=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_nosql_table(module, client, existing)
        module.exit_json(changed=True, nosql_table=to_dict(resource))
        return

    module.exit_json(changed=False, nosql_table=to_dict(existing))


if __name__ == "__main__":
    main()
