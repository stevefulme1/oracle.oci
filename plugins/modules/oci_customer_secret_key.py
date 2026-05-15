# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI customer secret keys."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_customer_secret_key
short_description: Manage OCI customer secret keys
description:
  - Create, update, and delete S3-compatible customer secret keys for OCI IAM users.
  - Customer secret keys are used for S3-compatible API access to Object Storage.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  user_id:
    description:
      - The OCID of the user who owns the secret key.
      - Required for all operations.
    type: str
    required: true
  customer_secret_key_id:
    description:
      - The OCID of the customer secret key.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the secret key.
      - Required when creating a new secret key.
    type: str
  state:
    description:
      - The desired state of the customer secret key.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a customer secret key
  stevefulme1.oci_cloud.oci_customer_secret_key:
    user_id: "ocid1.user.oc1..example"
    display_name: "s3-access-key"
    state: present

- name: Update a customer secret key
  stevefulme1.oci_cloud.oci_customer_secret_key:
    user_id: "ocid1.user.oc1..example"
    customer_secret_key_id: "ocid1.credential.oc1..example"
    display_name: "renamed-key"
    state: present

- name: Delete a customer secret key
  stevefulme1.oci_cloud.oci_customer_secret_key:
    user_id: "ocid1.user.oc1..example"
    customer_secret_key_id: "ocid1.credential.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The customer secret key details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the secret key.
      type: str
    user_id:
      description: The OCID of the user.
      type: str
    display_name:
      description: The display name of the secret key.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the key was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateCustomerSecretKeyDetails,
        UpdateCustomerSecretKeyDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_resource(client, user_id, key_id):
    """Get a customer secret key by listing user keys and matching ID."""
    if not key_id:
        return None
    try:
        keys = call_with_retry(client.list_customer_secret_keys, user_id).data
        for key in keys:
            if key.id == key_id and key.lifecycle_state not in ("DELETED", "TERMINATED"):
                return key
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise
    return None


def find_resource(client, user_id, display_name):
    """Find a customer secret key by user and display name."""
    if not user_id or not display_name:
        return None
    keys = call_with_retry(client.list_customer_secret_keys, user_id).data
    for key in keys:
        if key.display_name == display_name and key.lifecycle_state not in ("DELETED", "TERMINATED"):
            return key
    return None


def create_resource(module, client):
    """Create a new customer secret key."""
    details = CreateCustomerSecretKeyDetails(
        display_name=module.params["display_name"],
    )
    response = call_with_retry(
        client.create_customer_secret_key, details, module.params["user_id"]
    )
    return response.data


def update_resource(module, client, resource):
    """Update an existing customer secret key."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            kwargs["display_name"] = module.params["display_name"]

    if not kwargs:
        return resource

    details = UpdateCustomerSecretKeyDetails(**kwargs)
    response = call_with_retry(
        client.update_customer_secret_key, module.params["user_id"], resource.id, details
    )
    return response.data


def delete_resource(module, client, resource):
    """Delete a customer secret key."""
    call_with_retry(
        client.delete_customer_secret_key, module.params["user_id"], resource.id
    )


def needs_update(module, resource):
    """Check if the customer secret key needs updating."""
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            return True
    return False


def main():
    module_args = dict(
        user_id=dict(type="str", required=True),
        customer_secret_key_id=dict(type="str"),
        display_name=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["customer_secret_key_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    user_id = module.params["user_id"]
    key_id = module.params.get("customer_secret_key_id")

    resource = None
    if key_id:
        resource = get_resource(client, user_id, key_id)
    elif module.params.get("display_name"):
        resource = find_resource(client, user_id, module.params["display_name"])

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, resource)
        module.exit_json(changed=True)
        return

    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
