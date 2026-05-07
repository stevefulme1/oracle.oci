# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI External Database Connectors."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_external_database
short_description: Manage External Database Connectors in OCI
description:
    - Create, update, and delete External Database Connectors in Oracle Cloud Infrastructure.
    - External Database Connectors enable OCI to connect to and manage databases
      running outside of OCI or in customer-managed infrastructure.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
    external_database_connector_id:
        description:
            - The OCID of an existing External Database Connector.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the External Database Connector.
            - Required when creating a new connector.
        type: str
    external_database_id:
        description:
            - The OCID of the external database resource.
            - Required when creating a new connector.
        type: str
    connector_type:
        description:
            - The type of connector used by the external database resource.
        type: str
        choices:
            - MACS
        default: MACS
    connection_string:
        description:
            - The connection string details for the external database.
        type: dict
        suboptions:
            hostname:
                description:
                    - The host name of the database.
                type: str
            port:
                description:
                    - The port used to connect to the database.
                type: int
            service:
                description:
                    - The name of the service alias used to connect to the database.
                type: str
            protocol:
                description:
                    - The protocol used to connect to the database.
                type: str
                choices:
                    - TCP
                    - TCPS
    connection_credentials:
        description:
            - The credentials used to connect to the external database.
        type: dict
        suboptions:
            credential_type:
                description:
                    - The type of credential used to connect to the database.
                type: str
            credential_name:
                description:
                    - The name of the credential information used to connect to the database.
                type: str
            username:
                description:
                    - The username for the external database.
                type: str
            password:
                description:
                    - The password for the external database.
                type: str
            role:
                description:
                    - The role of the user connecting to the external database.
                type: str
    state:
        description:
            - The desired state of the External Database Connector.
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
- name: Create an External Database Connector
  stevefulme1.oci_cloud.oci_external_database:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My External DB Connector"
    external_database_id: "ocid1.externaldatabase.oc1..example"
    connector_type: MACS
    connection_string:
      hostname: "dbhost.example.com"
      port: 1521
      service: "mydb.example.com"
      protocol: TCP
    connection_credentials:
      credential_type: DETAILS
      credential_name: "my_creds"
      username: "dbadmin"
      password: "ExamplePassword123#"
      role: NORMAL
    state: present

- name: Update an External Database Connector
  stevefulme1.oci_cloud.oci_external_database:
    external_database_connector_id: "ocid1.externaldatabaseconnector.oc1..example"
    display_name: "Updated External DB Connector"
    state: present

- name: Delete an External Database Connector
  stevefulme1.oci_cloud.oci_external_database:
    external_database_connector_id: "ocid1.externaldatabaseconnector.oc1..example"
    state: absent
"""

RETURN = r"""
external_database_connector:
    description: Details of the External Database Connector.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.externaldatabaseconnector.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My External DB Connector"
        lifecycle_state: "AVAILABLE"
        connector_type: "MACS"
        external_database_id: "ocid1.externaldatabase.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateExternalDatabaseConnectorDetails,
        UpdateExternalDatabaseConnectorDetails,
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
        external_database_connector_id=dict(type="str"),
        display_name=dict(type="str"),
        external_database_id=dict(type="str"),
        connector_type=dict(
            type="str",
            choices=["MACS"],
            default="MACS",
        ),
        connection_string=dict(type="dict"),
        connection_credentials=dict(type="dict", no_log=True),
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


def get_external_database_connector(client, connector_id):
    """Get an existing External Database Connector by OCID."""
    try:
        response = call_with_retry(client.get_external_database_connector, connector_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_external_database_connector(client, compartment_id, external_database_id, display_name):
    """Find an External Database Connector by compartment and display_name."""
    if not compartment_id or not external_database_id:
        return None
    try:
        response = call_with_retry(
            client.list_external_database_connectors,
            compartment_id=compartment_id,
            external_database_id=external_database_id,
        )
        for connector in response.data:
            if connector.lifecycle_state in DEAD_STATES:
                continue
            if display_name and connector.display_name == display_name:
                return connector
    except ServiceError:
        pass
    return None


def create_external_database_connector(module, client):
    """Create a new External Database Connector."""
    params = module.params
    create_details = CreateExternalDatabaseConnectorDetails(
        display_name=params["display_name"],
        external_database_id=params["external_database_id"],
        connector_type=params.get("connector_type", "MACS"),
        connection_string=params.get("connection_string"),
        connection_credentials=params.get("connection_credentials"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_external_database_connector, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_external_database_connector,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_external_database_connector(module, client, existing):
    """Update an existing External Database Connector."""
    params = module.params
    update_details = UpdateExternalDatabaseConnectorDetails(
        display_name=params.get("display_name"),
        connection_string=params.get("connection_string"),
        connection_credentials=params.get("connection_credentials"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_external_database_connector,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_external_database_connector,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_external_database_connector(module, client, existing):
    """Delete an External Database Connector."""
    call_with_retry(client.delete_external_database_connector, existing.id)
    wait_for_resource(
        module,
        client.get_external_database_connector,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = ["display_name"]
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

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("external_database_connector_id"):
        existing = get_external_database_connector(client, params["external_database_connector_id"])
    elif params.get("compartment_id") and params.get("external_database_id"):
        existing = find_external_database_connector(
            client,
            params["compartment_id"],
            params["external_database_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_external_database_connector(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("display_name", "external_database_id"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an External Database Connector.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_external_database_connector(module, client)
        module.exit_json(changed=True, external_database_connector=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_external_database_connector(module, client, existing)
        module.exit_json(changed=True, external_database_connector=to_dict(resource))
        return

    module.exit_json(changed=False, external_database_connector=to_dict(existing))


if __name__ == "__main__":
    main()
