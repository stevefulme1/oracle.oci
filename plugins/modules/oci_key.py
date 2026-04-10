# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI KMS encryption keys."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_key
short_description: Manage OCI KMS encryption keys
description:
  - Create, update, and delete encryption keys in OCI Key Management Service.
  - Keys are used to encrypt data at rest and in transit across OCI services.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the key resides.
      - Required when creating a new key.
    type: str
  display_name:
    description:
      - A user-friendly name for the key.
      - Required when creating a new key.
    type: str
  key_shape:
    description:
      - The cryptographic properties of a key.
      - Required when creating a new key.
    type: dict
    suboptions:
      algorithm:
        description:
          - The algorithm used by a key's key versions to encrypt or decrypt.
        type: str
        choices: [AES, RSA, ECDSA]
        required: true
      length:
        description:
          - The length of the key in bytes.
          - "AES: 16 (128-bit), 24 (192-bit), 32 (256-bit)"
          - "RSA: 32 (256-bit), 64 (512-bit)"
          - "ECDSA: 32 (256-bit), 48 (384-bit)"
        type: int
        required: true
  management_endpoint:
    description:
      - The service endpoint for key management operations.
      - Obtained from the vault's management_endpoint attribute.
      - Required for all operations.
    type: str
    required: true
  protection_mode:
    description:
      - The key's protection mode.
      - HSM keys are stored on a hardware security module.
      - SOFTWARE keys are stored on the server.
    type: str
    choices: [HSM, SOFTWARE]
    default: HSM
  key_id:
    description:
      - The OCID of the key.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the key.
    type: str
    choices: [present, absent]
    default: present
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an AES-256 encryption key
  oracle.oci.oci_key:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-aes-key
    management_endpoint: https://example-management.kms.us-ashburn-1.oraclecloud.com
    key_shape:
      algorithm: AES
      length: 32
    protection_mode: HSM
    state: present

- name: Create an RSA key for signing
  oracle.oci.oci_key:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-rsa-key
    management_endpoint: https://example-management.kms.us-ashburn-1.oraclecloud.com
    key_shape:
      algorithm: RSA
      length: 32
    protection_mode: SOFTWARE
    state: present

- name: Disable and schedule key deletion
  oracle.oci.oci_key:
    key_id: ocid1.key.oc1..example
    management_endpoint: https://example-management.kms.us-ashburn-1.oraclecloud.com
    state: absent
"""

RETURN = r"""
resource:
  description: The key resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the key.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the key.
      type: str
    key_shape:
      description: The cryptographic properties of the key.
      type: dict
    protection_mode:
      description: The protection mode of the key.
      type: str
    lifecycle_state:
      description: The current lifecycle state of the key.
      type: str
    time_created:
      description: The date and time the key was created.
      type: str
    current_key_version:
      description: The OCID of the current key version.
      type: str
    vault_id:
      description: The OCID of the vault that contains the key.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import (
    get_oci_config,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.key_management import KmsManagementClient
    from oci.key_management.models import (
        CreateKeyDetails,
        KeyShape,
        UpdateKeyDetails,
        ScheduleKeyDeletionDetails,
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
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
        else:
            result[key] = value
    return result


def create_kms_client(module):
    """Create KmsManagementClient with the management endpoint."""
    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    endpoint = module.params["management_endpoint"]
    auth_type = module.params.get("auth_type", "api_key")

    if auth_type == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return KmsManagementClient(config={}, signer=signer, service_endpoint=endpoint)

    if auth_type == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        return KmsManagementClient(config={}, signer=signer, service_endpoint=endpoint)

    config = get_oci_config(module)
    oci.config.validate_config(config)
    return KmsManagementClient(config, service_endpoint=endpoint)


def get_key(client, key_id):
    """Get a key by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_key, key_id)
        key = response.data
        if key.lifecycle_state in ("DELETED", "PENDING_DELETION"):
            return None
        return key
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_key(client, compartment_id, display_name):
    """Find a key by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    keys = call_with_retry(client.list_keys, compartment_id).data
    for k in keys:
        if k.display_name == display_name and k.lifecycle_state not in (
            "DELETED",
            "PENDING_DELETION",
        ):
            return get_key(client, k.id)
    return None


def create_key(module, client):
    """Create a new encryption key."""
    shape_params = module.params["key_shape"]
    key_shape = KeyShape(
        algorithm=shape_params["algorithm"],
        length=shape_params["length"],
    )
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateKeyDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        key_shape=key_shape,
        protection_mode=module.params.get("protection_mode", "HSM"),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_key, details)
    key = response.data

    if module.params.get("wait", True):
        key = wait_for_resource(
            module,
            client.get_key,
            key.id,
            target_states={"ENABLED"},
        )
    return key


def update_key(module, client, key):
    """Update an existing key."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return key

    details = UpdateKeyDetails(**kwargs)
    response = call_with_retry(client.update_key, key.id, details)
    return response.data


def delete_key(module, client, key):
    """Schedule key for deletion."""
    # Disable the key first if it is enabled
    if key.lifecycle_state == "ENABLED":
        call_with_retry(client.disable_key, key.id)

    details = ScheduleKeyDeletionDetails()
    call_with_retry(client.schedule_key_deletion, key.id, details)

    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_key,
            key.id,
            target_states={"PENDING_DELETION", "DELETED"},
        )


def needs_update(module, key):
    """Check if key needs to be updated."""
    if module.params.get("display_name") and key.display_name != module.params["display_name"]:
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(key, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(key, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        key_shape=dict(
            type="dict",
            no_log=False,
            options=dict(
                algorithm=dict(type="str", choices=["AES", "RSA", "ECDSA"], required=True),
                length=dict(type="int", required=True),
            ),
        ),
        management_endpoint=dict(type="str", required=True),
        protection_mode=dict(type="str", choices=["HSM", "SOFTWARE"], default="HSM"),
        key_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "key_shape"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_kms_client(module)
    state = module.params.get("state", "present")
    key_id = module.params.get("key_id")

    # Get existing resource
    key = None
    if key_id:
        key = get_key(client, key_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        key = find_key(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if key is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_key(module, client, key)
        module.exit_json(changed=True)
        return

    # state == present
    if key is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id, display_name, and key_shape are required to create a key.")
        if module.check_mode:
            module.exit_json(changed=True)
        key = create_key(module, client)
        module.exit_json(changed=True, resource=to_dict(key))
        return

    if needs_update(module, key):
        if module.check_mode:
            module.exit_json(changed=True)
        key = update_key(module, client, key)
        module.exit_json(changed=True, resource=to_dict(key))
        return

    module.exit_json(changed=False, resource=to_dict(key))


def main():
    run_module()


if __name__ == "__main__":
    main()
