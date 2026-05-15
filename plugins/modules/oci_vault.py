# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Vault KMS vaults."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_vault
short_description: Manage OCI Vault KMS vaults
description:
  - Create, update, and delete vaults in OCI Key Management Service.
  - Vaults are logical containers for encryption keys and secrets.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the vault resides.
      - Required when creating a new vault.
    type: str
  display_name:
    description:
      - A user-friendly name for the vault.
      - Required when creating a new vault.
    type: str
  vault_type:
    description:
      - The type of vault to create.
    type: str
    choices: [DEFAULT, VIRTUAL_PRIVATE]
    default: DEFAULT
  vault_id:
    description:
      - The OCID of the vault.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the vault.
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
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a default vault
  stevefulme1.oci_cloud.oci_vault:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-vault
    vault_type: DEFAULT
    state: present

- name: Create a virtual private vault
  stevefulme1.oci_cloud.oci_vault:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-private-vault
    vault_type: VIRTUAL_PRIVATE
    state: present

- name: Update a vault display name
  stevefulme1.oci_cloud.oci_vault:
    vault_id: ocid1.vault.oc1..example
    display_name: renamed-vault
    state: present

- name: Schedule vault deletion
  stevefulme1.oci_cloud.oci_vault:
    vault_id: ocid1.vault.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The vault resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the vault.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the vault.
      type: str
    vault_type:
      description: The type of vault.
      type: str
    lifecycle_state:
      description: The current lifecycle state of the vault.
      type: str
    management_endpoint:
      description: The service endpoint for vault management operations.
      type: str
    crypto_endpoint:
      description: The service endpoint for crypto operations.
      type: str
    time_created:
      description: The date and time the vault was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.key_management import KmsVaultClient
    from oci.key_management.models import (
        CreateVaultDetails,
        UpdateVaultDetails,
        ScheduleVaultDeletionDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_vault(client, vault_id):
    """Get a vault by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_vault, vault_id)
        vault = response.data
        if vault.lifecycle_state in ("DELETED", "PENDING_DELETION"):
            return None
        return vault
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_vault(client, compartment_id, display_name):
    """Find a vault by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    vaults = call_with_retry(
        client.list_vaults,
        compartment_id,
    ).data
    for v in vaults:
        if v.display_name == display_name and v.lifecycle_state not in (
            "DELETED",
            "PENDING_DELETION",
        ):
            return get_vault(client, v.id)
    return None


def create_vault(module, client):
    """Create a new vault."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateVaultDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        vault_type=module.params.get("vault_type", "DEFAULT"),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_vault, details)
    vault = response.data

    if module.params.get("wait", True):
        vault = wait_for_resource(
            module,
            client.get_vault,
            vault.id,
            target_states={"ACTIVE"},
        )
    return vault


def update_vault(module, client, vault):
    """Update an existing vault."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return vault

    details = UpdateVaultDetails(**kwargs)
    response = call_with_retry(client.update_vault, vault.id, details)
    return response.data


def delete_vault(module, client, vault):
    """Schedule vault for deletion."""
    details = ScheduleVaultDeletionDetails()
    call_with_retry(client.schedule_vault_deletion, vault.id, details)

    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_vault,
            vault.id,
            target_states={"PENDING_DELETION", "DELETED"},
        )


def needs_update(module, vault):
    """Check if vault needs to be updated."""
    if module.params.get("display_name") and vault.display_name != module.params["display_name"]:
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(vault, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(vault, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        vault_type=dict(type="str", choices=["DEFAULT", "VIRTUAL_PRIVATE"], default="DEFAULT"),
        vault_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, KmsVaultClient)
    state = module.params.get("state", "present")
    vault_id = module.params.get("vault_id")

    # Get existing resource
    vault = None
    if vault_id:
        vault = get_vault(client, vault_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        vault = find_vault(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if vault is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_vault(module, client, vault)
        module.exit_json(changed=True)
        return

    # state == present
    if vault is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id and display_name are required to create a vault.")
        if module.check_mode:
            module.exit_json(changed=True)
        vault = create_vault(module, client)
        module.exit_json(changed=True, resource=to_dict(vault))
        return

    if needs_update(module, vault):
        if module.check_mode:
            module.exit_json(changed=True)
        vault = update_vault(module, client, vault)
        module.exit_json(changed=True, resource=to_dict(vault))
        return

    module.exit_json(changed=False, resource=to_dict(vault))


def main():
    run_module()


if __name__ == "__main__":
    main()
