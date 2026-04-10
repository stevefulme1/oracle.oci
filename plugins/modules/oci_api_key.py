# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI API signing keys."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_api_key
short_description: Manage OCI API signing keys
description:
    - Upload and delete API signing keys for OCI IAM users.
    - API keys are used for authenticating API requests with the OCI SDK and CLI.
    - Note that API keys cannot be updated; to change a key, delete and re-upload.
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    user_id:
        description:
            - The OCID of the user to manage the API key for.
            - Required for all operations.
        type: str
        required: true
    key_value:
        description:
            - The public key in PEM format to upload.
            - Required when I(state=present).
        type: str
    api_key_id:
        description:
            - The key's fingerprint (e.g. 12:34:56:78:...).
            - Required when I(state=absent) to identify the key to delete.
        type: str
    state:
        description:
            - The desired state of the API key.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Upload an API signing key
  oracle.oci.oci_api_key:
    user_id: "ocid1.user.oc1..example"
    key_value: |
      -----BEGIN PUBLIC KEY-----
      MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
      -----END PUBLIC KEY-----
    state: present

- name: Delete an API signing key by fingerprint
  oracle.oci.oci_api_key:
    user_id: "ocid1.user.oc1..example"
    api_key_id: "12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef"
    state: absent
"""

RETURN = r"""
resource:
    description: The API key details.
    returned: on success
    type: dict
    contains:
        key_id:
            description: The key's fingerprint identifier.
            type: str
        key_value:
            description: The public key value.
            type: str
        fingerprint:
            description: The fingerprint of the key.
            type: str
        user_id:
            description: The OCID of the user the key belongs to.
            type: str
        time_created:
            description: The date and time the key was uploaded.
            type: str
        lifecycle_state:
            description: The current lifecycle state of the API key.
            type: str
"""

try:
    from oci.identity import IdentityClient
    from oci.identity.models import CreateApiKeyDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry


def get_module_args():
    module_args = dict(
        user_id=dict(type="str", required=True),
        key_value=dict(type="str", no_log=False),
        api_key_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_key(client, module):
    """Find an existing API key by fingerprint or key_value match."""
    user_id = module.params["user_id"]
    api_key_id = module.params.get("api_key_id")
    key_value = module.params.get("key_value")

    try:
        keys = call_with_retry(client.list_api_keys, user_id).data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise

    if api_key_id:
        for key in keys:
            if key.fingerprint == api_key_id and key.lifecycle_state == LIFECYCLE_ACTIVE:
                return key

    if key_value:
        # Normalize whitespace for comparison
        normalized = key_value.strip()
        for key in keys:
            if key.key_value and key.key_value.strip() == normalized and key.lifecycle_state == LIFECYCLE_ACTIVE:
                return key

    return None


def create_resource(client, module):
    """Upload a new API key."""
    user_id = module.params["user_id"]
    key_value = module.params["key_value"]

    details = CreateApiKeyDetails(key=key_value)
    resource = call_with_retry(client.upload_api_key, user_id, details).data
    return resource


def delete_resource(client, module, resource):
    """Delete an API key."""
    user_id = module.params["user_id"]
    call_with_retry(client.delete_api_key, user_id, resource.fingerprint)


def to_dict(resource):
    """Convert an OCI resource to a plain dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        result[key] = value
    return result


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["key_value"]),
            ("state", "absent", ["api_key_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]

    resource = get_existing_key(client, module)

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(client, module, resource)
        module.exit_json(changed=True)
        return

    # state == present
    if resource is not None:
        # API keys are immutable; if it already exists, nothing to change
        module.exit_json(changed=False, resource=to_dict(resource))
        return

    if module.check_mode:
        module.exit_json(changed=True)

    resource = create_resource(client, module)
    module.exit_json(changed=True, resource=to_dict(resource))


if __name__ == "__main__":
    main()
