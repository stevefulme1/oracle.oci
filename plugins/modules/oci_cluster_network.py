# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Cluster Networks."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_cluster_network
short_description: Manage OCI Cluster Networks
description:
    - Create, update, and delete HPC cluster networks in Oracle Cloud
      Infrastructure.
    - Uses the ComputeManagementClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment containing the cluster network.
            - Required when creating a new cluster network.
        type: str
    cluster_network_id:
        description:
            - The OCID of the cluster network.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the cluster network.
        type: str
    instance_pools:
        description:
            - The instance pools to create as part of the cluster network.
            - Required when creating a new cluster network.
        type: list
        elements: dict
        suboptions:
            instance_configuration_id:
                description:
                    - The OCID of the instance configuration for the pool.
                type: str
                required: true
            size:
                description:
                    - The number of instances in the pool.
                type: int
                required: true
            display_name:
                description:
                    - A user-friendly name for the instance pool.
                type: str
    placement_configuration:
        description:
            - The placement configuration for the cluster network.
            - Required when creating a new cluster network.
        type: dict
        suboptions:
            availability_domain:
                description:
                    - The availability domain for the cluster network.
                type: str
                required: true
            primary_subnet_id:
                description:
                    - The OCID of the primary subnet.
                type: str
                required: true
            secondary_vnic_subnets:
                description:
                    - The set of secondary VNIC subnets.
                type: list
                elements: dict
    state:
        description:
            - The desired state of the cluster network.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a cluster network
  stevefulme1.oci_cloud.oci_cluster_network:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-cluster-network"
    instance_pools:
      - instance_configuration_id: "ocid1.instanceconfiguration.oc1..example"
        size: 4
    placement_configuration:
      availability_domain: "Uocm:PHX-AD-1"
      primary_subnet_id: "ocid1.subnet.oc1..example"
    state: present

- name: Update a cluster network display name
  stevefulme1.oci_cloud.oci_cluster_network:
    cluster_network_id: "ocid1.clusternetwork.oc1..example"
    display_name: "renamed-cluster"
    state: present

- name: Delete a cluster network
  stevefulme1.oci_cloud.oci_cluster_network:
    cluster_network_id: "ocid1.clusternetwork.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the cluster network.
    returned: on success
    type: dict
    sample:
        id: "ocid1.clusternetwork.oc1..example"
        display_name: "my-cluster-network"
        lifecycle_state: "RUNNING"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import ComputeManagementClient
    from oci.core.models import (
        CreateClusterNetworkDetails,
        UpdateClusterNetworkDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciClusterNetwork(OciResourceBase):
    """Manage OCI Cluster Networks."""

    client_class = ComputeManagementClient if HAS_OCI_SDK else None

    def get_resource(self):
        cluster_network_id = self.module.params.get("cluster_network_id")
        if not cluster_network_id:
            return None
        try:
            return call_with_retry(
                self.client.get_cluster_network, cluster_network_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateClusterNetworkDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            instance_pools=self.module.params.get("instance_pools"),
            placement_configuration=self.module.params.get("placement_configuration"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.create_cluster_network, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_cluster_network,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateClusterNetworkDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_cluster_network, resource.id, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_cluster_network,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(self.client.terminate_cluster_network, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_cluster_network,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cluster_network_id=dict(type="str"),
        display_name=dict(type="str"),
        instance_pools=dict(type="list", elements="dict"),
        placement_configuration=dict(type="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciClusterNetwork(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
