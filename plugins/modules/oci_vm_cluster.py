# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Exadata VM Clusters."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_vm_cluster
short_description: Manage Exadata VM Clusters in OCI
description:
    - Create, update, and delete VM Clusters on Exadata Cloud Infrastructure
      in Oracle Cloud Infrastructure.
    - A VM Cluster is a set of virtual machines running on Exadata infrastructure
      that host Oracle Database instances.
    - This module uses the OCI Python SDK C(oci.database.DatabaseClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the VM Cluster.
            - Required when creating a new VM Cluster.
        type: str
    vm_cluster_id:
        description:
            - The OCID of an existing VM Cluster.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the VM Cluster.
            - Required when creating a new VM Cluster.
        type: str
    exadata_infrastructure_id:
        description:
            - The OCID of the Exadata infrastructure on which to create the VM Cluster.
            - Required when creating a new VM Cluster.
        type: str
    vm_cluster_network_id:
        description:
            - The OCID of the VM cluster network.
            - Required when creating a new VM Cluster.
        type: str
    cpus_enabled:
        description:
            - The number of enabled CPU cores.
            - Required when creating a new VM Cluster.
        type: int
    memory_size_in_gbs:
        description:
            - The memory allocated in GBs.
        type: int
    db_node_storage_size_in_gbs:
        description:
            - The local node storage allocated in GBs.
        type: int
    data_storage_size_in_tbs:
        description:
            - The data disk group size to be allocated in TBs.
        type: float
    ssh_public_keys:
        description:
            - The public SSH keys for access to the VM Cluster.
            - Required when creating a new VM Cluster.
        type: list
        elements: str
    gi_version:
        description:
            - The Oracle Grid Infrastructure software version.
            - Required when creating a new VM Cluster.
        type: str
    state:
        description:
            - The desired state of the VM Cluster.
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
- name: Create a VM Cluster
  stevefulme1.oci_cloud.oci_vm_cluster:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My VM Cluster"
    exadata_infrastructure_id: "ocid1.exadatainfrastructure.oc1..example"
    vm_cluster_network_id: "ocid1.vmclusternetwork.oc1..example"
    cpus_enabled: 4
    memory_size_in_gbs: 60
    data_storage_size_in_tbs: 2
    ssh_public_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAA..."
    gi_version: "19.0.0.0"
    state: present

- name: Update a VM Cluster
  stevefulme1.oci_cloud.oci_vm_cluster:
    vm_cluster_id: "ocid1.vmcluster.oc1..example"
    cpus_enabled: 8
    memory_size_in_gbs: 120
    state: present

- name: Delete a VM Cluster
  stevefulme1.oci_cloud.oci_vm_cluster:
    vm_cluster_id: "ocid1.vmcluster.oc1..example"
    state: absent
"""

RETURN = r"""
vm_cluster:
    description: Details of the VM Cluster.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.vmcluster.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My VM Cluster"
        lifecycle_state: "AVAILABLE"
        cpus_enabled: 4
        memory_size_in_gbs: 60
        data_storage_size_in_tbs: 2
        gi_version: "19.0.0.0"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.database import DatabaseClient
    from oci.database.models import (
        CreateVmClusterDetails,
        UpdateVmClusterDetails,
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
        vm_cluster_id=dict(type="str"),
        display_name=dict(type="str"),
        exadata_infrastructure_id=dict(type="str"),
        vm_cluster_network_id=dict(type="str"),
        cpus_enabled=dict(type="int"),
        memory_size_in_gbs=dict(type="int"),
        db_node_storage_size_in_gbs=dict(type="int"),
        data_storage_size_in_tbs=dict(type="float"),
        ssh_public_keys=dict(type="list", elements="str", no_log=False),
        gi_version=dict(type="str"),
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


def get_vm_cluster(client, vm_cluster_id):
    """Get an existing VM Cluster by OCID."""
    try:
        response = call_with_retry(client.get_vm_cluster, vm_cluster_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_vm_cluster(client, compartment_id, display_name):
    """Find a VM Cluster by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_vm_clusters,
            compartment_id=compartment_id,
        )
        for vmc in response.data:
            if vmc.lifecycle_state in DEAD_STATES:
                continue
            if display_name and vmc.display_name == display_name:
                return vmc
    except ServiceError:
        pass
    return None


def create_vm_cluster(module, client):
    """Create a new VM Cluster."""
    params = module.params
    create_details = CreateVmClusterDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        exadata_infrastructure_id=params["exadata_infrastructure_id"],
        vm_cluster_network_id=params["vm_cluster_network_id"],
        cpus_enabled=params["cpus_enabled"],
        memory_size_in_gbs=params.get("memory_size_in_gbs"),
        db_node_storage_size_in_gbs=params.get("db_node_storage_size_in_gbs"),
        data_storage_size_in_tbs=params.get("data_storage_size_in_tbs"),
        ssh_public_keys=params["ssh_public_keys"],
        gi_version=params["gi_version"],
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_vm_cluster, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_vm_cluster,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_vm_cluster(module, client, existing):
    """Update an existing VM Cluster."""
    params = module.params
    update_details = UpdateVmClusterDetails(
        display_name=params.get("display_name"),
        cpus_enabled=params.get("cpus_enabled"),
        memory_size_in_gbs=params.get("memory_size_in_gbs"),
        db_node_storage_size_in_gbs=params.get("db_node_storage_size_in_gbs"),
        data_storage_size_in_tbs=params.get("data_storage_size_in_tbs"),
        ssh_public_keys=params.get("ssh_public_keys"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_vm_cluster,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_vm_cluster,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def delete_vm_cluster(module, client, existing):
    """Delete a VM Cluster."""
    call_with_retry(client.delete_vm_cluster, existing.id)
    wait_for_resource(
        module,
        client.get_vm_cluster,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "cpus_enabled",
        "memory_size_in_gbs",
        "db_node_storage_size_in_gbs",
        "data_storage_size_in_tbs",
    ]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("ssh_public_keys") is not None:
        current_keys = getattr(existing, "ssh_public_keys", None) or []
        if sorted(params["ssh_public_keys"]) != sorted(current_keys):
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
    if params.get("vm_cluster_id"):
        existing = get_vm_cluster(client, params["vm_cluster_id"])
    elif params.get("compartment_id"):
        existing = find_vm_cluster(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_vm_cluster(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "display_name", "exadata_infrastructure_id",
                    "vm_cluster_network_id", "cpus_enabled", "ssh_public_keys", "gi_version"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a VM Cluster.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_vm_cluster(module, client)
        module.exit_json(changed=True, vm_cluster=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_vm_cluster(module, client, existing)
        module.exit_json(changed=True, vm_cluster=to_dict(resource))
        return

    module.exit_json(changed=False, vm_cluster=to_dict(existing))


if __name__ == "__main__":
    main()
