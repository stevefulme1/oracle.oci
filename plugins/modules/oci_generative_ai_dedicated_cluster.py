# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Generative AI Dedicated AI Clusters."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_generative_ai_dedicated_cluster
short_description: Manage Generative AI Dedicated AI Clusters in OCI
description:
    - Create, update, and delete Generative AI Dedicated AI Clusters in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.generative_ai.GenerativeAiClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the dedicated AI cluster.
            - Required when creating a new cluster.
        type: str
    dedicated_ai_cluster_id:
        description:
            - The OCID of an existing dedicated AI cluster.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the dedicated AI cluster.
        type: str
    description:
        description:
            - A short description of the cluster.
        type: str
    type:
        description:
            - The type of dedicated AI cluster (HOSTING or FINE_TUNING).
            - Required when creating a new cluster.
        type: str
        choices:
            - HOSTING
            - FINE_TUNING
    unit_count:
        description:
            - The number of dedicated units in the cluster.
            - Required when creating a new cluster.
        type: int
    unit_shape:
        description:
            - The shape of the dedicated units (e.g., LARGE_COHERE, SMALL_COHERE).
            - Required when creating a new cluster.
        type: str
    state:
        description:
            - The desired state of the dedicated AI cluster.
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
        default: 1800
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a Generative AI dedicated AI cluster
  oracle.oci.oci_generative_ai_dedicated_cluster:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-hosting-cluster"
    type: "HOSTING"
    unit_count: 1
    unit_shape: "LARGE_COHERE"
    state: present

- name: Update a Generative AI dedicated AI cluster
  oracle.oci.oci_generative_ai_dedicated_cluster:
    dedicated_ai_cluster_id: "ocid1.generativeaidedicatedaicluster.oc1..example"
    display_name: "my-hosting-cluster-v2"
    state: present

- name: Delete a Generative AI dedicated AI cluster
  oracle.oci.oci_generative_ai_dedicated_cluster:
    dedicated_ai_cluster_id: "ocid1.generativeaidedicatedaicluster.oc1..example"
    state: absent
"""

RETURN = r"""
generative_ai_dedicated_cluster:
    description: Details of the Generative AI dedicated AI cluster.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.generativeaidedicatedaicluster.oc1..example"
        display_name: "my-hosting-cluster"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.generative_ai import GenerativeAiClient
    from oci.generative_ai.models import (
        CreateDedicatedAiClusterDetails,
        UpdateDedicatedAiClusterDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        dedicated_ai_cluster_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        type=dict(type="str", choices=["HOSTING", "FINE_TUNING"]),
        unit_count=dict(type="int"),
        unit_shape=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
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


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_dedicated_ai_cluster, resource_id)
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
            client.list_dedicated_ai_clusters, compartment_id=compartment_id,
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
    create_details = CreateDedicatedAiClusterDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        description=params.get("description"),
        type=params["type"],
        unit_count=params["unit_count"],
        unit_shape=params["unit_shape"],
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_dedicated_ai_cluster, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_dedicated_ai_cluster, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_kwargs = dict(
        display_name=params.get("display_name"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    if params.get("unit_count") is not None:
        update_kwargs["unit_count"] = params["unit_count"]
    update_details = UpdateDedicatedAiClusterDetails(**update_kwargs)
    response = call_with_retry(client.update_dedicated_ai_cluster, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_dedicated_ai_cluster, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_dedicated_ai_cluster, existing.id)
    wait_for_resource(
        module, client.get_dedicated_ai_cluster, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "description", "unit_count"]
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
            ("state", "present", ("compartment_id", "type", "unit_count", "unit_shape"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, GenerativeAiClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("dedicated_ai_cluster_id"):
        existing = get_resource(client, params["dedicated_ai_cluster_id"])
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
        for req in ("compartment_id", "type", "unit_count", "unit_shape"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a Generative AI dedicated cluster.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, generative_ai_dedicated_cluster=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, generative_ai_dedicated_cluster=to_dict(resource))
        return

    module.exit_json(changed=False, generative_ai_dedicated_cluster=to_dict(existing))


if __name__ == "__main__":
    main()
