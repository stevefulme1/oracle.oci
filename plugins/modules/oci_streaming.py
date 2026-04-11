# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Streaming."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_streaming
short_description: Manage Streams in OCI
description:
    - Create, update, and delete Streams in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.streaming.StreamAdminClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the stream.
            - Required when creating a new stream.
        type: str
    stream_id:
        description:
            - The OCID of an existing stream.
            - Required for update and delete operations.
        type: str
    name:
        description:
            - The name of the stream.
            - Required when creating a new stream.
        type: str
    partitions:
        description:
            - The number of partitions in the stream.
            - Required when creating a new stream.
        type: int
    retention_in_hours:
        description:
            - The retention period of the stream in hours.
        type: int
        default: 24
    stream_pool_id:
        description:
            - The OCID of the stream pool.
        type: str
    state:
        description:
            - The desired state of the stream.
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
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a stream
  oracle.oci.oci_streaming:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-stream"
    partitions: 1
    retention_in_hours: 24
    state: present

- name: Delete a stream
  oracle.oci.oci_streaming:
    stream_id: "ocid1.stream.oc1..example"
    state: absent
"""

RETURN = r"""
stream:
    description: Details of the stream.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.stream.oc1..example"
        name: "my-stream"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.streaming import StreamAdminClient
    from oci.streaming.models import (
        CreateStreamDetails,
        UpdateStreamDetails,
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
        stream_id=dict(type="str"),
        name=dict(type="str"),
        partitions=dict(type="int"),
        retention_in_hours=dict(type="int", default=24),
        stream_pool_id=dict(type="str"),
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
        response = call_with_retry(client.get_stream, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_streams, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if name and item.name == name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateStreamDetails(
        compartment_id=params["compartment_id"],
        name=params["name"],
        partitions=params["partitions"],
        retention_in_hours=params.get("retention_in_hours"),
        stream_pool_id=params.get("stream_pool_id"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_stream, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_stream, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateStreamDetails(
        stream_pool_id=params.get("stream_pool_id"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_stream, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_stream, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_stream, existing.id)
    wait_for_resource(
        module, client.get_stream, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["stream_pool_id"]
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
            ("state", "present", ("compartment_id", "name", "partitions"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, StreamAdminClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("stream_id"):
        existing = get_resource(client, params["stream_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("compartment_id", "name", "partitions"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a stream.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, stream=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, stream=to_dict(resource))
        return

    module.exit_json(changed=False, stream=to_dict(existing))


if __name__ == "__main__":
    main()
