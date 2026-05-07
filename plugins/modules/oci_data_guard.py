# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Data Guard associations."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_data_guard
short_description: Manage Data Guard associations in OCI
description:
    - Create, update, and delete Data Guard associations in Oracle Cloud Infrastructure.
    - Data Guard provides a set of services to create, maintain, manage, and monitor one
      or more standby databases to protect against data loss.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    database_id:
        description:
            - The OCID of the primary database for the Data Guard association.
            - Required when creating a new Data Guard association.
        type: str
    data_guard_association_id:
        description:
            - The OCID of an existing Data Guard association.
            - Required for update and delete operations.
        type: str
    creation_type:
        description:
            - Specifies whether to create the peer database in an existing DB System or a new one.
        type: str
        choices:
            - ExistingDbSystem
            - NewDbSystem
        default: ExistingDbSystem
    peer_db_system_id:
        description:
            - The OCID of the DB System to create the standby database on.
            - Required when I(creation_type) is C(ExistingDbSystem).
        type: str
    peer_db_home_id:
        description:
            - The OCID of the DB Home to create the standby database in.
            - Required when I(creation_type) is C(ExistingDbSystem).
        type: str
    peer_db_unique_name:
        description:
            - A unique name for the standby database.
        type: str
    protection_mode:
        description:
            - The protection mode for the Data Guard association.
            - C(MAXIMUM_AVAILABILITY) provides zero data loss with synchronous redo transport.
            - C(MAXIMUM_PERFORMANCE) provides near-zero data loss with asynchronous redo transport.
            - C(MAXIMUM_PROTECTION) provides zero data loss with synchronous transport and failover.
        type: str
        choices:
            - MAXIMUM_AVAILABILITY
            - MAXIMUM_PERFORMANCE
            - MAXIMUM_PROTECTION
        default: MAXIMUM_PERFORMANCE
    transport_type:
        description:
            - The redo transport type for the Data Guard association.
        type: str
        choices:
            - SYNC
            - ASYNC
            - FASTSYNC
        default: ASYNC
    database_admin_password:
        description:
            - The admin password of the primary database in the Data Guard association.
            - Required when creating a Data Guard association.
        type: str
    state:
        description:
            - The desired state of the Data Guard association.
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
- name: Create a Data Guard association with an existing DB System
  stevefulme1.oci_cloud.oci_data_guard:
    database_id: "ocid1.database.oc1..example"
    creation_type: ExistingDbSystem
    peer_db_system_id: "ocid1.dbsystem.oc1..example"
    peer_db_home_id: "ocid1.dbhome.oc1..example"
    peer_db_unique_name: "mydb_standby"
    protection_mode: MAXIMUM_PERFORMANCE
    transport_type: ASYNC
    database_admin_password: "ExamplePassword123#"
    state: present

- name: Create a Data Guard association with MAXIMUM_AVAILABILITY
  stevefulme1.oci_cloud.oci_data_guard:
    database_id: "ocid1.database.oc1..example"
    creation_type: ExistingDbSystem
    peer_db_system_id: "ocid1.dbsystem.oc1..example"
    peer_db_home_id: "ocid1.dbhome.oc1..example"
    protection_mode: MAXIMUM_AVAILABILITY
    transport_type: SYNC
    database_admin_password: "ExamplePassword123#"
    state: present

- name: Update Data Guard protection mode and transport type
  stevefulme1.oci_cloud.oci_data_guard:
    database_id: "ocid1.database.oc1..example"
    data_guard_association_id: "ocid1.dgassociation.oc1..example"
    protection_mode: MAXIMUM_AVAILABILITY
    transport_type: SYNC
    database_admin_password: "ExamplePassword123#"
    state: present

- name: Delete a Data Guard association
  stevefulme1.oci_cloud.oci_data_guard:
    database_id: "ocid1.database.oc1..example"
    data_guard_association_id: "ocid1.dgassociation.oc1..example"
    state: absent
"""

RETURN = r"""
data_guard_association:
    description: Details of the Data Guard association.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dgassociation.oc1..example"
        database_id: "ocid1.database.oc1..example"
        peer_db_system_id: "ocid1.dbsystem.oc1..example"
        peer_database_id: "ocid1.database.oc1..peerexample"
        lifecycle_state: "AVAILABLE"
        protection_mode: "MAXIMUM_PERFORMANCE"
        transport_type: "ASYNC"
        role: "PRIMARY"
        peer_role: "STANDBY"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateDataGuardAssociationWithNewDbSystemDetails,
        CreateDataGuardAssociationToExistingDbSystemDetails,
        UpdateDataGuardAssociationDetails,
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
)

# Data Guard specific lifecycle states
DG_AVAILABLE_STATES = READY_STATES | {"AVAILABLE"}
DG_TERMINATED_STATES = DEAD_STATES | {"TERMINATED"}


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        database_id=dict(type="str"),
        data_guard_association_id=dict(type="str"),
        creation_type=dict(
            type="str",
            choices=["ExistingDbSystem", "NewDbSystem"],
            default="ExistingDbSystem",
        ),
        peer_db_system_id=dict(type="str"),
        peer_db_home_id=dict(type="str"),
        peer_db_unique_name=dict(type="str"),
        protection_mode=dict(
            type="str",
            choices=[
                "MAXIMUM_AVAILABILITY",
                "MAXIMUM_PERFORMANCE",
                "MAXIMUM_PROTECTION",
            ],
            default="MAXIMUM_PERFORMANCE",
        ),
        transport_type=dict(
            type="str",
            choices=["SYNC", "ASYNC", "FASTSYNC"],
            default="ASYNC",
        ),
        database_admin_password=dict(type="str", no_log=True),
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


def get_data_guard_association(client, database_id, data_guard_association_id):
    """Get an existing Data Guard association by OCID."""
    try:
        response = call_with_retry(
            client.get_data_guard_association,
            database_id,
            data_guard_association_id,
        )
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_data_guard_association(client, database_id):
    """Find Data Guard associations for a given database."""
    if not database_id:
        return None
    try:
        response = call_with_retry(
            client.list_data_guard_associations,
            database_id=database_id,
        )
        for dga in response.data:
            if dga.lifecycle_state in DG_TERMINATED_STATES:
                continue
            return dga
    except ServiceError:
        pass
    return None


def _wait_for_dg(module, client, database_id, dg_id):
    """Poll a Data Guard association until it reaches a ready state."""
    import time

    wait = module.params.get("wait", True)
    if not wait:
        resp = call_with_retry(client.get_data_guard_association, database_id, dg_id)
        return resp.data

    timeout = module.params.get("wait_timeout", 1200)
    interval = module.params.get("wait_interval", 30)
    start = time.monotonic()

    while True:
        try:
            resp = client.get_data_guard_association(database_id, dg_id)
            resource = resp.data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

        state = getattr(resource, "lifecycle_state", None)
        if state in DG_AVAILABLE_STATES:
            return resource
        if state in ("FAILED",):
            module.fail_json(
                msg=f"Data Guard association {dg_id} entered failure state: {state}",
            )
        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            module.fail_json(
                msg=f"Timed out waiting for Data Guard association {dg_id}. State: {state}",
            )
        time.sleep(min(interval, timeout - elapsed))


def create_data_guard_association(module, client):
    """Create a new Data Guard association."""
    params = module.params

    if params["creation_type"] == "ExistingDbSystem":
        create_details = CreateDataGuardAssociationToExistingDbSystemDetails(
            database_admin_password=params["database_admin_password"],
            protection_mode=params["protection_mode"],
            transport_type=params["transport_type"],
            peer_db_system_id=params.get("peer_db_system_id"),
            peer_db_home_id=params.get("peer_db_home_id"),
            peer_db_unique_name=params.get("peer_db_unique_name"),
        )
    else:
        create_details = CreateDataGuardAssociationWithNewDbSystemDetails(
            database_admin_password=params["database_admin_password"],
            protection_mode=params["protection_mode"],
            transport_type=params["transport_type"],
            peer_db_unique_name=params.get("peer_db_unique_name"),
        )

    response = call_with_retry(
        client.create_data_guard_association,
        params["database_id"],
        create_details,
    )
    dga = response.data

    dga = _wait_for_dg(module, client, params["database_id"], dga.id)
    return dga


def update_data_guard_association(module, client, existing):
    """Update an existing Data Guard association."""
    params = module.params

    update_details = UpdateDataGuardAssociationDetails(
        database_admin_password=params["database_admin_password"],
        protection_mode=params.get("protection_mode"),
        transport_type=params.get("transport_type"),
    )

    response = call_with_retry(
        client.update_data_guard_association,
        params["database_id"],
        existing.id,
        update_details,
    )
    dga = response.data

    dga = _wait_for_dg(module, client, params["database_id"], dga.id)
    return dga


def delete_data_guard_association(module, client, existing):
    """Delete a Data Guard association by terminating the standby database."""
    # The OCI API does not have a direct delete for Data Guard associations.
    # The association is removed by terminating the standby DB System or database.
    # For this module we call delete_data_guard_association if available,
    # otherwise we report the limitation.
    try:
        call_with_retry(
            client.delete_data_guard_association,
            module.params["database_id"],
            existing.id,
        )
    except (AttributeError, ServiceError) as e:
        # Some SDK versions may not expose this method; fall back to guidance.
        if isinstance(e, AttributeError):
            module.fail_json(
                msg="Direct deletion of Data Guard associations is not supported in this "
                "SDK version. Terminate the standby DB System to remove the association.",
            )
        raise


def needs_update(params, existing):
    """Determine if the existing Data Guard association differs from desired state."""
    updatable = ["protection_mode", "transport_type"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    return False


def main():
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("database_id", "database_admin_password")),
            ("state", "absent", ("database_id", "data_guard_association_id")),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("data_guard_association_id") and params.get("database_id"):
        existing = get_data_guard_association(
            client,
            params["database_id"],
            params["data_guard_association_id"],
        )
    elif params.get("database_id"):
        existing = find_data_guard_association(client, params["database_id"])

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_data_guard_association(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        if not params.get("database_admin_password"):
            module.fail_json(
                msg="Parameter 'database_admin_password' is required to create a Data Guard association.",
            )
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_data_guard_association(module, client)
        module.exit_json(changed=True, data_guard_association=to_dict(resource))
        return

    if needs_update(params, existing):
        if not params.get("database_admin_password"):
            module.fail_json(
                msg="Parameter 'database_admin_password' is required to update a Data Guard association.",
            )
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_data_guard_association(module, client, existing)
        module.exit_json(changed=True, data_guard_association=to_dict(resource))
        return

    module.exit_json(changed=False, data_guard_association=to_dict(existing))


if __name__ == "__main__":
    main()
