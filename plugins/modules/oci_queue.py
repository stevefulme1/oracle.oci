# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Queues."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_queue
short_description: Manage Queues in OCI
description:
    - Create, update, and delete Queues in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.queue.QueueAdminClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the queue.
            - Required when creating a new queue.
        type: str
    queue_id:
        description:
            - The OCID of an existing queue.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the queue.
            - Required when creating a new queue.
        type: str
    retention_in_seconds:
        description:
            - The retention period for messages in seconds.
        type: int
        default: 3600
    visibility_in_seconds:
        description:
            - The default visibility timeout for messages in seconds.
        type: int
        default: 30
    timeout_in_seconds:
        description:
            - The default polling timeout in seconds.
        type: int
        default: 30
    dead_letter_queue_delivery_count:
        description:
            - Number of delivery attempts before moving to the dead letter queue.
        type: int
    state:
        description:
            - The desired state of the queue.
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
- name: Create a queue
  stevefulme1.oci_cloud.oci_queue:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-queue"
    retention_in_seconds: 3600
    state: present

- name: Delete a queue
  stevefulme1.oci_cloud.oci_queue:
    queue_id: "ocid1.queue.oc1..example"
    state: absent
"""

RETURN = r"""
queue:
    description: Details of the queue.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.queue.oc1..example"
        display_name: "my-queue"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.queue import QueueAdminClient
    from oci.queue.models import (
        CreateQueueDetails,
        UpdateQueueDetails,
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
    module_args = dict(
        compartment_id=dict(type="str"),
        queue_id=dict(type="str"),
        display_name=dict(type="str"),
        retention_in_seconds=dict(type="int", default=3600),
        visibility_in_seconds=dict(type="int", default=30),
        timeout_in_seconds=dict(type="int", default=30),
        dead_letter_queue_delivery_count=dict(type="int"),
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
        response = call_with_retry(client.get_queue, resource_id)
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
            client.list_queues, compartment_id=compartment_id,
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
    create_details = CreateQueueDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        retention_in_seconds=params.get("retention_in_seconds"),
        visibility_in_seconds=params.get("visibility_in_seconds"),
        timeout_in_seconds=params.get("timeout_in_seconds"),
        dead_letter_queue_delivery_count=params.get("dead_letter_queue_delivery_count"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_queue, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_queue, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateQueueDetails(
        display_name=params.get("display_name"),
        visibility_in_seconds=params.get("visibility_in_seconds"),
        timeout_in_seconds=params.get("timeout_in_seconds"),
        dead_letter_queue_delivery_count=params.get("dead_letter_queue_delivery_count"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_queue, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_queue, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_queue, existing.id)
    wait_for_resource(
        module, client.get_queue, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "visibility_in_seconds", "timeout_in_seconds",
                 "dead_letter_queue_delivery_count"]
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
            ("state", "present", ("compartment_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, QueueAdminClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("queue_id"):
        existing = get_resource(client, params["queue_id"])
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
        for req in ("compartment_id", "display_name"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a queue.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, queue=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, queue=to_dict(resource))
        return

    module.exit_json(changed=False, queue=to_dict(existing))


if __name__ == "__main__":
    main()
