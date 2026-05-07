# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI SMTP credentials."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_smtp_credential
short_description: Manage OCI SMTP credentials
description:
  - Create, update, and delete SMTP credentials for OCI IAM users.
  - SMTP credentials are used to send email through the OCI Email Delivery service.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  user_id:
    description:
      - The OCID of the user who owns the SMTP credential.
      - Required for all operations.
    type: str
    required: true
  smtp_credential_id:
    description:
      - The OCID of the SMTP credential.
      - Required for update and delete operations.
    type: str
  description:
    description:
      - A description of the SMTP credential.
      - Required when creating a new SMTP credential.
    type: str
  state:
    description:
      - The desired state of the SMTP credential.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create an SMTP credential
  stevefulme1.oci_cloud.oci_smtp_credential:
    user_id: "ocid1.user.oc1..example"
    description: "Email delivery credential"
    state: present

- name: Update an SMTP credential description
  stevefulme1.oci_cloud.oci_smtp_credential:
    user_id: "ocid1.user.oc1..example"
    smtp_credential_id: "ocid1.credential.oc1..example"
    description: "Updated email credential"
    state: present

- name: Delete an SMTP credential
  stevefulme1.oci_cloud.oci_smtp_credential:
    user_id: "ocid1.user.oc1..example"
    smtp_credential_id: "ocid1.credential.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The SMTP credential details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the SMTP credential.
      type: str
    user_id:
      description: The OCID of the user.
      type: str
    description:
      description: The description of the SMTP credential.
      type: str
    username:
      description: The SMTP username.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the credential was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateSmtpCredentialDetails,
        UpdateSmtpCredentialDetails,
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


def get_resource(client, user_id, credential_id):
    """Get an SMTP credential by listing user credentials and matching ID."""
    if not credential_id:
        return None
    try:
        creds = call_with_retry(client.list_smtp_credentials, user_id).data
        for cred in creds:
            if cred.id == credential_id and cred.lifecycle_state not in ("DELETED", "TERMINATED"):
                return cred
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise
    return None


def find_resource(client, user_id, description):
    """Find an SMTP credential by user and description."""
    if not user_id or not description:
        return None
    creds = call_with_retry(client.list_smtp_credentials, user_id).data
    for cred in creds:
        if cred.description == description and cred.lifecycle_state not in ("DELETED", "TERMINATED"):
            return cred
    return None


def create_resource(module, client):
    """Create a new SMTP credential."""
    details = CreateSmtpCredentialDetails(
        description=module.params["description"],
    )
    response = call_with_retry(
        client.create_smtp_credential, details, module.params["user_id"]
    )
    return response.data


def update_resource(module, client, resource):
    """Update an existing SMTP credential."""
    kwargs = {}
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            kwargs["description"] = module.params["description"]

    if not kwargs:
        return resource

    details = UpdateSmtpCredentialDetails(**kwargs)
    response = call_with_retry(
        client.update_smtp_credential, module.params["user_id"], resource.id, details
    )
    return response.data


def delete_resource(module, client, resource):
    """Delete an SMTP credential."""
    call_with_retry(
        client.delete_smtp_credential, module.params["user_id"], resource.id
    )


def needs_update(module, resource):
    """Check if the SMTP credential needs updating."""
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            return True
    return False


def main():
    module_args = dict(
        user_id=dict(type="str", required=True),
        smtp_credential_id=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["smtp_credential_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    user_id = module.params["user_id"]
    credential_id = module.params.get("smtp_credential_id")

    resource = None
    if credential_id:
        resource = get_resource(client, user_id, credential_id)
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
