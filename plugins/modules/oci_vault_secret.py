# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Vault secrets."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_vault_secret
short_description: Manage secrets in OCI Vault
description:
    - Create, update, and delete secrets in Oracle Cloud Infrastructure Vault.
    - Secret content is provided as a base64-encoded string.
    - Deletion schedules the secret for deletion rather than immediately removing it.
    - Uses the OCI Python SDK C(oci.vault.VaultsClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment where the secret resides.
            - Required when creating a new secret.
        type: str
    vault_id:
        description:
            - The OCID of the vault where the secret will be stored.
            - Required when creating a new secret.
        type: str
    key_id:
        description:
            - The OCID of the master encryption key used to encrypt the secret.
            - Required when creating a new secret.
        type: str
    secret_name:
        description:
            - A user-friendly name for the secret.
            - Used to find an existing secret when I(secret_id) is not provided.
            - Required when creating a new secret.
        type: str
    description:
        description:
            - A brief description of the secret.
        type: str
    secret_content:
        description:
            - The content of the secret.
            - This is a dictionary with C(content_type) and C(content) keys.
            - C(content_type) should be C(BASE64).
            - C(content) is the base64-encoded secret value.
        type: dict
        suboptions:
            content_type:
                description:
                    - The content type of the secret. Must be C(BASE64).
                type: str
                required: true
                choices:
                    - BASE64
            content:
                description:
                    - The base64-encoded secret content.
                type: str
                required: true
    secret_id:
        description:
            - The OCID of an existing secret.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the secret.
            - C(present) will create or update the secret.
            - C(absent) will schedule the secret for deletion.
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
- name: Create a vault secret
  oracle.oci.oci_vault_secret:
    compartment_id: "ocid1.compartment.oc1..example"
    vault_id: "ocid1.vault.oc1..example"
    key_id: "ocid1.key.oc1..example"
    secret_name: "my-db-password"
    description: "Database password for production"
    secret_content:
      content_type: BASE64
      content: "cGFzc3dvcmQxMjM="
    state: present

- name: Update an existing secret with new content
  oracle.oci.oci_vault_secret:
    secret_id: "ocid1.vaultsecret.oc1..example"
    secret_content:
      content_type: BASE64
      content: "bmV3cGFzc3dvcmQ0NTY="
    state: present

- name: Delete (schedule deletion of) a secret
  oracle.oci.oci_vault_secret:
    secret_id: "ocid1.vaultsecret.oc1..example"
    state: absent
"""

RETURN = r"""
secret:
    description: Details of the vault secret.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.vaultsecret.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vault_id: "ocid1.vault.oc1..example"
        key_id: "ocid1.key.oc1..example"
        secret_name: "my-db-password"
        lifecycle_state: "ACTIVE"
        description: "Database password for production"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.vault import VaultsClient
    from oci.vault.models import (
        Base64SecretContentDetails,
        CreateSecretDetails,
        ScheduleSecretDeletionDetails,
        UpdateSecretDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

# Vault secret active states
SECRET_ACTIVE_STATES = frozenset({"ACTIVE"})
SECRET_DELETED_STATES = frozenset({"PENDING_DELETION", "DELETED", "CANCELLING_DELETION"})


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        vault_id=dict(type="str"),
        key_id=dict(type="str"),
        secret_name=dict(type="str"),
        description=dict(type="str"),
        secret_content=dict(
            type="dict",
            no_log=True,
            options=dict(
                content_type=dict(type="str", required=True, choices=["BASE64"]),
                content=dict(type="str", required=True, no_log=True),
            ),
        ),
        secret_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    """Convert OCI SDK object to a serializable dict."""
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


def get_secret(client, secret_id):
    """Get an existing secret by OCID."""
    try:
        response = call_with_retry(client.get_secret, secret_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_secret_by_name(client, compartment_id, vault_id, secret_name):
    """Find a secret by name within a compartment and vault."""
    if not compartment_id or not secret_name:
        return None
    try:
        response = call_with_retry(
            client.list_secrets,
            compartment_id=compartment_id,
            vault_id=vault_id,
            name=secret_name,
        )
        for secret in response.data:
            if secret.lifecycle_state in SECRET_DELETED_STATES:
                continue
            if secret.secret_name == secret_name:
                return get_secret(client, secret.id)
    except ServiceError:
        pass
    return None


def build_secret_content(secret_content_param):
    """Build the SecretContentDetails from the module parameter."""
    if not secret_content_param:
        return None
    return Base64SecretContentDetails(
        content=secret_content_param["content"],
    )


def create_secret(module, client):
    """Create a new vault secret."""
    params = module.params

    create_details = CreateSecretDetails(
        compartment_id=params["compartment_id"],
        vault_id=params["vault_id"],
        key_id=params["key_id"],
        secret_name=params["secret_name"],
        description=params.get("description"),
        secret_content=build_secret_content(params.get("secret_content")),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_secret, create_details)
    secret = response.data

    secret = wait_for_resource(
        module,
        client.get_secret,
        secret.id,
        target_states=SECRET_ACTIVE_STATES,
    )
    return secret


def update_secret(module, client, existing):
    """Update an existing vault secret with new content."""
    params = module.params

    update_details = UpdateSecretDetails(
        description=params.get("description"),
        secret_content=build_secret_content(params.get("secret_content")),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_secret,
        existing.id,
        update_details,
    )
    secret = response.data

    secret = wait_for_resource(
        module,
        client.get_secret,
        secret.id,
        target_states=SECRET_ACTIVE_STATES,
    )
    return secret


def delete_secret(module, client, existing):
    """Schedule a secret for deletion."""
    deletion_details = ScheduleSecretDeletionDetails()

    call_with_retry(
        client.schedule_secret_deletion,
        existing.id,
        deletion_details,
    )

    wait_for_resource(
        module,
        client.get_secret,
        existing.id,
        target_states=SECRET_DELETED_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing secret differs from desired state."""
    if params.get("description") is not None:
        if getattr(existing, "description", None) != params["description"]:
            return True
    # Secret content is always considered an update since we cannot read back
    # the actual content to compare
    if params.get("secret_content"):
        return True
    # Check tags
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "vault_id", "key_id", "secret_name"), True),
            ("state", "absent", ("secret_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, VaultsClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("secret_id"):
        existing = get_secret(client, params["secret_id"])
    elif params.get("compartment_id") and params.get("secret_name"):
        existing = find_secret_by_name(
            client,
            params["compartment_id"],
            params.get("vault_id"),
            params["secret_name"],
        )

    if state == "absent":
        if existing is None or existing.lifecycle_state in SECRET_DELETED_STATES:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_secret(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        # Validate required params for create
        for req in ("compartment_id", "vault_id", "key_id", "secret_name"):
            if not params.get(req):
                module.fail_json(
                    msg="Parameter '{0}' is required to create a secret.".format(req)
                )
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_secret(module, client)
        module.exit_json(changed=True, secret=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_secret(module, client, existing)
        module.exit_json(changed=True, secret=to_dict(resource))
        return

    module.exit_json(changed=False, secret=to_dict(existing))


if __name__ == "__main__":
    main()
