# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Cache (Redis) Clusters."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_redis_cluster
short_description: Manage OCI Cache (Redis) Clusters in OCI
description:
    - Create, update, and delete OCI Cache (Redis) Clusters in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.redis.RedisClusterClient).
version_added: "2.1.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the Redis cluster.
            - Required when creating a new cluster.
        type: str
    redis_cluster_id:
        description:
            - The OCID of an existing Redis cluster.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the Redis cluster.
        type: str
    subnet_id:
        description:
            - The OCID of the subnet for the Redis cluster.
            - Required when creating a new cluster.
        type: str
    node_count:
        description:
            - The number of nodes in the Redis cluster.
        type: int
    node_memory_in_gbs:
        description:
            - The amount of memory per node in GBs.
        type: float
    software_version:
        description:
            - The Redis software version for the cluster.
        type: str
    state:
        description:
            - The desired state of the Redis cluster.
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
- name: Create a Redis cluster
  stevefulme1.oci_cloud.oci_redis_cluster:
    compartment_id: "ocid1.compartment.oc1..example"
    subnet_id: "ocid1.subnet.oc1..example"
    display_name: "my-redis-cluster"
    node_count: 3
    node_memory_in_gbs: 8
    software_version: "V7_0_5"
    state: present

- name: Delete a Redis cluster
  stevefulme1.oci_cloud.oci_redis_cluster:
    redis_cluster_id: "ocid1.rediscluster.oc1..example"
    state: absent
"""

RETURN = r"""
redis_cluster:
    description: Details of the Redis cluster.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.rediscluster.oc1..example"
        display_name: "my-redis-cluster"
        lifecycle_state: "ACTIVE"
        node_count: 3
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.redis import RedisClusterClient
    from oci.redis.models import (
        CreateRedisClusterDetails,
        UpdateRedisClusterDetails,
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
    module_args = dict(
        compartment_id=dict(type="str"),
        redis_cluster_id=dict(type="str"),
        display_name=dict(type="str"),
        subnet_id=dict(type="str"),
        node_count=dict(type="int"),
        node_memory_in_gbs=dict(type="float"),
        software_version=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_redis_cluster, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_redis_clusters, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateRedisClusterDetails(
        compartment_id=params["compartment_id"],
        subnet_id=params["subnet_id"],
        display_name=params.get("display_name"),
        node_count=params.get("node_count"),
        node_memory_in_gbs=params.get("node_memory_in_gbs"),
        software_version=params.get("software_version"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_redis_cluster, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_redis_cluster, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateRedisClusterDetails(
        display_name=params.get("display_name"),
        node_count=params.get("node_count"),
        node_memory_in_gbs=params.get("node_memory_in_gbs"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_redis_cluster, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_redis_cluster, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_redis_cluster, existing.id)
    wait_for_resource(
        module, client.get_redis_cluster, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "node_count", "node_memory_in_gbs"]
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
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", (
                "compartment_id", "subnet_id", "node_count",
                "node_memory_in_gbs", "software_version",
            ), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, RedisClusterClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("redis_cluster_id"):
        existing = get_resource(client, params["redis_cluster_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("display_name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, redis_cluster=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, redis_cluster=to_dict(resource))
        return

    module.exit_json(changed=False, redis_cluster=to_dict(existing))


if __name__ == "__main__":
    main()
