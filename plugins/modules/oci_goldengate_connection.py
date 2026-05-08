# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI GoldenGate Connections."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_goldengate_connection
short_description: Manage GoldenGate Connections in OCI
description:
    - Create, update, and delete GoldenGate Connections in Oracle Cloud Infrastructure.
    - GoldenGate Connections represent the database or technology endpoints used
      in GoldenGate replication and data integration pipelines.
    - This module uses the OCI Python SDK C(oci.golden_gate.GoldenGateClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the GoldenGate connection.
            - Required when creating a new connection.
        type: str
    connection_id:
        description:
            - The OCID of an existing GoldenGate connection.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the GoldenGate connection.
            - Required when creating a new connection.
        type: str
    connection_type:
        description:
            - The type of connection.
            - Required when creating a new connection.
        type: str
        choices:
            - GOLDENGATE
            - KAFKA
            - KAFKA_SCHEMA_REGISTRY
            - MYSQL
            - OCI_OBJECT_STORAGE
            - ORACLE
            - AZURE_DATA_LAKE_STORAGE
            - POSTGRESQL
            - AZURE_SYNAPSE_ANALYTICS
            - SNOWFLAKE
            - AMAZON_S3
            - HDFS
            - MICROSOFT_SQLSERVER
            - AMAZON_KINESIS
            - GOOGLE_CLOUD_STORAGE
            - GOOGLE_BIGQUERY
            - GENERIC
            - REDIS
            - ELASTICSEARCH
            - DATABRICKS
    technology_type:
        description:
            - The technology type of the connection.
            - Required when creating a new connection.
        type: str
    username:
        description:
            - The username for the connection.
        type: str
    password:
        description:
            - The password for the connection.
        type: str
    host:
        description:
            - The hostname or IP address for the connection.
        type: str
    port:
        description:
            - The port number for the connection.
        type: int
    database_name:
        description:
            - The name of the database.
        type: str
    state:
        description:
            - The desired state of the GoldenGate connection.
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
- name: Create a GoldenGate Oracle connection
  stevefulme1.oci_cloud.oci_goldengate_connection:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My Oracle Connection"
    connection_type: ORACLE
    technology_type: ORACLE_DATABASE
    username: "ggadmin"
    password: "ExamplePassword123#"
    host: "dbhost.example.com"
    port: 1521
    database_name: "mydb"
    state: present

- name: Create a GoldenGate MySQL connection
  stevefulme1.oci_cloud.oci_goldengate_connection:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My MySQL Connection"
    connection_type: MYSQL
    technology_type: MYSQL_SERVER
    username: "ggadmin"
    password: "ExamplePassword123#"
    host: "mysqlhost.example.com"
    port: 3306
    database_name: "mydb"
    state: present

- name: Update a GoldenGate connection
  stevefulme1.oci_cloud.oci_goldengate_connection:
    connection_id: "ocid1.goldengateconnection.oc1..example"
    display_name: "Updated Connection"
    state: present

- name: Delete a GoldenGate connection
  stevefulme1.oci_cloud.oci_goldengate_connection:
    connection_id: "ocid1.goldengateconnection.oc1..example"
    state: absent
"""

RETURN = r"""
goldengate_connection:
    description: Details of the GoldenGate connection.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.goldengateconnection.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My Oracle Connection"
        lifecycle_state: "ACTIVE"
        connection_type: "ORACLE"
        technology_type: "ORACLE_DATABASE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.golden_gate import GoldenGateClient
    from oci.golden_gate.models import (
        CreateConnectionDetails,
        UpdateConnectionDetails,
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
        connection_id=dict(type="str"),
        display_name=dict(type="str"),
        connection_type=dict(
            type="str",
            choices=[
                "GOLDENGATE",
                "KAFKA",
                "KAFKA_SCHEMA_REGISTRY",
                "MYSQL",
                "OCI_OBJECT_STORAGE",
                "ORACLE",
                "AZURE_DATA_LAKE_STORAGE",
                "POSTGRESQL",
                "AZURE_SYNAPSE_ANALYTICS",
                "SNOWFLAKE",
                "AMAZON_S3",
                "HDFS",
                "MICROSOFT_SQLSERVER",
                "AMAZON_KINESIS",
                "GOOGLE_CLOUD_STORAGE",
                "GOOGLE_BIGQUERY",
                "GENERIC",
                "REDIS",
                "ELASTICSEARCH",
                "DATABRICKS",
            ],
        ),
        technology_type=dict(type="str"),
        username=dict(type="str"),
        password=dict(type="str", no_log=True),
        host=dict(type="str"),
        port=dict(type="int"),
        database_name=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_connection(client, connection_id):
    """Get an existing GoldenGate connection by OCID."""
    try:
        response = call_with_retry(client.get_connection, connection_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_connection(client, compartment_id, display_name):
    """Find a GoldenGate connection by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_connections,
            compartment_id=compartment_id,
        )
        for conn in response.data.items:
            if conn.lifecycle_state in DEAD_STATES:
                continue
            if display_name and conn.display_name == display_name:
                return get_connection(client, conn.id)
    except ServiceError:
        pass
    return None


def create_connection(module, client):
    """Create a new GoldenGate connection."""
    params = module.params
    create_details = CreateConnectionDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        connection_type=params["connection_type"],
        technology_type=params["technology_type"],
        username=params.get("username"),
        password=params.get("password"),
        host=params.get("host"),
        port=params.get("port"),
        database_name=params.get("database_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_connection, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_connection,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_connection(module, client, existing):
    """Update an existing GoldenGate connection."""
    params = module.params
    update_details = UpdateConnectionDetails(
        display_name=params.get("display_name"),
        username=params.get("username"),
        password=params.get("password"),
        host=params.get("host"),
        port=params.get("port"),
        database_name=params.get("database_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_connection,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_connection,
        existing.id,
        target_states=READY_STATES,
    )
    return resource


def delete_connection(module, client, existing):
    """Delete a GoldenGate connection."""
    call_with_retry(client.delete_connection, existing.id)
    wait_for_resource(
        module,
        client.get_connection,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "username",
        "host",
        "port",
        "database_name",
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

    client = create_service_client(module, GoldenGateClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("connection_id"):
        existing = get_connection(client, params["connection_id"])
    elif params.get("compartment_id"):
        existing = find_connection(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_connection(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "display_name", "connection_type", "technology_type"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a GoldenGate connection.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_connection(module, client)
        module.exit_json(changed=True, goldengate_connection=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_connection(module, client, existing)
        module.exit_json(changed=True, goldengate_connection=to_dict(resource))
        return

    module.exit_json(changed=False, goldengate_connection=to_dict(existing))


if __name__ == "__main__":
    main()
