# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OKE clusters."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_oke_cluster
short_description: Manage OKE (Oracle Kubernetes Engine) clusters
description:
  - Create, update, and delete OKE clusters in Oracle Cloud Infrastructure.
  - Uses C(oci.container_engine.ContainerEngineClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the cluster in.
      - Required when creating a new cluster.
    type: str
  name:
    description:
      - The name of the cluster.
      - Required when creating a new cluster.
    type: str
  vcn_id:
    description:
      - The OCID of the VCN for the cluster.
      - Required when creating a new cluster.
    type: str
  kubernetes_version:
    description:
      - The Kubernetes version to deploy (e.g. v1.28.2).
      - Required when creating a new cluster.
    type: str
  cluster_id:
    description:
      - The OCID of the cluster. Required for update and delete operations.
    type: str
  options:
    description:
      - Optional configuration for the cluster.
    type: dict
    suboptions:
      service_lb_subnet_ids:
        description:
          - List of subnet OCIDs for Kubernetes service load balancers.
        type: list
        elements: str
      add_ons:
        description:
          - Configurable cluster add-ons.
        type: dict
        suboptions:
          is_kubernetes_dashboard_enabled:
            description: Whether the Kubernetes dashboard is enabled.
            type: bool
          is_tiller_enabled:
            description: Whether Tiller is enabled.
            type: bool
      kubernetes_network_config:
        description:
          - Network configuration for Kubernetes.
        type: dict
        suboptions:
          pods_cidr:
            description: CIDR block for Kubernetes pods.
            type: str
          services_cidr:
            description: CIDR block for Kubernetes services.
            type: str
  state:
    description:
      - The desired state of the cluster.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an OKE cluster
  oracle.oci.oci_oke_cluster:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-k8s-cluster"
    vcn_id: "ocid1.vcn.oc1.phx.example"
    kubernetes_version: "v1.28.2"
    options:
      service_lb_subnet_ids:
        - "ocid1.subnet.oc1.phx.example"
      kubernetes_network_config:
        pods_cidr: "10.244.0.0/16"
        services_cidr: "10.96.0.0/16"
    state: present

- name: Update cluster Kubernetes version
  oracle.oci.oci_oke_cluster:
    cluster_id: "ocid1.cluster.oc1.phx.example"
    kubernetes_version: "v1.29.1"
    state: present

- name: Delete an OKE cluster
  oracle.oci.oci_oke_cluster:
    cluster_id: "ocid1.cluster.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The cluster details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.cluster.oc1.phx.example"
    name: "my-k8s-cluster"
    lifecycle_state: "ACTIVE"
    kubernetes_version: "v1.28.2"
    vcn_id: "ocid1.vcn.oc1.phx.example"
    compartment_id: "ocid1.compartment.oc1..example"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_DELETED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_work_request,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciOkeCluster(OciResourceBase):
    """Manage OKE clusters."""

    def __init__(self, module):
        self.client_class = oci.container_engine.ContainerEngineClient
        super().__init__(module)

    def get_resource(self):
        cluster_id = self.module.params.get("cluster_id")
        if not cluster_id:
            return None
        try:
            response = self.client.get_cluster(cluster_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_DELETED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _build_cluster_options(self):
        """Build cluster options from module params."""
        opts = self.module.params.get("options")
        if not opts:
            return None

        kwargs = {}

        if opts.get("service_lb_subnet_ids"):
            kwargs["service_lb_subnet_ids"] = opts["service_lb_subnet_ids"]

        if opts.get("add_ons"):
            addons = opts["add_ons"]
            kwargs["add_ons"] = oci.container_engine.models.AddOnOptions(
                is_kubernetes_dashboard_enabled=addons.get("is_kubernetes_dashboard_enabled", False),
                is_tiller_enabled=addons.get("is_tiller_enabled", False),
            )

        if opts.get("kubernetes_network_config"):
            knc = opts["kubernetes_network_config"]
            kwargs["kubernetes_network_config"] = oci.container_engine.models.KubernetesNetworkConfig(
                pods_cidr=knc.get("pods_cidr"),
                services_cidr=knc.get("services_cidr"),
            )

        return oci.container_engine.models.ClusterCreateOptions(**kwargs)

    def create_resource(self):
        params = self.module.params
        kwargs = dict(
            compartment_id=params["compartment_id"],
            name=params["name"],
            vcn_id=params["vcn_id"],
            kubernetes_version=params["kubernetes_version"],
        )

        cluster_options = self._build_cluster_options()
        if cluster_options:
            kwargs["options"] = cluster_options

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.container_engine.models.CreateClusterDetails(**kwargs)
        response = call_with_retry(self.client.create_cluster, create_details)

        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wr = wait_for_work_request(self.module, self.client, work_request_id)
            # Extract cluster ID from work request resources
            cluster_id = None
            for res in (wr.resources or []):
                if res.entity_type == "cluster":
                    cluster_id = res.identifier
                    break
            if cluster_id:
                return self.client.get_cluster(cluster_id).data
        return None

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("name"):
            kwargs["name"] = params["name"]
        if params.get("kubernetes_version"):
            kwargs["kubernetes_version"] = params["kubernetes_version"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.container_engine.models.UpdateClusterDetails(**kwargs)
        response = call_with_retry(
            self.client.update_cluster, resource.id, update_details,
        )

        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wait_for_work_request(self.module, self.client, work_request_id)
        return self.client.get_cluster(resource.id).data

    def delete_resource(self, resource):
        response = call_with_retry(self.client.delete_cluster, resource.id)
        work_request_id = response.headers.get("opc-work-request-id")
        if self.module.params.get("wait", True) and work_request_id:
            wait_for_work_request(self.module, self.client, work_request_id)

    def _updatable_attributes(self):
        return ["name", "kubernetes_version"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        vcn_id=dict(type="str"),
        kubernetes_version=dict(type="str"),
        cluster_id=dict(type="str"),
        options=dict(
            type="dict",
            options=dict(
                service_lb_subnet_ids=dict(type="list", elements="str"),
                add_ons=dict(
                    type="dict",
                    options=dict(
                        is_kubernetes_dashboard_enabled=dict(type="bool"),
                        is_tiller_enabled=dict(type="bool"),
                    ),
                ),
                kubernetes_network_config=dict(
                    type="dict",
                    options=dict(
                        pods_cidr=dict(type="str"),
                        services_cidr=dict(type="str"),
                    ),
                ),
            ),
        ),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "name", "vcn_id", "kubernetes_version"), True),
            ("state", "absent", ("cluster_id",)),
        ],
    )

    oci_cluster = OciOkeCluster(module)
    oci_cluster.run()


if __name__ == "__main__":
    main()
