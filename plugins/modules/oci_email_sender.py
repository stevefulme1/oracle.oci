# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI senders."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_email_sender
short_description: Manage OCI Senders
description:
    - Create, update, and delete senders in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new sender.
        type: str
    sender_id:
        description:
            - The OCID of the sender.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the sender.
        type: str
    email_address:
        description:
            - The email address of the sender.
        type: str
    state:
        description:
            - The desired state of the sender.
        type: str
        choices:
            - present
            - absent
        default: present
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a sender
  stevefulme1.oci_cloud.oci_email_sender:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-sender"
    state: present

- name: Delete a sender
  stevefulme1.oci_cloud.oci_email_sender:
    sender_id: "ocid1.sender.oc1..example"
    state: absent
"""

RETURN = r"""
sender:
    description: Details of the sender.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.sender.oc1..example"
        display_name: "my-sender"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.email import EmailClient
    from oci.email.models import CreateSenderDetails
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
    """Build module argument spec."""
    module_args = dict(
        compartment_id=dict(type="str"),
        sender_id=dict(type="str"),
        display_name=dict(type="str"),
        email_address=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get a sender by OCID."""
    try:
        response = call_with_retry(client.get_sender, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a sender by display name in a compartment."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_senders, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if getattr(item, "lifecycle_state", None) in DEAD_STATES:
                continue
            if display_name and getattr(item, "display_name", None) == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    """Create a new sender."""
    params = module.params
    create_details = CreateSenderDetails(
        compartment_id=params.get("compartment_id"),
        email_address=params.get("email_address"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_sender, create_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_sender, resource.id, target_states=READY_STATES,
        )
    return resource


def delete_resource(module, client, existing):
    """Delete a sender."""
    call_with_retry(client.delete_sender, existing.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_sender, existing.id, target_states=DEAD_STATES,
        )


def needs_update(params, existing):
    """Check if resource attributes differ from desired state."""
    updatable = []
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
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, EmailClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("sender_id"):
        existing = get_resource(client, params["sender_id"])
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
        module.exit_json(changed=True, sender=to_dict(resource))
        return

    module.exit_json(changed=False, sender=to_dict(existing))


if __name__ == "__main__":
    main()
