# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI user auth tokens."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_auth_token
short_description: Manage OCI user auth tokens
description:
  - Create, update, and delete auth tokens for OCI IAM users.
  - Auth tokens are used to authenticate with third-party APIs compatible
    with Oracle Cloud Infrastructure signatures.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  user_id:
    description:
      - The OCID of the user who owns the auth token.
      - Required for all operations.
    type: str
    required: true
  auth_token_id:
    description:
      - The OCID of the auth token.
      - Required for update and delete operations.
    type: str
  description:
    description:
      - A description of the auth token.
      - Required when creating a new auth token.
    type: str
  state:
    description:
      - The desired state of the auth token.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an auth token
  oracle.oci.oci_auth_token:
    user_id: "ocid1.user.oc1..example"
    description: "Token for API access"
    state: present

- name: Update an auth token description
  oracle.oci.oci_auth_token:
    user_id: "ocid1.user.oc1..example"
    auth_token_id: "ocid1.credential.oc1..example"
    description: "Updated token description"
    state: present

- name: Delete an auth token
  oracle.oci.oci_auth_token:
    user_id: "ocid1.user.oc1..example"
    auth_token_id: "ocid1.credential.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The auth token details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the auth token.
      type: str
    user_id:
      description: The OCID of the user.
      type: str
    description:
      description: The description of the auth token.
      type: str
    token:
      description: The token value (only returned on create).
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the token was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateAuthTokenDetails,
        UpdateAuthTokenDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource to a serializable dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        result[key] = value
    return result


def get_resource(client, user_id, auth_token_id):
    """Get an auth token by listing user tokens and matching ID."""
    if not auth_token_id:
        return None
    try:
        tokens = call_with_retry(client.list_auth_tokens, user_id).data
        for token in tokens:
            if token.id == auth_token_id and token.lifecycle_state not in ("DELETED", "TERMINATED"):
                return token
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise
    return None


def find_resource(client, user_id, description):
    """Find an auth token by user and description."""
    if not user_id or not description:
        return None
    tokens = call_with_retry(client.list_auth_tokens, user_id).data
    for token in tokens:
        if token.description == description and token.lifecycle_state not in ("DELETED", "TERMINATED"):
            return token
    return None


def create_resource(module, client):
    """Create a new auth token."""
    details = CreateAuthTokenDetails(
        description=module.params["description"],
    )
    response = call_with_retry(
        client.create_auth_token, details, module.params["user_id"]
    )
    return response.data


def update_resource(module, client, resource):
    """Update an existing auth token."""
    kwargs = {}
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            kwargs["description"] = module.params["description"]

    if not kwargs:
        return resource

    details = UpdateAuthTokenDetails(**kwargs)
    response = call_with_retry(
        client.update_auth_token, module.params["user_id"], resource.id, details
    )
    return response.data


def delete_resource(module, client, resource):
    """Delete an auth token."""
    call_with_retry(
        client.delete_auth_token, module.params["user_id"], resource.id
    )


def needs_update(module, resource):
    """Check if the auth token needs updating."""
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            return True
    return False


def main():
    module_args = dict(
        user_id=dict(type="str", required=True),
        auth_token_id=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["auth_token_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    user_id = module.params["user_id"]
    auth_token_id = module.params.get("auth_token_id")

    resource = None
    if auth_token_id:
        resource = get_resource(client, user_id, auth_token_id)
    elif module.params.get("description"):
        resource = find_resource(client, user_id, module.params["description"])

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
