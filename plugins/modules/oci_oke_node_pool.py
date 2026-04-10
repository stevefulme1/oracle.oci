#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OKE node pools."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_oke_node_pool
short_description: Manage OKE node pools
description:
  - Create, update, and delete node pools in Oracle Kubernetes Engine (OKE).
  - Node pools are groups of worker nodes within an OKE cluster.
  - Uses C(oci.container_engine.ContainerEngineClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment for the node pool.
      - Required when creating a new node pool.
    type: str
  cluster_id:
    description:
      - The OCID of the cluster to add the node pool to.
      - Required when creating a new node pool.
    type: str
  name:
    description:
      - The name of the node pool.
      - Required when creating a new node pool.
    type: str
  node_shape:
    description:
      - The shape of the nodes in the pool (e.g. VM.Standard.E4.Flex).
      - Required when creating a new node pool.
    type: str
  node_image_id:
    description:
      - The OCID of the image to use for nodes.
      - Required when creating a new node pool.
    type: str
  node_shape_config:
    description:
      - Shape configuration details for flexible shapes.
    type: dict
    suboptions:
      ocpus:
        description: The number of OCPUs for each node.
        type: float
      memory_in_gbs:
        description: The amount of memory per node in GBs.
        type: float
  subnet_ids:
    description:
      - List of subnet OCIDs for node placement.
      - Required when creating a new node pool.
    type: list
    elements: str
  size:
    description:
      - The number of nodes in the node pool.
      - Required when creating a new node pool.
    type: int
  node_pool_id:
    description:
      - The OCID of the node pool. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the node pool.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an OKE node pool
  oracle.oci.oci_oke_node_pool:
    compartment_id: "ocid1.compartment.oc1..example"
    cluster_id: "ocid1.cluster.oc1.phx.example"
    name: "pool-1"
    node_shape: "VM.Standard.E4.Flex"
    node_image_id: "ocid1.image.oc1.phx.example"
    node_shape_config:
      ocpus: 2
      memory_in_gbs: 16
    subnet_ids:
      - "ocid1.subnet.oc1.phx.example"
    size: 3
    state: present

- name: Scale a node pool
  oracle.oci.oci_oke_node_pool:
    node_pool_id: "ocid1.nodepool.oc1.phx.example"
    size: 5
    state: present

- name: Delete a node pool
  oracle.oci.oci_oke_node_pool:
    node_pool_id: "ocid1.nodepool.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The node pool details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.nodepool.oc1.phx.example"
    name: "pool-1"
    lifecycle_state: "ACTIVE"
    node_shape: "VM.Standard.E4.Flex"
    cluster_id: "ocid1.cluster.oc1.phx.example"
    node_config_details:
      size: 3
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
    wait_for_work_request,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciOkeNodePool(OciResourceBase):
    """Manage OKE node pools."""

    def __init__(self, module):
        self.client_class = oci.container_engine.ContainerEngineClient
        super().__init__(module)

    def get_resource(self):
        node_pool_id = self.module.params.get("node_pool_id")
        if not node_pool_id:
            return None
        try:
            response = self.client.get_node_pool(node_pool_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_DELETED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _build_placement_configs(self):
        """Build node pool placement configurations from subnet_ids."""
        subnet_ids = self.module.params.get("subnet_ids") or []
        return [
            oci.container_engine.models.NodePoolPlacementConfigDetails(
                availability_domain=None,  # Let OCI distribute
                subnet_id=subnet_id,
            )
            for subnet_id in subnet_ids
        ]

    def create_resource(self):
        params = self.module.params

        # Build node config details with placement and size
        placement_configs = self._build_placement_configs()
        node_config = oci.container_engine.models.CreateNodePoolNodeConfigDetails(
            size=params["size"],
            placement_configs=placement_configs,
        )

        kwargs = dict(
            compartment_id=params["compartment_id"],
            cluster_id=params["cluster_id"],
            name=params["name"],
            node_shape=params["node_shape"],
            node_config_details=node_config,
        )

        # Set node source via image
        if params.get("node_image_id"):
            kwargs["node_source_details"] = oci.container_engine.models.NodeSourceViaImageDetails(
                image_id=params["node_image_id"],
            )

        if params.get("node_shape_config"):
            sc = params["node_shape_config"]
            kwargs["node_shape_config"] = oci.container_engine.models.CreateNodeShapeConfigDetails(
                ocpus=sc.get("ocpus"),
                memory_in_gbs=sc.get("memory_in_gbs"),
            )

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.container_engine.models.CreateNodePoolDetails(**kwargs)
        response = call_with_retry(self.client.create_node_pool, create_details)

        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wr = wait_for_work_request(self.module, self.client, work_request_id)
            node_pool_id = None
            for res in (wr.resources or []):
                if res.entity_type == "nodepool":
                    node_pool_id = res.identifier
                    break
            if node_pool_id:
                return self.client.get_node_pool(node_pool_id).data
        return None

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("name"):
            kwargs["name"] = params["name"]

        if params.get("node_shape"):
            kwargs["node_shape"] = params["node_shape"]

        if params.get("node_shape_config"):
            sc = params["node_shape_config"]
            kwargs["node_shape_config"] = oci.container_engine.models.UpdateNodeShapeConfigDetails(
                ocpus=sc.get("ocpus"),
                memory_in_gbs=sc.get("memory_in_gbs"),
            )

        # Update size via node_config_details
        if params.get("size") is not None:
            # Preserve existing placement configs
            existing_placements = []
            if resource.node_config_details and resource.node_config_details.placement_configs:
                for pc in resource.node_config_details.placement_configs:
                    existing_placements.append(
                        oci.container_engine.models.NodePoolPlacementConfigDetails(
                            availability_domain=pc.availability_domain,
                            subnet_id=pc.subnet_id,
                        )
                    )
            kwargs["node_config_details"] = oci.container_engine.models.UpdateNodePoolNodeConfigDetails(
                size=params["size"],
                placement_configs=existing_placements if existing_placements else None,
            )

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.container_engine.models.UpdateNodePoolDetails(**kwargs)
        response = call_with_retry(
            self.client.update_node_pool, resource.id, update_details,
        )

        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wait_for_work_request(self.module, self.client, work_request_id)
        return self.client.get_node_pool(resource.id).data

    def delete_resource(self, resource):
        response = call_with_retry(self.client.delete_node_pool, resource.id)
        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wait_for_work_request(self.module, self.client, work_request_id)

    def needs_update(self, resource):
        """Custom update check for node pool size."""
        if super().needs_update(resource):
            return True
        desired_size = self.module.params.get("size")
        if desired_size is not None and resource.node_config_details:
            if resource.node_config_details.size != desired_size:
                return True
        return False

    def _updatable_attributes(self):
        return ["name", "node_shape"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        cluster_id=dict(type="str"),
        name=dict(type="str"),
        node_shape=dict(type="str"),
        node_image_id=dict(type="str"),
        node_shape_config=dict(
            type="dict",
            options=dict(
                ocpus=dict(type="float"),
                memory_in_gbs=dict(type="float"),
            ),
        ),
        subnet_ids=dict(type="list", elements="str"),
        size=dict(type="int"),
        node_pool_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "cluster_id", "name", "node_shape", "subnet_ids", "size"), True),
            ("state", "absent", ("node_pool_id",)),
        ],
    )

    oci_np = OciOkeNodePool(module)
    oci_np.run()


if __name__ == "__main__":
    main()
