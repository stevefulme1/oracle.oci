# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Email Delivery Senders."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_email_delivery
short_description: Manage Email Delivery Senders in OCI
description:
    - Create and delete Email Delivery Senders in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.email.EmailClient).
    - This is a create/delete only resource; update is not supported.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the sender.
            - Required when creating a new sender.
        type: str
    sender_id:
        description:
            - The OCID of an existing sender.
            - Required for delete operations.
        type: str
    email_address:
        description:
            - The email address of the sender.
            - Required when creating a new sender.
        type: str
    state:
        description:
            - The desired state of the email sender.
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
- name: Create an email sender
  stevefulme1.oci_cloud.oci_email_delivery:
    compartment_id: "ocid1.compartment.oc1..example"
    email_address: "noreply@example.com"
    state: present

- name: Delete an email sender
  stevefulme1.oci_cloud.oci_email_delivery:
    sender_id: "ocid1.emailsender.oc1..example"
    state: absent
"""

RETURN = r"""
email_sender:
    description: Details of the email sender.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.emailsender.oc1..example"
        email_address: "noreply@example.com"
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
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        sender_id=dict(type="str"),
        email_address=dict(type="str"),
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
        response = call_with_retry(client.get_sender, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, email_address):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_senders, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if email_address and item.email_address == email_address:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateSenderDetails(
        compartment_id=params["compartment_id"],
        email_address=params["email_address"],
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_sender, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_sender, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_sender, existing.id)
    wait_for_resource(
        module, client.get_sender, existing.id, target_states=DEAD_STATES,
    )


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "email_address"), True),
        ],
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
        existing = find_resource(client, params["compartment_id"], params.get("email_address"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("compartment_id", "email_address"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an email sender.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, email_sender=to_dict(resource))
        return

    # No update supported for email senders
    module.exit_json(changed=False, email_sender=to_dict(existing))


if __name__ == "__main__":
    main()
