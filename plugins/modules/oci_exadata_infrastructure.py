# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Exadata Cloud Infrastructure."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_exadata_infrastructure
short_description: Manage Exadata Cloud Infrastructure in OCI
description:
    - Create, update, and delete Exadata Cloud Infrastructure resources in
      Oracle Cloud Infrastructure.
    - Exadata Cloud Infrastructure provides dedicated Exadata hardware in OCI
      for running Oracle Database workloads.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the Exadata infrastructure.
            - Required when creating a new Exadata infrastructure.
        type: str
    exadata_infrastructure_id:
        description:
            - The OCID of an existing Exadata infrastructure.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the Exadata infrastructure.
            - Required when creating a new Exadata infrastructure.
        type: str
    shape:
        description:
            - The shape of the Exadata infrastructure (e.g. Exadata.X9M).
            - Required when creating a new Exadata infrastructure.
        type: str
    compute_count:
        description:
            - The number of compute servers for the Exadata infrastructure.
            - Required when creating a new Exadata infrastructure.
        type: int
    storage_count:
        description:
            - The number of storage servers for the Exadata infrastructure.
            - Required when creating a new Exadata infrastructure.
        type: int
    cloud_control_plane_server1:
        description:
            - The IP address for the first control plane server.
            - Required when creating a new Exadata infrastructure.
        type: str
    cloud_control_plane_server2:
        description:
            - The IP address for the second control plane server.
            - Required when creating a new Exadata infrastructure.
        type: str
    time_zone:
        description:
            - The time zone of the Exadata infrastructure (e.g. UTC, US/Pacific).
            - Required when creating a new Exadata infrastructure.
        type: str
    state:
        description:
            - The desired state of the Exadata infrastructure.
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
- name: Create an Exadata Cloud Infrastructure
  stevefulme1.oci_cloud.oci_exadata_infrastructure:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My Exadata Infra"
    shape: "Exadata.X9M"
    compute_count: 2
    storage_count: 3
    cloud_control_plane_server1: "10.0.0.1"
    cloud_control_plane_server2: "10.0.0.2"
    time_zone: "UTC"
    state: present

- name: Update an Exadata Cloud Infrastructure
  stevefulme1.oci_cloud.oci_exadata_infrastructure:
    exadata_infrastructure_id: "ocid1.exadatainfrastructure.oc1..example"
    compute_count: 4
    storage_count: 6
    state: present

- name: Delete an Exadata Cloud Infrastructure
  stevefulme1.oci_cloud.oci_exadata_infrastructure:
    exadata_infrastructure_id: "ocid1.exadatainfrastructure.oc1..example"
    state: absent
"""

RETURN = r"""
exadata_infrastructure:
    description: Details of the Exadata infrastructure.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.exadatainfrastructure.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My Exadata Infra"
        lifecycle_state: "ACTIVE"
        shape: "Exadata.X9M"
        compute_count: 2
        storage_count: 3
        time_zone: "UTC"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateExadataInfrastructureDetails,
        UpdateExadataInfrastructureDetails,
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
        exadata_infrastructure_id=dict(type="str"),
        display_name=dict(type="str"),
        shape=dict(type="str"),
        compute_count=dict(type="int"),
        storage_count=dict(type="int"),
        cloud_control_plane_server1=dict(type="str"),
        cloud_control_plane_server2=dict(type="str"),
        time_zone=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_exadata_infrastructure(client, exadata_infrastructure_id):
    """Get an existing Exadata infrastructure by OCID."""
    try:
        response = call_with_retry(client.get_exadata_infrastructure, exadata_infrastructure_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_exadata_infrastructure(client, compartment_id, display_name):
    """Find an Exadata infrastructure by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_exadata_infrastructures,
            compartment_id=compartment_id,
        )
        for infra in response.data:
            if infra.lifecycle_state in DEAD_STATES:
                continue
            if display_name and infra.display_name == display_name:
                return infra
    except ServiceError:
        pass
    return None


def create_exadata_infrastructure(module, client):
    """Create a new Exadata infrastructure."""
    params = module.params
    create_details = CreateExadataInfrastructureDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        shape=params["shape"],
        compute_count=params["compute_count"],
        storage_count=params["storage_count"],
        cloud_control_plane_server1=params.get("cloud_control_plane_server1"),
        cloud_control_plane_server2=params.get("cloud_control_plane_server2"),
        time_zone=params.get("time_zone"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_exadata_infrastructure, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_exadata_infrastructure,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_exadata_infrastructure(module, client, existing):
    """Update an existing Exadata infrastructure."""
    params = module.params
    update_details = UpdateExadataInfrastructureDetails(
        display_name=params.get("display_name"),
        compute_count=params.get("compute_count"),
        storage_count=params.get("storage_count"),
        cloud_control_plane_server1=params.get("cloud_control_plane_server1"),
        cloud_control_plane_server2=params.get("cloud_control_plane_server2"),
        time_zone=params.get("time_zone"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_exadata_infrastructure,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_exadata_infrastructure,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_exadata_infrastructure(module, client, existing):
    """Delete an Exadata infrastructure."""
    call_with_retry(client.delete_exadata_infrastructure, existing.id)
    wait_for_resource(
        module,
        client.get_exadata_infrastructure,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "compute_count",
        "storage_count",
        "cloud_control_plane_server1",
        "cloud_control_plane_server2",
        "time_zone",
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

    client = create_service_client(module, DatabaseClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("exadata_infrastructure_id"):
        existing = get_exadata_infrastructure(client, params["exadata_infrastructure_id"])
    elif params.get("compartment_id"):
        existing = find_exadata_infrastructure(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_exadata_infrastructure(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "display_name", "shape", "compute_count", "storage_count"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an Exadata infrastructure.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_exadata_infrastructure(module, client)
        module.exit_json(changed=True, exadata_infrastructure=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_exadata_infrastructure(module, client, existing)
        module.exit_json(changed=True, exadata_infrastructure=to_dict(resource))
        return

    module.exit_json(changed=False, exadata_infrastructure=to_dict(existing))


if __name__ == "__main__":
    main()
